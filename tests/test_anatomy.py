from detection.anatomy import extract
from detection.preprocess import clean


def anatomy(text, sender=None):
    return extract(clean(text)[0], sender)


def test_singlish_zero_link_call():
    a = anatomy("Orion Bank: obage account eka block wenawa. Wahama 0771234567 ta call karanna.")
    assert a["claimed_bank"]["id"] == "orion"
    assert a["primary_action"] == "call"
    assert a["contacts"][0]["normalized"] == "0771234567"
    assert a["zero_link"] and "URGENCY" in a["tactics"]


def test_otp_request_vs_real_otp_message():
    scam = anatomy("Demo Bank: to cancel the transfer, reply with the OTP you just received.")
    real = anatomy("Orion Bank: Your OTP for payment of LKR 4,850.00 is 483920. Do not share this code.")
    assert scam["primary_action"] == "share_credential"
    assert real["primary_action"] == "none"


def test_call_needs_a_number():
    a = anatomy("Orion Bank: LKR 500 debited. Not you? Call the number on the back of your card.")
    assert a["primary_action"] == "none"


def test_legitimate_bill_reminder_still_requests_payment():
    a = anatomy("Orion Bank: Please pay before the due date to avoid late fees.")
    assert a["primary_action"] == "pay"


def test_fee_scam_and_link():
    assert anatomy("Pay the processing fee of LKR 4,500 to release your loan.")["primary_action"] == "pay"
    a = anatomy("Verify now: hxxps://orion-verify[.]example/login")
    assert a["contacts"][0] == {"type": "url", "value": "hxxps://orion-verify[.]example/login",
                                "normalized": "orion-verify.example"}


def test_sinhala_call():
    a = anatomy("Orion Bank: ඔබගේ ගිණුම අවහිර වේ. කරුණාකර වහාම 0771234567 අමතන්න.")
    assert a["primary_action"] == "call" and "ACCOUNT_THREAT" in a["tactics"]
