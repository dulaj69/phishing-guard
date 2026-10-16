"""Load the model and make predictions. The API uses this file."""
import time

import joblib

from src.config import MODEL_PATH, MODEL_VERSION

_model = None


def load_model(path=None):
    """Load a trained model from disk (raises FileNotFoundError if missing)."""
    global _model
    _model = joblib.load(path or MODEL_PATH)
    return _model


def get_model():
    if _model is None:
        load_model()
    return _model


def predict_texts(texts):
    """Return one result dict per text."""
    model = get_model()
    start = time.perf_counter()
    probabilities = model.predict_proba(texts)
    total_ms = (time.perf_counter() - start) * 1000
    per_message_ms = total_ms / max(len(texts), 1)

    classes = list(model.classes_)
    results = []
    for row in probabilities:
        probs = {name: round(float(p), 4) for name, p in zip(classes, row)}
        label = max(probs, key=probs.get)
        results.append(
            {
                "label": label,
                "probabilities": probs,
                "model_version": MODEL_VERSION,
                "latency_ms": round(per_message_ms, 2),
            }
        )
    return results
