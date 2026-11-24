"""Train and evaluate a closeness classifier from human-labelled chat exports."""

import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "train-closeness-only")

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score)
from sklearn.model_selection import train_test_split

from closeness import FEATURE_KEYS, LEVEL_NAMES, compute_closeness, feature_vector
from closeness_ml import ARTIFACT_DIR, METRICS_PATH, MODEL_PATH

ROOT = Path(__file__).resolve().parent
CHATS_DIR = ROOT / "sampel-chat"
LABELS_PATH = ROOT / "colab" / "closeness_labels.csv"
SEED = 42


def labelled_rows():
    if not CHATS_DIR.exists() or not LABELS_PATH.exists():
        raise SystemExit("Human-labelled exports are required in sampel-chat/ and colab/closeness_labels.csv.")

    sys.path.insert(0, str(ROOT))
    from main import parse_wa_export, read_whatsapp_upload

    labels_by_file = {}
    with LABELS_PATH.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            filename = (row.get("file") or "").strip()
            label = (row.get("label") or "").strip()
            if filename and label in LEVEL_NAMES:
                labels_by_file.setdefault(filename.casefold(), []).append(label)

    rows = []
    missing = []
    for filename, votes in labels_by_file.items():
        path = next((item for item in CHATS_DIR.iterdir() if item.name.casefold() == filename), None)
        if path is None:
            missing.append(filename)
            continue
        try:
            raw = read_whatsapp_upload(path.name, path.read_bytes())
            messages = parse_wa_export(raw)
        except (OSError, ValueError):
            continue
        people = [name for name, _ in Counter(sender for _, sender, _ in messages).most_common(2)]
        if len(people) != 2:
            continue
        relevant = [message for message in messages if message[1] in people]
        if len(relevant) < 2:
            continue
        result = compute_closeness(relevant, people)
        rows.append((feature_vector(result), Counter(votes).most_common(1)[0][0], path.name))

    if missing:
        print("Labelled exports not found:", len(missing))
    if len(rows) < 8:
        raise SystemExit(f"Only {len(rows)} usable labelled chats found; at least 8 are required for a holdout evaluation.")
    return rows


def split_rows(rows):
    X = [row[0] for row in rows]
    y = [row[1] for row in rows]
    counts = Counter(y)

    # Keep labels with only one example in training; they cannot be evaluated in a holdout.
    singleton_indices = [index for index, label in enumerate(y) if counts[label] == 1]
    eligible = [index for index, label in enumerate(y) if counts[label] > 1]
    eligible_y = [y[index] for index in eligible]
    stratify = eligible_y if min(Counter(eligible_y).values()) >= 2 else None
    train_eligible, test_indices = train_test_split(
        eligible, test_size=0.25, random_state=SEED, stratify=stratify)
    train_indices = sorted(train_eligible + singleton_indices)
    return ([X[index] for index in train_indices], [X[index] for index in test_indices],
            [y[index] for index in train_indices], [y[index] for index in test_indices], counts)


def main():
    rows = labelled_rows()
    X_train, X_test, y_train, y_test, label_counts = split_rows(rows)
    model = RandomForestClassifier(
        n_estimators=160, max_depth=8, min_samples_leaf=2,
        random_state=SEED, class_weight="balanced")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    labels = [label for label in LEVEL_NAMES if label in set(y_test)]
    report = classification_report(y_test, y_pred, labels=labels, zero_division=0, output_dict=True)
    metrics = {
        "algorithm": "RandomForestClassifier",
        "n_estimators": 160,
        "features": list(FEATURE_KEYS),
        "classes": list(model.classes_),
        "n_rows": len(rows),
        "n_train": len(y_train),
        "n_test": len(y_test),
        "label_counts": dict(label_counts),
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 3),
        "precision_macro": round(float(precision_score(y_test, y_pred, labels=labels, average="macro", zero_division=0)), 3),
        "recall_macro": round(float(recall_score(y_test, y_pred, labels=labels, average="macro", zero_division=0)), 3),
        "f1_macro": round(float(f1_score(y_test, y_pred, labels=labels, average="macro", zero_division=0)), 3),
        "confusion_matrix": {"labels": labels, "rows": confusion_matrix(y_test, y_pred, labels=labels).tolist()},
        "per_class": {name: {"precision": round(report[name]["precision"], 3),
                             "recall": round(report[name]["recall"], 3),
                             "f1": round(report[name]["f1-score"], 3),
                             "support": int(report[name]["support"])} for name in labels},
        "feature_importances": dict(zip(FEATURE_KEYS, (round(float(value), 3) for value in model.feature_importances_))),
        "test_split": round(len(y_test) / len(rows), 3),
        "random_state": SEED,
        "evaluation_note": "Metrics use only held-out human-labelled chats. Classes with one sample are retained in training and are not represented in test metrics.",
    }

    ARTIFACT_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(classification_report(y_test, y_pred, labels=labels, zero_division=0))
    print("Accuracy:", metrics["accuracy"], "F1-macro:", metrics["f1_macro"])
    print("Rows:", len(rows), "train:", len(y_train), "test:", len(y_test))
    print("Wrote", MODEL_PATH, "and", METRICS_PATH)


if __name__ == "__main__":
    main()
