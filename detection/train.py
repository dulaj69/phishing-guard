"""Train the baseline detector (TF-IDF character n-grams + Logistic Regression).

Character n-grams work for English, Singlish and Sinhala script without any
extra tools, so this is a fair first baseline before the XLM-R model.

Run:  python -m detection.train

The test split keeps whole TEMPLATES apart (GroupShuffleSplit), so the model is
tested on message styles it never saw. Numbers are still only PRELIMINARY:
the data is mostly synthetic. Final results must use the real gold test set.
"""
import json

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, recall_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

from detection import synth
from detection.config import (MODEL_PATH, MODEL_VERSION, PUBLIC_CSV, SEED_CSV, SYNTH_CSV)
from detection.preprocess import clean


COLS = ["id", "text", "label", "language", "template_id", "source"]


def load_data(include_public=True):
    """Our own data, plus the public datasets when they have been built.

    `is_local` marks the rows written for THIS project (hand-written seed +
    synthetic Sinhala/Singlish/English). The public rows are English, Hindi and
    Telugu, so they teach general scam wording but say nothing about Singlish.
    Every result is therefore reported twice: on everything, and on the local
    rows alone. Reporting only the combined number would hide the language gap.
    """
    seed = pd.read_csv(SEED_CSV, dtype=str, keep_default_na=False)
    seed["template_id"] = "seed-" + seed["id"]
    seed["source"] = "seed-v1"
    if not SYNTH_CSV.exists():
        synth.main()
    syn = pd.read_csv(SYNTH_CSV, dtype=str, keep_default_na=False)
    parts = [seed[COLS], syn[COLS]]

    if include_public and PUBLIC_CSV.exists():
        pub = pd.read_csv(PUBLIC_CSV, dtype=str, keep_default_na=False)
        parts.append(pub[COLS])
        print(f"  + {len(pub)} public messages from {PUBLIC_CSV.name}")
    elif include_public:
        print(f"  (no public data yet: run python -m detection.get_datasets "
              f"then python -m detection.public_data)")

    data = pd.concat(parts, ignore_index=True)
    data["is_local"] = ~data["source"].str.startswith(("smishtank", "mendeley", "exais",
                                                       "uci", "indian"))
    data["clean"] = [clean(t)[0] for t in data["text"]]
    data["zero_link"] = ~data["text"].str.contains(r"\[\.\]|http|www\.|\.example", regex=True)
    return data


def build_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)),
    ])


def evaluate(data, seed=7):
    split = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
    train_idx, test_idx = next(split.split(data, groups=data["template_id"]))
    train, test = data.iloc[train_idx], data.iloc[test_idx]
    model = build_pipeline().fit(train["clean"], train["label"])
    pred = model.predict(test["clean"])
    print(f"Train: {len(train)} messages | Test: {len(test)} messages "
          f"({test['template_id'].nunique()} unseen templates)\n")
    print(classification_report(test["label"], pred, zero_division=0))

    results = {"overall_macro_f1": None, "by_language": {}, "zero_link_phishing_recall": None}
    report = classification_report(test["label"], pred, zero_division=0, output_dict=True)
    results["overall_macro_f1"] = round(report["macro avg"]["f1-score"], 3)
    print("Phishing recall by language (unseen templates):")
    for lang, part in test.groupby("language"):
        mask = part["label"] == "phishing"
        if mask.sum():
            r = recall_score(part["label"][mask], model.predict(part["clean"][mask]),
                             labels=["phishing"], average="micro", zero_division=0)
            results["by_language"][lang] = {"phishing_recall": round(r, 3), "n_phishing": int(mask.sum())}
            print(f"  {lang:9s} {r:.2f}  (n={mask.sum()})")
    zl = test[(test["label"] == "phishing") & test["zero_link"]]
    if len(zl):
        r = (model.predict(zl["clean"]) == "phishing").mean()
        results["zero_link_phishing_recall"] = round(float(r), 3)
        print(f"  zero-link {r:.2f}  (n={len(zl)})")
    local = test[test["is_local"]]
    if len(local) and (~test["is_local"]).any():
        lp = local[local["label"] == "phishing"]
        lr = classification_report(local["label"], model.predict(local["clean"]),
                                   zero_division=0, output_dict=True)
        results["local_only"] = {
            "n_test": int(len(local)),
            "macro_f1": round(lr["macro avg"]["f1-score"], 3),
            "phishing_recall": round(float((model.predict(lp["clean"]) == "phishing").mean()), 3)
            if len(lp) else None,
        }
        print(f"\nOur own Sinhala/Singlish/English rows only (n={len(local)}): "
              f"macro-F1 {results['local_only']['macro_f1']}, "
              f"phishing recall {results['local_only']['phishing_recall']}")

    print("\nPRELIMINARY: our local rows are still mostly synthetic. "
          "Final results need the real, hand-labelled gold test set.")
    return results


def train(model_path=MODEL_PATH, show_report=True):
    data = load_data()
    results = evaluate(data) if show_report else None
    model = build_pipeline().fit(data["clean"], data["label"])
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "version": MODEL_VERSION}, model_path)
    if results:
        (model_path.parent / "detector_results.json").write_text(json.dumps(results, indent=2))
    print(f"Model saved to {model_path}")
    return model_path


if __name__ == "__main__":
    train()
