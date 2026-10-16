"""Train a very simple baseline model (TF-IDF + Logistic Regression).

Run from the project root:
    python -m src.train_baseline

IMPORTANT: the seed file has only ~36 messages, so the scores printed here are
NOT meaningful. This model exists only to test the pipeline (API -> XAI -> UI).
"""
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

from src.config import MODEL_PATH, SEED_CSV


def build_pipeline():
    # Character n-grams work for English, Singlish and Sinhala without extra tools.
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), lowercase=True)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def train(csv_path=SEED_CSV, model_path=MODEL_PATH, show_report=True):
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    texts, labels = df["text"], df["label"]
    pipe = build_pipeline()

    if show_report:
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        predicted = cross_val_predict(pipe, texts, labels, cv=cv)
        print(classification_report(labels, predicted, zero_division=0))
        print("(Tiny dataset: do not trust these numbers.)")

    pipe.fit(texts, labels)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_path)
    print(f"Model saved to {model_path}")
    return model_path


if __name__ == "__main__":
    train()
