"""Experimental joint classification/action training with paired-view consistency.

Requires requirements-ml.txt and an annotated train/validation/test JSONL.
Loads a Hugging Face encoder (network/model download when not cached).
python -m research.train_joint data/real/annotations.jsonl --out work/joint --consistency 0.2
Compare identical seeds/splits with --consistency 0. Uses gold action labels,
not rule-generated pseudo-labels. Never changes the production model.
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from detection.anatomy import HARM
from detection.preprocess import clean
from research.evaluate import load_rows, action_metrics

LABELS = ['legit', 'spam', 'phishing']
ACTIONS = list(HARM)


def paired_training_rows(rows):
    """Deterministic equivalent views; never pair across groups/splits or labels."""
    groups = defaultdict(list)
    for r in rows:
        if r.get('pair_id'):
            groups[r['pair_id']].append(r)
    pairs = {}
    for variants in groups.values():
        first = variants[0]
        if any((r['label'], set(r['actions']), r['group_id'], r['split']) !=
               (first['label'], set(first['actions']), first['group_id'], first['split']) for r in variants):
            raise ValueError('Paired views must share meaning, label, group and split')
        for i, r in enumerate(variants):
            pairs[r['id']] = variants[(i + 1) % len(variants)]
    return [(r, pairs.get(r['id'], r)) for r in rows]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('annotations'); p.add_argument('--out', required=True)
    p.add_argument('--model', default='xlm-roberta-base')
    p.add_argument('--epochs', type=int, default=3); p.add_argument('--batch', type=int, default=8)
    p.add_argument('--seed', type=int, default=7); p.add_argument('--consistency', type=float, default=0.2)
    p.add_argument('--action-weight', type=float, default=1.0)
    args = p.parse_args()
    if args.epochs < 1 or args.batch < 1 or args.consistency < 0 or args.action_weight < 0:
        p.error('Epochs/batch must be positive and loss weights non-negative')
    rows = load_rows(args.annotations)
    splits = {s: [r for r in rows if r['split'] == s] for s in ('train', 'validation', 'test')}
    if not all(splits.values()):
        p.error('Human-labelled train, validation and test splits are all required')
    paired_training_rows(rows)  # validate all declared equivalences before training
    pairs = paired_training_rows(splits['train'])
    if args.consistency and not any(a['id'] != b['id'] for a, b in pairs):
        p.error('Consistency training requires at least one annotated equivalent pair in train')

    import torch
    from torch import nn
    from transformers import AutoModel, AutoTokenizer
    from sklearn.metrics import f1_score

    random.seed(args.seed); torch.manual_seed(args.seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    class Joint(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = AutoModel.from_pretrained(args.model)
            self.classes = nn.Linear(self.encoder.config.hidden_size, len(LABELS))
            self.actions = nn.Linear(self.encoder.config.hidden_size, len(ACTIONS))

        def forward(self, batch):
            h = self.encoder(**batch).last_hidden_state
            mask = batch['attention_mask'].unsqueeze(-1)
            pooled = (h * mask).sum(1) / mask.sum(1).clamp_min(1)
            return self.classes(pooled), self.actions(pooled)

    model = Joint().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    def encode(batch):
        return tokenizer([clean(r['text'])[0] for r in batch], padding=True, truncation=True,
                         max_length=256, return_tensors='pt').to(device)

    def supervised(logits, batch):
        classes, actions = logits
        y = torch.tensor([LABELS.index(r['label']) for r in batch], device=device)
        a = torch.tensor([[float(k in r['actions']) for k in ACTIONS] for r in batch], device=device)
        return nn.functional.cross_entropy(classes, y) + args.action_weight * nn.functional.binary_cross_entropy_with_logits(actions, a)

    def evaluate_split(batch_rows):
        model.eval(); predicted_classes, predicted_actions = [], []
        with torch.no_grad():
            for i in range(0, len(batch_rows), args.batch):
                c, a = model(encode(batch_rows[i:i+args.batch]))
                predicted_classes.extend(LABELS[j] for j in c.argmax(-1).cpu().tolist())
                for values in a.sigmoid().cpu().tolist():
                    predicted_actions.append([k for k, v in zip(ACTIONS, values) if v >= .5 and k != 'none'] or ['none'])
        return {'classification_macro_f1': float(f1_score([r['label'] for r in batch_rows], predicted_classes,
                    labels=LABELS, average='macro', zero_division=0)),
                'actions': action_metrics(batch_rows, predicted_actions)}

    best = -1
    for epoch in range(args.epochs):
        model.train(); random.shuffle(pairs)
        for i in range(0, len(pairs), args.batch):
            batch = pairs[i:i+args.batch]; left, right = map(list, zip(*batch))
            optimizer.zero_grad()
            logits = model(encode(left)); loss = supervised(logits, left)
            if args.consistency:
                other = model(encode(right))
                loss = (loss + supervised(other, right)) / 2
                mask = torch.tensor([a['id'] != b['id'] for a, b in batch], device=device)
                if mask.any():
                    c = (logits[0].softmax(-1) - other[0].softmax(-1)).square().mean(-1)
                    a = (logits[1].sigmoid() - other[1].sigmoid()).square().mean(-1)
                    loss = loss + args.consistency * (c[mask] + a[mask]).mean()
            loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); optimizer.step()
        validation = evaluate_split(splits['validation'])
        criterion = validation['classification_macro_f1'] + validation['actions']['macro_f1']
        if criterion > best:
            best = criterion
            torch.save(model.state_dict(), out / 'joint.pt')
            (out / 'validation.json').write_text(json.dumps({'epoch': epoch+1, **validation}, indent=2))
    # Test set is used once after validation selection; fixed 0.5 action threshold.
    model.load_state_dict(torch.load(out / 'joint.pt', map_location=device, weights_only=True))
    report = evaluate_split(splits['test'])
    report['by_language'] = {lang: evaluate_split([r for r in splits['test'] if r['language'] == lang])
                             for lang in sorted({r['language'] for r in splits['test']})}
    (out / 'test.json').write_text(json.dumps(report, indent=2))
    tokenizer.save_pretrained(out / 'tokenizer')
    model.encoder.config.save_pretrained(out / 'encoder_config')
    (out / 'manifest.json').write_text(json.dumps({**vars(args), 'labels': LABELS, 'actions': ACTIONS,
         'train_ids': [r['id'] for r in splits['train']], 'status': 'experimental_not_deployed'}, indent=2))


if __name__ == '__main__':
    main()
