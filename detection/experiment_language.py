"""Experiment: does adding 13k English/Hindi/Telugu public messages help our
Sinhala and Singlish detection, or hurt it?

Run:  python -m detection.experiment_language
Out:  models/experiment_language.json

Why this experiment exists
--------------------------
Every public smishing dataset we could find is English. Our project is about
code-mixed Sinhala and Singlish. The obvious move is to throw the English data
in and hope it helps, but "hope" is not a result. So we hold out the SAME local
test templates for both models and change only one thing: whether the public
data was added to training.

  Model A  = our own data only          (seed + synthetic)
  Model B  = our own data + public data (seed + synthetic + public_v1)

Both are tested on identical, unseen LOCAL templates, so the difference is
caused by the public data and nothing else. We also test both on held-out
public messages, which shows the cost of training only on local data.

Significance: McNemar's exact test on the messages where the two models
disagree. With a small local test set a difference of a few messages is noise,
and this test says so instead of letting us over-claim.
"""
import json
from math import comb

import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import GroupShuffleSplit

from detection.config import MODEL_PATH
from detection.train import build_pipeline, load_data

TEST_SIZE = 0.25
RANDOM_STATE = 7


def group_split(frame, test_size=TEST_SIZE, seed=RANDOM_STATE):
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(splitter.split(frame, groups=frame["template_id"]))
    return frame.iloc[train_idx], frame.iloc[test_idx]


def mcnemar_exact(correct_a, correct_b):
    """Two-sided exact McNemar test on paired right/wrong outcomes.

    b = model A right, model B wrong.  c = model A wrong, model B right.
    Under "the two models are equally good", each disagreement is a coin flip,
    so b follows Binomial(b + c, 0.5). No scipy needed.
    """
    b = int((correct_a & ~correct_b).sum())
    c = int((~correct_a & correct_b).sum())
    n = b + c
    if n == 0:
        return {"b": 0, "c": 0, "p_value": 1.0}
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return {"b": b, "c": c, "p_value": round(min(1.0, 2 * tail), 4)}


def score(model, frame):
    pred = model.predict(frame["clean"])
    report = classification_report(frame["label"], pred, zero_division=0, output_dict=True)
    phishing = frame["label"] == "phishing"
    return {
        "n": int(len(frame)),
        "macro_f1": round(report["macro avg"]["f1-score"], 3),
        "phishing_recall": round(float((pred[phishing] == "phishing").mean()), 3)
        if phishing.any() else None,
        "suspicious_recall": round(report.get("suspicious", {}).get("recall", 0.0), 3),
    }, (pred == frame["label"].values)


def main():
    data = load_data(include_public=True)
    local, public = data[data["is_local"]], data[~data["is_local"]]
    if public.empty:
        raise SystemExit("No public data. Run detection.get_datasets then detection.public_data.")

    local_train, local_test = group_split(local)
    public_train, public_test = group_split(public)

    print(f"local:  {len(local_train)} train / {len(local_test)} test "
          f"({local_test['template_id'].nunique()} unseen templates)")
    print(f"public: {len(public_train)} train / {len(public_test)} test\n")

    model_a = build_pipeline().fit(local_train["clean"], local_train["label"])
    mixed = pd.concat([local_train, public_train], ignore_index=True)
    model_b = build_pipeline().fit(mixed["clean"], mixed["label"])

    results = {
        "setup": {
            "model_a": "our own data only (seed + synthetic)",
            "model_b": "our own data + public datasets",
            "local_train": int(len(local_train)), "local_test": int(len(local_test)),
            "public_train": int(len(public_train)), "public_test": int(len(public_test)),
            "test_size": TEST_SIZE, "random_state": RANDOM_STATE,
        }
    }

    for name, frame in (("on_local_test", local_test), ("on_public_test", public_test)):
        a_stats, a_ok = score(model_a, frame)
        b_stats, b_ok = score(model_b, frame)
        results[name] = {"model_a": a_stats, "model_b": b_stats,
                         "mcnemar": mcnemar_exact(a_ok, b_ok)}
        print(f"--- {name.replace('_', ' ')} (n={a_stats['n']}) ---")
        print(f"  {'':22s} {'macro-F1':>9s} {'phishing recall':>16s} {'suspicious recall':>18s}")
        for label, st in (("A  local data only", a_stats), ("B  + public data", b_stats)):
            print(f"  {label:22s} {st['macro_f1']:>9} {str(st['phishing_recall']):>16} "
                  f"{st['suspicious_recall']:>18}")
        m = results[name]["mcnemar"]
        print(f"  McNemar: A-only-right {m['b']}, B-only-right {m['c']}, p = {m['p_value']}"
              f"{'  (not significant)' if m['p_value'] >= 0.05 else '  (significant at 0.05)'}\n")

    n_templates = int(local_test["template_id"].nunique())
    results["warning"] = None
    if n_templates < 30:
        results["warning"] = (
            f"Only {n_templates} unseen local templates in the test set. That is too few to "
            f"call a difference on local data real, whichever way it points. Treat the local "
            f"comparison as inconclusive until the hand-labelled gold set exists.")
        print(f"WARNING: {results['warning']}\n")

    out = MODEL_PATH.parent / "experiment_language.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"Saved to {out}")
    return results


if __name__ == "__main__":
    main()
