"""Source-scoped registry checks. Absence is unknown unless coverage is explicit."""
import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from detection.anatomy import normalize_phone

REGISTRY_PATH = Path(__file__).resolve().parent / 'data' / 'bank_registry.json'
MAX_SOURCE_AGE_DAYS = 180  # provisional; evaluate sensitivity, not a bank guarantee


@lru_cache(maxsize=1)
def load_registry(path=REGISTRY_PATH):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    return {bank['id']: bank for bank in data['banks']}


def find_bank(claimed):
    if not claimed:
        return None
    banks = load_registry()
    if claimed.get('id') in banks:
        return banks[claimed['id']]
    name = (claimed.get('name') or '').lower()
    return next((b for b in banks.values() if name in
                 [b['name'].lower()] + [a.lower() for a in b.get('aliases', [])]), None)


def source_for(bank, field, today=None):
    # Real entries require a source attached to the exact field/rule being checked.
    source = bank.get('fact_sources', {}).get(field)
    if source is None and bank.get('fictional'):
        source = (bank.get('sources') or [{}])[0]
    source = dict(source or {})
    try:
        age = ((today or date.today()) - date.fromisoformat(source.get('checked', ''))).days
        fresh = 0 <= age <= MAX_SOURCE_AGE_DAYS
    except (TypeError, ValueError):
        fresh = False
    source.update({'freshness': 'current' if fresh else 'stale_or_missing',
                   'fictional': bool(bank.get('fictional')), 'field': field})
    return source


def _result(bank, field, check, result, detail, value=None, today=None):
    source = source_for(bank, field, today) if bank else None
    if source and (source['freshness'] != 'current' or not source.get('url')):
        result, detail = 'unknown', 'Evidence is stale or missing; independently verify this detail.'
    return {'check': check, 'result': result, 'detail': detail, 'value': value,
            'source': source, 'evidence_status': {'pass': 'supported', 'fail': 'contradicted',
                                               'unknown': 'unverified'}[result]}


def check(anatomy, sender=None, today=None):
    bank = find_bank(anatomy.get('claimed_bank'))
    results = []
    if not bank:
        results.append(_result(None, '', 'bank_known', 'unknown',
                               'The claimed bank is not covered by the registry.'))
    for contact in anatomy.get('contacts', []):
        kind, value = contact['type'], contact['normalized']
        if kind not in ('phone', 'short_code', 'url'):
            continue
        field = 'official_domains' if kind == 'url' else 'official_numbers'
        name = 'official_domain' if kind == 'url' else 'official_number'
        if not bank:
            results.append(_result(None, field, name, 'unknown', 'No bank evidence available.', value))
            continue
        if kind == 'url':
            ok = any(value == d or value.endswith('.' + d) for d in bank.get(field, []))
        else:
            numbers = bank.get(field, []) + bank.get('short_codes', [])
            ok = normalize_phone(value) in {normalize_phone(n) for n in numbers}
        complete = bank.get('coverage', {}).get(field) == 'complete'
        result = 'pass' if ok else ('fail' if complete else 'unknown')
        detail = (f'{value} matches a published {bank["name"]} detail; this does not authenticate the SMS.'
                  if ok else f'{value} is not listed in the registry; absence alone does not prove fraud.')
        if result == 'fail':
            detail = f'{value} contradicts the bank’s explicitly complete published list.'
        results.append(_result(bank, field, name, result, detail, value, today))

    if bank:
        # Only contradict the specific credential policy supported by the source.
        evidence = anatomy.get('action_evidence', [])
        credential_text = ' '.join(e['text'] for e in evidence
                                   if e['action'] == 'share_credential' and e['status'] == 'requested').lower()
        import re
        checks = [('never_asks_otp', r'otp|ඕටීපී|one.time|verification code'),
                  ('never_asks_pin', r'\bpin\b'),
                  ('never_asks_card_details', r'card|cvv|expiry'),
                  ('never_asks_password', r'password|මුරපදය')]
        for rule, pattern in checks:
            if bank.get('rules', {}).get(rule) and re.search(pattern, credential_text, re.I):
                results.append(_result(bank, rule, 'bank_rule', 'fail',
                    f'The requested credential conflicts with {bank["name"]} policy ({rule}).', today=today))
        if anatomy.get('primary_action') == 'install' and bank.get('rules', {}).get('never_asks_to_install_apps'):
            results.append(_result(bank, 'never_asks_to_install_apps', 'bank_rule', 'fail',
                                  'The install request conflicts with the published bank policy.', today=today))
        if sender:
            ok = sender.upper() in [s.upper() for s in bank.get('sender_ids', [])]
            results.append(_result(bank, 'sender_ids', 'sender_id', 'pass' if ok else 'unknown',
                'Sender name matches a published name but can be spoofed.' if ok else
                'Sender name is unverified; the registry may be incomplete.', sender, today))
    return results


def official_contact(anatomy, today=None):
    bank = find_bank(anatomy.get('claimed_bank'))
    if not bank or bank.get('fictional') or not bank.get('official_numbers'):
        return None
    source = source_for(bank, 'official_numbers', today)
    if source['freshness'] != 'current' or not source.get('url'):
        return None
    return {'bank': bank['name'], 'number': bank['official_numbers'][0], 'source': source}
