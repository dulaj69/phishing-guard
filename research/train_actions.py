"""Train an optional supervised action baseline using human-labelled training rows.

No automatic deployment; compare this baseline before implementing joint XLM-R.
python -m research.train_actions annotations.jsonl --output work/actions.joblib
"""
import argparse
import json
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MultiLabelBinarizer
from detection.anatomy import HARM
from detection.preprocess import clean
from research.evaluate import load_rows, action_metrics


def train(rows, output):
    train_rows = [r for r in rows if r['split'] == 'train']
    test_rows = [r for r in rows if r['split'] == 'test']
    if not train_rows or not test_rows:
        raise ValueError('Separate train and test rows required')
    encoder = MultiLabelBinarizer(classes=list(HARM)).fit([list(HARM)])
    labels = encoder.transform([r['actions'] for r in train_rows])
    model = Pipeline([('text', TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 5))),
                      ('actions', OneVsRestClassifier(LogisticRegression(max_iter=1000, class_weight='balanced')))])
    model.fit([clean(r['text'])[0] for r in train_rows], labels)
    pred = encoder.inverse_transform(model.predict([clean(r['text'])[0] for r in test_rows]))
    pred = [list(set(p) - {'none'}) or ['none'] for p in pred]
    output = Path(output); output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model': model, 'encoder': encoder, 'method': 'supervised_action_baseline_v1',
                 'training_ids': [r['id'] for r in train_rows]}, output)
    report = action_metrics(test_rows, pred)
    report['limitations'] = 'Baseline only; no calibrated action confidence or joint/consistency training.'
    output.with_suffix('.metrics.json').write_text(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('annotations'); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    train(load_rows(args.annotations), args.output)
