"""Hand-authored diagnostic fixtures, not a held-out gold dataset.
Sinhala/Singlish translations require native-speaker adjudication.
"""
FAMILIES = [
    ('otp', 'Credential request', 'phishing', 'share_credential', {
        'en': 'Demo Bank: reply with your OTP to unlock your account.',
        'singlish': 'Demo Bank: account eka unlock karanna OTP eka ewanna.',
        'si': 'Demo Bank: ඔබගේ ගිණුම සඳහා OTP අංකය එවන්න.'}),
    ('negation', 'Safety advice / negation', 'legit', 'none', {
        'en': 'Demo Bank: Never share your OTP with anyone.',
        'singlish': 'Demo Bank: OTP eka denna epa.',
        'si': 'Demo Bank: OTP අංකය දෙන්න එපා.'}),
    ('callback', 'Zero-link callback', 'phishing', 'call', {
        'en': 'Orion Bank: your account is blocked. Call 0771234567 now.',
        'singlish': 'Orion Bank: obage account eka block wela. Wahama 0771234567 ta call karanna.',
        'si': 'Orion Bank: ඔබගේ ගිණුම අවහිර වේ. 0771234567 අමතන්න.'}),
    ('receipt', 'Transaction notification', 'legit', 'none', {
        'en': 'Orion Bank: LKR 500 credited to your account. Balance LKR 1500.',
        'singlish': 'Orion Bank: obage account ekata Rs 500 credit una. Shesaya Rs 1500.',
        'si': 'Orion Bank: ඔබගේ ගිණුමට රුපියල් 500 බැර විය.'}),
]
CASES = [{'id': f'{family}-{lang}', 'family': family, 'name': name, 'language': lang,
          'text': text, 'label': label, 'expected_action': action,
          'provenance': 'hand_authored_diagnostic', 'needs_language_review': lang != 'en'}
         for family, name, label, action, texts in FAMILIES for lang, text in texts.items()]
CASES += [
    {'id': 'reported-en', 'family': 'reported', 'name': 'Reported scam request', 'language': 'en',
     'text': 'Someone called and asked me to share my OTP.', 'label': 'legit', 'expected_action': 'none'},
    {'id': 'contrast-en', 'family': 'contrast', 'name': 'Safety advice followed by a request', 'language': 'en',
     'text': 'Do not share your OTP, but send your PIN now.', 'label': 'phishing', 'expected_action': 'share_credential'},
    {'id': 'bare-link-en', 'family': 'bare-link', 'name': 'A contact is not a request', 'language': 'en',
     'text': 'Our website is orionbank.example.', 'label': 'legit', 'expected_action': 'none'},
]

# Deliberately difficult cases remain visible to expose current rule limitations.
CASES += [
    {'id': 'indirect-en', 'family': 'indirect', 'name': 'Indirect credential request / challenge', 'language': 'en',
     'text': 'For verification, we need the code sent to your phone.', 'label': 'phishing', 'expected_action': 'share_credential'},
    {'id': 'reported-singlish', 'family': 'reported', 'name': 'Reported speech / challenge', 'language': 'singlish',
     'text': 'OTP eka denna kiyala kenek mata kiwwa.', 'label': 'legit', 'expected_action': 'none', 'needs_language_review': True},
    {'id': 'reported-si', 'family': 'reported', 'name': 'Reported speech / challenge', 'language': 'si',
     'text': 'කෙනෙක් මට OTP අංකය දෙන්න කිව්වා.', 'label': 'legit', 'expected_action': 'none', 'needs_language_review': True},
]


def case(case_id):
    found = next((c for c in CASES if c['id'] == case_id), None)
    if found is None:
        raise ValueError('Unknown diagnostic case')
    return dict(found)
