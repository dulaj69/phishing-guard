"""Step 2 of verify: which words pushed the scam score up?

Three methods, so Perera can compare them (that comparison is a research result):
  - occlusion:  remove one word at a time and see how much the score drops.
                Simple, fast, works with any model. Used in the live app.
  - lime:       LIME (Ribeiro et al., 2016). Needs `pip install lime`.
  - shap / IG:  added in Phase 3 for the XLM-R model (shap, captum).

Explanations here describe the MODEL, not the danger. Danger is the risk tier.
"""
import re

from detection.model import probabilities, scam_score


def _score_many(texts):
    return [scam_score(p) for p in probabilities(texts)]


def occlusion(clean_text, top_k=6):
    words = clean_text.split()
    if not words:
        return []
    base = _score_many([clean_text])[0]
    variants = [" ".join(words[:i] + words[i + 1:]) for i in range(len(words))]
    scores = _score_many(variants)
    weights = [(w, round(base - s, 4)) for w, s in zip(words, scores)]
    weights = [(re.sub(r"^[^\w]+|[^\w]+$", "", w) or w, v) for w, v in weights]
    weights.sort(key=lambda x: x[1], reverse=True)
    return [{"word": w, "weight": v} for w, v in weights[:top_k] if v > 0]


def lime(clean_text, top_k=6, num_samples=500):
    """LIME explanation. Returns None if the lime package is not installed."""
    try:
        from lime.lime_text import LimeTextExplainer
    except ImportError:
        return None
    import numpy as np

    def predict(texts):
        return np.array([[1 - s, s] for s in _score_many(texts)])

    explainer = LimeTextExplainer(class_names=["safe", "scam"], random_state=0)
    exp = explainer.explain_instance(clean_text, predict, num_features=top_k, num_samples=num_samples)
    return [{"word": w, "weight": round(v, 4)} for w, v in exp.as_list() if v > 0]


def explain(clean_text, method="occlusion", top_k=6):
    if method == "lime":
        result = lime(clean_text, top_k)
        if result is not None:
            return result
    return occlusion(clean_text, top_k)
