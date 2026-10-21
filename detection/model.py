"""Run the full detection step on one or many messages.

    clean text -> model probabilities -> scam anatomy (rules) -> one result dict
"""
import time

import joblib

from detection import anatomy
from detection.config import LABELS, MODEL_PATH, MODEL_VERSION
from detection.preprocess import clean

_bundle = None


def load_model(path=None):
    """Load a trained model (raises FileNotFoundError if it is missing)."""
    global _bundle
    _bundle = joblib.load(path or MODEL_PATH)
    return _bundle


def _model():
    if _bundle is None:
        load_model()
    return _bundle["model"]


def probabilities(clean_texts):
    """Return one {label: probability} dict per text. Used by the explainers too."""
    model = _model()
    rows = model.predict_proba(list(clean_texts))
    out = []
    for row in rows:
        probs = {label: 0.0 for label in LABELS}
        probs.update({c: round(float(p), 4) for c, p in zip(model.classes_, row)})
        out.append(probs)
    return out


def scam_score(probs):
    """One number for 'how likely is this a scam'. Suspicious counts as half."""
    return round(min(1.0, probs.get("phishing", 0) + 0.5 * probs.get("suspicious", 0)), 4)


def detect(texts, senders=None):
    senders = senders or [None] * len(texts)
    start = time.perf_counter()
    cleaned = [clean(t) for t in texts]
    probs = probabilities([c[0] for c in cleaned])
    per_ms = (time.perf_counter() - start) * 1000 / max(len(texts), 1)

    results = []
    for (norm, lang, tricks), p, sender in zip(cleaned, probs, senders):
        results.append({
            "label": max(p, key=p.get),
            "probabilities": p,
            "scam_score": scam_score(p),
            "score_semantics": "uncalibrated_weighted_score",
            "language": lang,
            "normalized_text": norm,
            "tricks_found": tricks,
            "anatomy": anatomy.extract(norm, sender),
            "model_version": _bundle.get("version", MODEL_VERSION),
            "latency_ms": round(per_ms, 2),
        })
    return results
