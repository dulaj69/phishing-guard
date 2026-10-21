"""Controlled evidence interventions, explicitly simulated, never bank validation."""
from itertools import combinations
from verify.risk import assess, MATRIX, HARM_LEVEL, likelihood


SCENARIOS = {
    'callback': {'text': 'Orion Bank: account blocked. Call 0771234567 now. orionbank.example', 'action': 'call'},
    'credential': {'text': 'Orion Bank: share your OTP now. orionbank.example', 'action': 'share_credential'},
    'link': {'text': 'Orion Bank: open orionbank.example to verify your account.', 'action': 'click'},
}


def signature(result):
    return result['tier'], result['abstain']


def audit(score, action, checks, uncertainty='rule_based'):
    """Exact subset search is bounded by four scenario facts, not arbitrary user data."""
    base = assess(score, action, checks, uncertainty)
    removals = []
    for i, check in enumerate(checks):
        without = assess(score, action, checks[:i]+checks[i+1:], uncertainty)
        removals.append({'removed': check['id'], 'detail': check['detail'], 'tier': without['tier'],
                         'abstain': without['abstain'], 'decision_changed': signature(base) != signature(without)})
    minimal = []
    for count in range(len(checks)+1):
        for subset in combinations(checks, count):
            if signature(assess(score, action, list(subset), uncertainty)) == signature(base):
                minimal.append([c['id'] for c in subset])
        if minimal:
            break
    return base, removals, minimal


def run(scenario, score, contradiction, copied_domain, stale, missing, uncertainty):
    definition = SCENARIOS[scenario]
    source = {'url': 'https://orionbank.example/demo-policy', 'fictional': True,
              'freshness': 'stale_or_missing' if stale else 'current', 'checked': 'SIMULATED'}
    checks = []
    if not missing:
        if contradiction:
            checks.append({'id': 'contradiction', 'check': 'bank_rule' if scenario == 'credential' else 'official_number',
                           'result': 'unknown' if stale else 'fail', 'source': source,
                           'detail': 'Simulated contradiction unavailable because source is stale.' if stale else
                                     'Simulated explicit bank-policy or complete-list contradiction.'})
        if copied_domain:
            checks.append({'id': 'domain_match', 'check': 'official_domain',
                           'result': 'unknown' if stale else 'pass', 'source': source,
                           'detail': 'Simulated published-domain match; does not authenticate the SMS.'})
    u = 'uncertain' if uncertainty else 'rule_based'
    result, removed, minimal = audit(score, definition['action'], checks, u)
    coverage = []
    for name, facts in [('none', []), ('matches_only', [c for c in checks if c['result'] == 'pass']), ('available', checks)]:
        r = assess(score, definition['action'], facts, u)
        coverage.append({'evidence': name, 'tier': r['tier'], 'abstain': r['abstain']})
    return {'kind': 'controlled_simulation', 'scenario': definition, 'score': score,
            'assumptions': {'contradiction': contradiction, 'copied_domain': copied_domain,
                            'stale': stale, 'missing': missing, 'uncertain_action': uncertainty},
            'checks': checks, 'risk': result, 'removal_audit': removed, 'minimal_sufficient_sets': minimal,
            'baselines': {'likelihood_only': {'Low':'Low', 'Medium':'Medium', 'High':'High'}[likelihood(score)],
                          'matrix_only': MATRIX[likelihood(score)][HARM_LEVEL[definition['action']]],
                          'evidence_policy': result['tier']}, 'coverage': coverage,
            'limitation': 'Fictional evidence and manually controlled score. Minimal sets preserve this policy’s tier/abstention only; not causal proof or real-bank verification.'}
