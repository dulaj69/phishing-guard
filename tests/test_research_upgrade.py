import json
from datetime import date

import pytest
from detection.anatomy import extract
from verify import fact_check, risk
from warn import reliance
from research.evaluate import load_rows, evaluate


@pytest.mark.parametrize('text,expected,status', [
    ('Tell us your OTP.', 'share_credential', 'requested'),
    ('Never tell anyone your OTP.', 'none', 'negated'),
    ('Someone called and asked me to share my OTP.', 'none', 'reported'),
    ('Do not call 0771234567.', 'none', 'negated'),
    ('Do not share your OTP, but send your PIN now.', 'share_credential', 'requested'),
    ('OTP eka kiyanna.', 'share_credential', 'requested'),
    ('OTP eka denna epa.', 'none', 'negated'),
    ('Visit bank.example now.', 'click', 'requested'),
    ('Our website is bank.example.', 'none', None),
])
def test_action_context_and_exact_spans(text, expected, status):
    output = extract(text)
    assert output['primary_action'] == expected
    if status:
        assert any(e['status'] == status for e in output['action_evidence'])
    for e in output['action_evidence']:
        assert text[e['start']:e['end']] == e['text']


def real_bank(monkeypatch, checked='2026-10-18', complete=False):
    bank = {'id': 'test', 'name': 'Test Bank', 'fictional': False,
            'official_numbers': ['0112223333'], 'official_domains': ['test.example'],
            'rules': {'never_asks_otp': True},
            'fact_sources': {f: {'url': 'https://test.example/policy', 'checked': checked}
                             for f in ('official_numbers', 'official_domains', 'never_asks_otp')},
            'coverage': {'official_numbers': 'complete' if complete else 'partial'}}
    monkeypatch.setattr(fact_check, 'load_registry', lambda: {'test': bank})
    return {'claimed_bank': {'id': 'test'}, 'primary_action': 'call',
            'contacts': [{'type': 'phone', 'normalized': '0771234567'}]}


def test_registry_missing_stale_and_explicit_complete(monkeypatch):
    a = real_bank(monkeypatch)
    assert fact_check.check(a, today=date(2026, 10, 18))[0]['result'] == 'unknown'
    a = real_bank(monkeypatch, complete=True)
    assert fact_check.check(a, today=date(2026, 10, 18))[0]['result'] == 'fail'
    a = real_bank(monkeypatch, checked='2020-01-01', complete=True)
    assert fact_check.check(a, today=date(2026, 10, 18))[0]['result'] == 'unknown'
    assert fact_check.official_contact(a, today=date(2026, 10, 18)) is None


def test_safe_contact_requires_current_fact_source(monkeypatch):
    a = real_bank(monkeypatch)
    assert fact_check.official_contact(a, today=date(2026, 10, 18))['number'] == '0112223333'


def test_matching_details_cannot_override_credential_request():
    checks = [{'check': 'official_domain', 'result': 'pass', 'detail': 'Copied domain'}]
    r = risk.assess(.05, 'share_credential', checks)
    assert r['tier'] == 'High' and not r['abstain'] and r['adjustment'] != 'down'
    assert risk.assess(.5, 'call', [])['abstain']
    assert risk.assess(.1, 'none', [], 'uncertain')['abstain']


def test_reliance_excludes_missing_initial_truth_and_abstention(tmp_path):
    for i, (initial, truth, ai) in enumerate([(None, 'scam', 'safe'), ('safe', None, 'safe'), ('safe', 'scam', 'uncertain')]):
        reliance.record({'user_id': 'P', 'message_id': str(i), 'initial_choice': initial,
                         'ai_advice': ai, 'final_choice': 'safe', 'truth': truth})
    p = reliance.profile('P')
    assert p['decisions'] == 0 and p['RAIR'] is None and p['RSR'] is None


def test_evidence_policy_ablation():
    p = {'intervention': 'light'}
    r = {'abstain': True, 'evidence_quality': 'insufficient'}
    assert reliance.choose_warning(p, r, 'static') == 'standard'
    assert reliance.choose_warning(p, r, 'user_only') == 'light'
    assert reliance.choose_warning(p, r, 'evidence_aware') == 'uncertainty'


def row(i, text, split, group):
    return {'id': i, 'text': text, 'split': split, 'group_id': group, 'language': 'en',
            'label': 'phishing', 'actions': ['share_credential'], 'primary_action': 'share_credential'}


def test_evaluator_rejects_group_leakage_and_reports_missing_evidence(tmp_path):
    path = tmp_path / 'gold.jsonl'
    rows = [row('a', 'Send OTP', 'train', 'same'), row('b', 'Tell us your OTP', 'test', 'same')]
    path.write_text('\n'.join(json.dumps(r) for r in rows))
    with pytest.raises(ValueError, match='leaks'):
        load_rows(path)
    rows[0]['group_id'] = 'different'
    path.write_text('\n'.join(json.dumps(r) for r in rows))
    report = evaluate(load_rows(path))
    assert report['actions']['exact_match'] == 1
    assert report['variant_consistency']['rate'] is None
    assert all(v['n'] == 0 for v in report['risk'].values())


def test_joint_views_are_meaning_preserving():
    from research.train_joint import paired_training_rows
    a = row('a', 'Send OTP', 'train', 'same')
    b = row('b', 'OTP eka denna', 'train', 'same')
    a['pair_id'] = b['pair_id'] = 'pair'
    assert paired_training_rows([a, b])[0][1]['id'] == 'b'
    b['actions'] = ['none']
    with pytest.raises(ValueError, match='share meaning'):
        paired_training_rows([a, b])


def test_supervised_action_baseline_can_train_without_deploying(tmp_path):
    from research.train_actions import train
    rows = [row('a', 'Tell us your OTP', 'train', 'a'), row('b', 'Please send OTP', 'test', 'b')]
    benign = row('c', 'Your balance is ready', 'train', 'c')
    benign.update(label='legit', actions=['none'], primary_action='none')
    out = tmp_path / 'actions.joblib'
    with pytest.warns(UserWarning):  # tiny fixture intentionally lacks other actions
        report = train(rows + [benign], out)
    assert out.exists() and report['n'] == 1


def test_study_summary_excludes_abstention_from_reliance():
    from research.study_report import summarize
    common = {'user_id': 'P', 'session': '1', 'condition': 'static', 'truth': 'scam',
              'initial_choice': 'safe', 'final_choice': 'scam', 'action': 'report', 'seconds': '2'}
    summary = summarize([{**common, 'ai_advice': 'scam'}, {**common, 'ai_advice': 'uncertain'}])
    p = summary['participant_sessions'][0]
    assert summary['participants'] == 1 and p['RAIR_n'] == 1 and p['abstentions'] == 1


def test_claimed_bank_not_overridden_by_spoofable_sender():
    assert extract('Demo Bank: send OTP', sender='ORIONBANK')['claimed_bank']['id'] == 'demo'
    assert extract('Fake Bank: send OTP', sender='ORIONBANK')['claimed_bank']['name'] == 'Fake Bank'
