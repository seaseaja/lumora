"""Compare Lumora's rule-based closeness level with human labels.

Workflow:
  1. Put WhatsApp exports (.txt or .zip) in sampel-chat/ (ignored by Git).
  2. Run:  python colab/validate_closeness.py
     The first run writes colab/closeness_labels.csv with one row per chat.
  3. Each group member reads the chats they are allowed to read and fills in
     their own rows: rater = their name/initials, label = one of
     Distant, Casual, Close, Very close. Copy a row to add another rater.
     Label BEFORE looking at the app's score so the comparison stays fair.
  4. Run the script again to see accuracy, a confusion matrix, and per-chat results.

Output contains file names, scores, and labels only, never message text.
Both CSV files stay out of Git because file names can contain people's names.
"""

import argparse
import csv
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# main.py needs these to import; this script never touches the database.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "validation-script-only")

from closeness import LEVEL_NAMES, compute_closeness  # noqa: E402
from main import parse_wa_export, read_whatsapp_upload  # noqa: E402

DEFAULT_CHATS = ROOT / "sampel-chat"
DEFAULT_LABELS = Path(__file__).resolve().parent / "closeness_labels.csv"
DEFAULT_RESULTS = Path(__file__).resolve().parent / "closeness_validation_results.csv"
LABEL_ALIASES = {name.casefold(): name for name in LEVEL_NAMES} | {
    "1": "Distant", "2": "Casual", "3": "Close", "4": "Very close",
    "jauh": "Distant", "renggang": "Distant", "biasa": "Casual", "dekat": "Close",
    "sangat dekat": "Very close", "very_close": "Very close", "veryclose": "Very close",
}


def score_chat(path: Path):
    raw = read_whatsapp_upload(path.name, path.read_bytes())
    messages = parse_wa_export(raw)
    people = [name for name, _ in Counter(sender for _, sender, _ in messages).most_common(2)]
    if len(people) < 2:
        raise ValueError("needs messages from two people")
    relevant = [message for message in messages if message[1] in people]
    return compute_closeness(relevant, people), len(relevant)


def write_template(chat_files, labels_path: Path):
    with labels_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["file", "rater", "label"])
        for path in chat_files:
            writer.writerow([path.name, "", ""])
    print(f"Wrote {labels_path} with {len(chat_files)} chats.")
    print("Fill in rater and label (Distant / Casual / Close / Very close), then run this script again.")


def read_labels(labels_path: Path):
    labels, problems = {}, []
    with labels_path.open(newline="", encoding="utf-8-sig") as handle:
        for line_no, row in enumerate(csv.DictReader(handle), start=2):
            file, raw_label = (row.get("file") or "").strip(), (row.get("label") or "").strip()
            if not file or not raw_label:
                continue
            label = LABEL_ALIASES.get(raw_label.casefold())
            if not label:
                problems.append(f"line {line_no}: unknown label '{raw_label}'")
                continue
            labels.setdefault(file, []).append(label)
    return labels, problems


def consensus(votes):
    """Majority vote; on a tie, the median level (lower middle) decides."""
    counts = Counter(votes).most_common()
    if len(counts) == 1 or counts[0][1] > counts[1][1]:
        return counts[0][0]
    ordered = sorted(LEVEL_NAMES.index(vote) for vote in votes)
    return LEVEL_NAMES[ordered[(len(ordered) - 1) // 2]]


def spearman(xs, ys):
    """Spearman rank correlation with average ranks for ties (no SciPy needed)."""
    def ranks(values):
        order = sorted(range(len(values)), key=values.__getitem__)
        result = [0.0] * len(values)
        index = 0
        while index < len(order):
            end = index
            while end + 1 < len(order) and values[order[end + 1]] == values[order[index]]:
                end += 1
            for position in range(index, end + 1):
                result[order[position]] = (index + end) / 2 + 1
            index = end + 1
        return result
    rx, ry = ranks(xs), ranks(ys)
    mean_x, mean_y = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(rx, ry))
    var = (sum((a - mean_x) ** 2 for a in rx) * sum((b - mean_y) ** 2 for b in ry)) ** 0.5
    return cov / var if var else None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--chats", type=Path, default=DEFAULT_CHATS, help="folder with WhatsApp exports")
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS, help="CSV with file,rater,label")
    parser.add_argument("--out", type=Path, default=DEFAULT_RESULTS, help="where to write per-chat results")
    args = parser.parse_args()

    chat_files = sorted(path for path in args.chats.glob("*") if path.suffix.lower() in {".txt", ".zip"})
    if not chat_files:
        sys.exit(f"No .txt or .zip exports found in {args.chats}")
    if not args.labels.exists():
        write_template(chat_files, args.labels)
        return

    labels, problems = read_labels(args.labels)
    for problem in problems:
        print("Skipped", problem)

    rows = []
    for path in chat_files:
        try:
            result, message_count = score_chat(path)
        except ValueError as exc:
            print(f"Skipped {path.name}: {exc}")
            continue
        votes = labels.get(path.name, [])
        rows.append({"file": path.name, "messages": message_count, "app_score": result["score"],
                     "app_level": result["level"], "human_level": consensus(votes) if votes else "",
                     "raters": len(votes), "rater_votes": "; ".join(votes),
                     "raters_agree": "" if len(votes) < 2 else len(set(votes)) == 1})

    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["file"])
        writer.writeheader()
        writer.writerows(rows)

    labelled = [row for row in rows if row["human_level"]]
    print(f"\nScored {len(rows)} chats; {len(labelled)} have human labels. Per-chat results: {args.out}")
    if not labelled:
        print("No labels yet. Fill in", args.labels)
        return

    app_index = [LEVEL_NAMES.index(row["app_level"]) for row in labelled]
    human_index = [LEVEL_NAMES.index(row["human_level"]) for row in labelled]
    exact = sum(a == h for a, h in zip(app_index, human_index))
    within_one = sum(abs(a - h) <= 1 for a, h in zip(app_index, human_index))
    mean_gap = sum(abs(a - h) for a, h in zip(app_index, human_index)) / len(labelled)
    rho = spearman([row["app_score"] for row in labelled], human_index)

    print(f"\nExact level match:     {exact}/{len(labelled)} = {exact / len(labelled):.0%}")
    print(f"Within one level:      {within_one}/{len(labelled)} = {within_one / len(labelled):.0%}")
    print(f"Average level gap:     {mean_gap:.2f} levels")
    print("Spearman (score vs label): " + ("n/a (all labels or scores identical)" if rho is None else f"{rho:.2f}"))
    multi = [row for row in labelled if row["raters"] >= 2]
    if multi:
        agree = sum(1 for row in multi if row["raters_agree"])
        print(f"Raters fully agree:    {agree}/{len(multi)} chats with 2+ raters = {agree / len(multi):.0%}")

    print("\nConfusion matrix (rows = human label, columns = app level)")
    width = max(len(name) for name in LEVEL_NAMES) + 2
    print(" " * width + "".join(name.rjust(width) for name in LEVEL_NAMES))
    for h, human in enumerate(LEVEL_NAMES):
        counts = [sum(1 for a, hh in zip(app_index, human_index) if hh == h and a == col) for col in range(len(LEVEL_NAMES))]
        print(human.ljust(width) + "".join(str(count).rjust(width) for count in counts))

    higher = sum(a > h for a, h in zip(app_index, human_index))
    lower = sum(a < h for a, h in zip(app_index, human_index))
    if higher or lower:
        print(f"\nApp rated higher than humans on {higher} chats and lower on {lower}.")
        if higher > 2 * max(lower, 1):
            print("The score runs high: consider raising the level thresholds in closeness.py.")
        elif lower > 2 * max(higher, 1):
            print("The score runs low: consider lowering the level thresholds in closeness.py.")
    if len(labelled) < 20:
        print(f"\nOnly {len(labelled)} labelled chats: treat these numbers as a rough first check, not a result.")


if __name__ == "__main__":
    main()
