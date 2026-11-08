"""Fine-tune a multilingual transformer (XLM-R) on the same data. RUN ON GOOGLE COLAB (GPU).

This is the Phase 2 model for PP1 ("small multilingual model"). Head B (scam
anatomy token tagging) is added in Phase 3.

NOTE: written without a GPU to test on. Run it on Colab and fix anything that
breaks; the steps are standard Hugging Face code.

Colab steps:
    1. Runtime > Change runtime type > T4 GPU
    2. !git clone https://github.com/<your-user>/banking-phish-nlp.git && cd banking-phish-nlp
    3. !pip install -q transformers datasets accelerate scikit-learn pandas joblib
    4. !python -m detection.train_xlmr --model xlm-roberta-base --epochs 3
"""
import argparse
import json

import numpy as np
from sklearn.metrics import classification_report
from sklearn.model_selection import GroupShuffleSplit

from detection.config import LABELS, ROOT
from detection.train import load_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="xlm-roberta-base")
    parser.add_argument("--epochs", type=float, default=3)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--out", default=str(ROOT / "models" / "xlmr"))
    args = parser.parse_args()

    import torch
    from datasets import Dataset
    from transformers import (AutoModelForSequenceClassification, AutoTokenizer, Trainer,
                              TrainingArguments)

    data = load_data()
    label2id = {l: i for i, l in enumerate(LABELS)}
    data["labels"] = data["label"].map(label2id)
    split = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=7)
    train_idx, test_idx = next(split.split(data, groups=data["template_id"]))
    train_df, test_df = data.iloc[train_idx], data.iloc[test_idx]

    tok = AutoTokenizer.from_pretrained(args.model)

    def encode(df):
        ds = Dataset.from_pandas(df[["clean", "labels"]].reset_index(drop=True))
        return ds.map(lambda b: tok(b["clean"], truncation=True, max_length=128), batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, num_labels=len(LABELS), id2label=dict(enumerate(LABELS)), label2id=label2id)

    trainer = Trainer(
        model=model,
        args=TrainingArguments(output_dir=args.out, num_train_epochs=args.epochs,
                               per_device_train_batch_size=args.batch, learning_rate=2e-5,
                               weight_decay=0.01, logging_steps=20, save_strategy="no",
                               report_to=[], fp16=torch.cuda.is_available(), seed=42),
        train_dataset=encode(train_df),
        tokenizer=tok,
    )
    trainer.train()

    logits = trainer.predict(encode(test_df)).predictions
    pred = [LABELS[i] for i in np.argmax(logits, axis=1)]
    report = classification_report(test_df["label"], pred, zero_division=0, output_dict=True)
    print(classification_report(test_df["label"], pred, zero_division=0))
    by_lang = {}
    for lang in test_df["language"].unique():
        mask = (test_df["language"] == lang).values & (test_df["label"] == "phishing").values
        if mask.sum():
            by_lang[lang] = float(np.mean(np.array(pred)[mask] == "phishing"))
    print("Phishing recall by language:", by_lang)
    print("PRELIMINARY: mostly synthetic data, unseen templates only.")

    trainer.save_model(args.out)
    tok.save_pretrained(args.out)
    with open(f"{args.out}/results.json", "w") as f:
        json.dump({"macro_f1": report["macro avg"]["f1-score"], "phishing_recall_by_language": by_lang}, f, indent=2)


if __name__ == "__main__":
    main()
