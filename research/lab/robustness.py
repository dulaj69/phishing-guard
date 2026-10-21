"""Measure action contrast and perturbation behaviour on declared fixtures."""
import re
import joblib
from sklearn.metrics import f1_score
from detection import anatomy, model
from detection.preprocess import clean
from research.lab.cases import CASES, case

LIMITATION = ('Hand-authored diagnostic fixtures; possible training overlap. These results are not '
              'held-out accuracy, validated linguistic equivalence, or a novelty claim.')


def keyword_action(text):
    """Deliberately simple comparator: same lexicon, no clause/negation handling."""
    candidates = []
    rule = anatomy.ACTION_WORDS['share_credential']
    if re.search(rule['terms'], text, re.I) and re.search(rule['verbs'], text, re.I):
        candidates.append('share_credential')
    for action in ('pay', 'install', 'call', 'reply', 'click'):
        if re.search(anatomy.ACTION_WORDS[action], text, re.I):
            if action == 'call' and not (anatomy.PHONE.search(text) or anatomy.SHORT_CODE.search(text)):
                continue
            if action == 'click' and not anatomy.URL.search(text):
                continue
            candidates.append(action)
    return max(candidates, key=lambda a: (anatomy.HARM[a], -list(anatomy.HARM).index(a))) if candidates else 'none'


def fingerprint():
    return joblib.hash(model._model())[:16]


def variants(text):
    # Fixed defensive diagnostic operators; do not optimize messages for evasion.
    transforms = [
        ('original', 'Original', text),
        ('homoglyph', 'Latin o → Cyrillic look-alike', text.replace('o', 'о').replace('O', 'О')),
        ('spacing', 'Space credential letters', re.sub(r'\bOTP\b', 'O T P', text, flags=re.I)),
        ('hidden', 'Insert invisible character inside OTP', re.sub(r'\bOTP\b', 'O\u200bTP', text, flags=re.I)),
        ('case', 'Change letter case', text.swapcase()),
    ]
    seen, output = set(), []
    for key, name, value in transforms:
        if value not in seen:
            output.append((key, name, value)); seen.add(value)
    return output


def inspect(case_id):
    c = case(case_id)
    candidates = variants(c['text'])
    raw_probs = model.probabilities([t for _, _, t in candidates])
    results = model.detect([t for _, _, t in candidates])
    rows = []
    for (key, name, text), raw, result in zip(candidates, raw_probs, results):
        rows.append({'operator': key, 'name': name, 'text': text,
                     'normalized_text': result['normalized_text'], 'tricks': result['tricks_found'],
                     'raw_label': max(raw, key=raw.get), 'raw_score': model.scam_score(raw),
                     'label': result['label'], 'score': result['scam_score'],
                     'keyword_action': keyword_action(result['normalized_text']),
                     'action': result['anatomy']['primary_action'],
                     'action_correct': result['anatomy']['primary_action'] == c['expected_action'],
                     'evidence': result['anatomy']['action_evidence']})
    base = rows[0]
    return {'case': c, 'rows': rows, 'model_fingerprint': fingerprint(), 'limitation': LIMITATION,
            'summary': {'variants': len(rows),
                        'raw_label_changes': sum(r['raw_label'] != base['raw_label'] for r in rows[1:]),
                        'normalized_label_changes': sum(r['label'] != base['label'] for r in rows[1:]),
                        'correct_actions': sum(r['action_correct'] for r in rows)}}


def benchmark():
    analyses = [inspect(c['id']) for c in CASES]
    originals = [a['rows'][0] for a in analyses]
    per_language = []
    for language in sorted({c['language'] for c in CASES}):
        pairs = [(c, r) for c, r in zip(CASES, originals) if c['language'] == language]
        per_language.append({'language': language, 'n': len(pairs),
            'keyword_correct': sum(r['keyword_action'] == c['expected_action'] for c, r in pairs),
            'context_correct': sum(r['action'] == c['expected_action'] for c, r in pairs)})
    return {'kind': 'diagnostic_benchmark', 'model_fingerprint': fingerprint(), 'limitation': LIMITATION,
            'cases': len(CASES), 'per_language': per_language,
            'classification_macro_labels': ['legit', 'suspicious', 'phishing'],
            'class_support': {label: sum(c['label'] == label for c in CASES) for label in ['legit', 'suspicious', 'phishing']},
            'keyword_correct': sum(r['keyword_action'] == c['expected_action'] for c, r in zip(CASES, originals)),
            'context_correct': sum(r['action'] == c['expected_action'] for c, r in zip(CASES, originals)),
            'classification_macro_f1': float(f1_score([c['label'] for c in CASES], [r['label'] for r in originals],
                                                     labels=['legit', 'suspicious', 'phishing'], average='macro', zero_division=0)),
            'rows': [{'id': c['id'], 'language': c['language'], 'text': c['text'],
                      'expected': c['expected_action'], 'keyword': r['keyword_action'], 'context': r['action'],
                      'correct': r['action_correct']} for c, r in zip(CASES, originals)]}
