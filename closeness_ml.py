"""Load the saved Random Forest and predict a closeness level from six features."""

import json
from pathlib import Path

from closeness import FEATURE_KEYS, LEVEL_NAMES, feature_vector

ROOT = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "closeness_rf.joblib"
METRICS_PATH = ARTIFACT_DIR / "closeness_metrics.json"

_model = None


def load_metrics() -> dict | None:
    if not METRICS_PATH.exists():
        return None
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


def load_model():
    global _model
    if _model is not None:
        return _model
    if not MODEL_PATH.exists():
        return None
    import joblib
    _model = joblib.load(MODEL_PATH)
    return _model


def predict_closeness(result: dict) -> dict | None:
    """Return ml_level, class probabilities, and the six features. None if the model file is missing."""
    model = load_model()
    if model is None:
        return None
    features = feature_vector(result)
    predicted = model.predict([features])[0]
    proba = model.predict_proba([features])[0]
    classes = list(model.classes_)
    probabilities = {name: round(float(proba[classes.index(name)]), 3) for name in LEVEL_NAMES if name in classes}
    return {
        "level": str(predicted),
        "confidence": round(float(max(proba)), 3),
        "probabilities": probabilities,
        "features": dict(zip(FEATURE_KEYS, features)),
        "model_file": MODEL_PATH.name,
    }
