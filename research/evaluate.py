"""Evaluate independent component outputs against annotated JSONL.

python -m research.evaluate annotations.jsonl --output report.json
Rows include id, group_id, split, language, text, label, actions, primary_action.
Optional: pair_id (meaning-equivalent variants), expert_tier, checks, score.
Never evaluates the installed classifier on data it may have trained on.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from sklearn.metrics import f1_score, cohen_kappa_score
from sklearn.preprocessing import MultiLabelBinarizer
from detection.anatomy import extract, HARM
from detection.preprocess import clean
from verify.risk import assess, likelihood, MATRIX, TIERS


def load_rows(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    seen, groups, pairs = set(), {}, {}
    normalized = {}
    for r in rows:
        for field in ('id', 'group_id', 'split', 'language', 'text', 'label', 'actions', 'primary_action'):
            if field not in r:
                raise ValueError(f'Missing {field}')
        if r['id'] in seen or r['split'] not in ('train', 'validation', 'test'):
            raise ValueError('Duplicate ID or invalid split')
        seen.add(r['id'])
        if not r['group_id'] or not r['text'].strip():
            raise ValueError('Text and group_id must not be empty')
        if r['label'] not in ('legit', 'spam', 'phishing'):
            raise ValueError('Use substantive labels legit/spam/phishing; uncertainty is not a label')
        if not r['actions'] or not set(r['actions']) <= set(HARM) or r['primary_action'] not in r['actions']:
            raise ValueError('Invalid actions')
        if 'none' in r['actions'] and len(r['actions']) > 1:
            raise ValueError('none cannot coexist with an action')
        for mapping, key in ((groups, r['group_id']), (pairs, r.get('pair_id')),
                             (normalized, clean(r['text'])[0].casefold())):
            if not key:
                continue
            if key in mapping and mapping[key] != r['split']:
                raise ValueError('Group, variant pair, or duplicate text leaks across splits')
            mapping[key] = r['split']
    return rows


def action_metrics(rows, predicted):
    labels = list(HARM)
    encoder = MultiLabelBinarizer(classes=labels).fit([labels])
    y, p = encoder.transform([r['actions'] for r in rows]), encoder.transform(predicted)
    return {'n': len(rows), 'macro_f1': float(f1_score(y, p, average='macro', zero_division=0)),
            'micro_f1': float(f1_score(y, p, average='micro', zero_division=0)),
            'exact_match': sum(set(r['actions']) == set(a) for r, a in zip(rows, predicted)) / len(rows)}


def evaluate(rows):
    test = [r for r in rows if r['split'] == 'test']
    if not test:
        raise ValueError('No held-out test rows')
    predicted = [extract(clean(r['text'])[0]) for r in test]
    report = {'status': 'evaluation_only_not_a_novelty_claim', 'actions': action_metrics(test, [p['actions'] for p in predicted]), 'by_language': {}}
    for lang in sorted({r['language'] for r in test}):
        indices = [i for i, r in enumerate(test) if r['language'] == lang]
        report['by_language'][lang] = action_metrics([test[i] for i in indices], [predicted[i]['actions'] for i in indices])
    pairs = defaultdict(list)
    for row, pred in zip(test, predicted):
        if row.get('pair_id'):
            pairs[row['pair_id']].append((set(row['actions']), set(pred['actions'])))
    paired = [v for v in pairs.values() if len(v) > 1]
    if any(any(gold != values[0][0] for gold, _ in values) for values in paired):
        raise ValueError('Meaning-equivalent pairs must have the same gold actions')
    report['variant_consistency'] = {'groups': len(paired), 'rate': sum(all(p == v[0][1] for _, p in v) for v in paired) / len(paired) if paired else None}
    # Use gold actions to isolate C2; repeat with predicted actions to expose propagation.
    report['risk'] = {}
    eligible = [(r, p) for r, p in zip(test, predicted) if 'score' in r and 'expert_tier' in r and 'checks' in r]
    for coverage in (0.0, 0.5, 1.0):
        for mode in ('gold_actions', 'predicted_actions'):
            for policy in ('matrix', 'evidence'):
                accepted, ranked = [], []
                for row, pred in eligible:
                    if row['expert_tier'] not in TIERS or not 0 <= row['score'] <= 1:
                        raise ValueError('Invalid expert tier or score')
                    import hashlib
                    checks = [c for i, c in enumerate(row['checks']) if int(hashlib.sha256(f"{row['id']}:{i}".encode()).hexdigest()[:8], 16) / 0xffffffff < coverage]
                    action = row['primary_action'] if mode == 'gold_actions' else pred['primary_action']
                    out = assess(row['score'], action, checks, pred['action_uncertainty'] if mode == 'predicted_actions' else 'rule_based')
                    tier = MATRIX[likelihood(row['score'])][HARM[action]] if policy == 'matrix' else out['tier']
                    if policy == 'matrix' or not out['abstain']:
                        accepted.append((row, tier))
                        ranked.append((TIERS.index(row['expert_tier']), TIERS.index(tier)))
                danger = [(r, t) for r, t in accepted if r['label'] == 'phishing' and HARM[r['primary_action']] == 3]
                report['risk'][f'{mode}/{policy}/coverage_{coverage}'] = {
                    'n': len(eligible), 'answered': len(accepted),
                    'decision_coverage': len(accepted) / len(eligible) if eligible else None,
                    'tier_error': sum(a != b for a, b in ranked) / len(ranked) if ranked else None,
                    'false_low_risk_n': len(danger),
                    'false_low_risk_rate': sum(t in ('Low', 'Medium') for _, t in danger) / len(danger) if danger else None,
                    'weighted_kappa': float(cohen_kappa_score(*zip(*ranked), labels=list(range(4)), weights='quadratic')) if ranked and len({x for pair in ranked for x in pair}) > 1 else None}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('annotations'); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    report = evaluate(load_rows(args.annotations))
    Path(args.output).write_text(json.dumps(report, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
