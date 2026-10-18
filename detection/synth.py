"""Make SYNTHETIC training messages from templates (English, Singlish, Sinhala).

Why: we only have 36 hand-written seed messages. This gives the PP1 demo model
enough examples to learn from, while real donated messages are being collected.

IMPORTANT
- Synthetic data is for TRAINING ONLY. Never report final results on it.
  The final test set must be real, hand-labelled messages (the gold set).
- Banks are fictional (Orion Bank, Demo Bank). Phone numbers are random.
- Sinhala and Singlish templates must be checked by a native speaker.
- Every row has a template_id, so train/test splits can keep whole templates
  apart (otherwise the model just memorises the template and scores look fake-high).

Run:  python -m detection.synth
"""
import csv
import random

from detection.config import SYNTH_CSV

BANKS = [("Orion Bank", "ORIONBANK", "orionbank.example", "011 2000 100"),
         ("Demo Bank", "DEMOBANK", "demobank.example", "011 2000 000")]
MERCHANTS = ["ShopMart", "Keells", "Cargills", "Daraz", "PickMe", "Uber", "Dialog", "SLT"]
SCAM_DOMAINS = ["{b}-verify[.]top", "{b}-secure[.]xyz", "{b}-kyc[.]online", "bit[.]ly/{r}",
                "{b}-refund[.]site", "secure-{b}[.]link"]


def _rand_phone():
    return "07" + str(random.randint(0, 8)) + "".join(str(random.randint(0, 9)) for _ in range(7))


def _amount():
    return f"{random.choice([1200, 2500, 4850, 12500, 25000, 48000, 95000, 189000]):,}.00"


def _fill(t, bank):
    name, sender, domain, hotline = bank
    short = name.split()[0].lower()
    return t.format(
        bank=name, amt=_amount(), bal=_amount(), otp=random.randint(100000, 999999),
        acc=f"xxxx{random.randint(1000, 9999)}", merchant=random.choice(MERCHANTS),
        phone=_rand_phone(), hotline=hotline, domain=domain.replace(".", "[.]"),
        scam=random.choice(SCAM_DOMAINS).format(b=short, r=random.randint(1000, 9999)),
        hours=random.choice([2, 12, 24, 48]),
    )


# (template_id, label, language, primary_action, text)
TEMPLATES = [
    # ---------- LEGIT: English ----------
    ("L-en-otp", "legit", "en", "none", "{bank}: Your OTP for payment of LKR {amt} at {merchant} is {otp}. Valid for 5 minutes. Do not share this code with anyone."),
    ("L-en-debit", "legit", "en", "none", "{bank}: LKR {amt} debited from A/C {acc} at {merchant}. Avail. Bal: LKR {bal}."),
    ("L-en-credit", "legit", "en", "none", "{bank}: LKR {amt} credited to A/C {acc}. Avail. Bal: LKR {bal}. Thank you for banking with us."),
    ("L-en-due", "legit", "en", "none", "{bank}: Your credit card payment of LKR {amt} is due soon. Please pay before the due date to avoid late fees."),
    ("L-en-notyou", "legit", "en", "none", "{bank}: A transaction of LKR {amt} was made with your card at {merchant}. Not you? Call {hotline} or the number on the back of your card."),
    ("L-en-promo", "legit", "en", "click", "{bank}: Get 10% off at {merchant} this weekend with your {bank} card. T&Cs apply. {domain}/offers"),
    ("L-en-estmt", "legit", "en", "none", "{bank}: Your e-statement is ready in the {bank} app. We will never ask for your PIN, password or OTP."),
    # ---------- LEGIT: Singlish ----------
    ("L-sl-debit", "legit", "singlish", "none", "{bank}: Obage A/C {acc} eken Rs. {amt} k debit una. Shesaya: Rs. {bal}."),
    ("L-sl-credit", "legit", "singlish", "none", "{bank}: Obage A/C {acc} ekata Rs. {amt} k credit una. Shesaya: Rs. {bal}."),
    ("L-sl-otp", "legit", "singlish", "none", "{bank}: Obage OTP eka {otp}. Meka kisiwekuta denna epa."),
    # ---------- LEGIT: Sinhala ----------
    ("L-si-debit", "legit", "si", "none", "{bank}: ඔබගේ ගිණුමෙන් රු. {amt} ක් ඉවත් කරන ලදී. ශේෂය: රු. {bal}."),
    ("L-si-otp", "legit", "si", "none", "{bank}: ඔබගේ OTP අංකය {otp}. මෙය කිසිවෙකුට ලබා නොදෙන්න."),
    # ---------- PHISHING: English ----------
    ("P-en-block-call", "phishing", "en", "call", "{bank} ALERT: Your account will be blocked within {hours} hours. Call our security team on {phone} immediately."),
    ("P-en-tx-call", "phishing", "en", "call", "{bank}: Unauthorized transaction of LKR {amt} detected. If this was not you, call the fraud desk now on {phone}."),
    ("P-en-otp", "phishing", "en", "share_credential", "{bank} Security: To cancel the pending transfer of LKR {amt}, reply with the OTP you just received."),
    ("P-en-pin", "phishing", "en", "share_credential", "Dear customer, your {bank} card has been blocked. To reactivate, send your card PIN and expiry date to {phone}."),
    ("P-en-link", "phishing", "en", "click", "{bank}: Your account is suspended due to incomplete KYC. Verify now: hxxps://{scam}"),
    ("P-en-reward", "phishing", "en", "click", "{bank}: Congratulations! You have won a LKR {amt} cashback reward. Claim within {hours} hours: {scam}"),
    ("P-en-loanfee", "phishing", "en", "pay", "{bank}: Your loan of LKR {amt} is approved. Pay the processing fee of LKR 4,500 to release funds. Call {phone}."),
    ("P-en-app", "phishing", "en", "install", "{bank}: Your mobile banking will stop today. Install the new security app from {scam} to continue."),
    ("P-en-fluent", "phishing", "en", "share_credential", "Hello, this is the {bank} security team. We have limited your card after an unusual payment. To restore access, please reply with the verification code we just sent."),
    # ---------- PHISHING: Singlish ----------
    ("P-sl-block-call", "phishing", "singlish", "call", "{bank}: Obage account eka passe {hours} k athule block wenawa. Wahama {phone} ta call karanna."),
    ("P-sl-otp", "phishing", "singlish", "share_credential", "{bank}: Obage transaction eka cancel karanna ona nam, phone ekata ena OTP eka reply karanna."),
    ("P-sl-link", "phishing", "singlish", "click", "{bank}: Obage account eka update karanna ona. Meka click karanna: {scam}"),
    ("P-sl-reward", "phishing", "singlish", "call", "{bank}: Oyata Rs. {amt} cashback ekak labuna! Ganna {phone} ta call karanna."),
    # ---------- PHISHING: Sinhala ----------
    ("P-si-block-call", "phishing", "si", "call", "{bank}: ඔබගේ ගිණුම පැය {hours} ක් ඇතුළත අවහිර වේ. කරුණාකර වහාම {phone} අමතන්න."),
    ("P-si-otp", "phishing", "si", "share_credential", "{bank}: ඔබගේ ගිණුම සත්‍යාපනය කිරීමට ඔබට ලැබුණු OTP අංකය මෙම අංකයට එවන්න."),
    # ---------- SUSPICIOUS ----------
    ("S-en-loan", "suspicious", "en", "reply", "Congratulations! You are selected for a pre-approved personal loan of LKR {amt}. Reply YES to know more."),
    ("S-en-kyc", "suspicious", "en", "click", "Dear customer, your KYC may expire soon. Please update at your earliest convenience: {scam}"),
    ("S-sl-earn", "suspicious", "singlish", "click", "Gedara idan dawasakata Rs. {amt} hambu karanna. Join wenna: {scam}"),
]


def generate(per_template=30, seed=42):
    random.seed(seed)
    rows = []
    for template_id, label, lang, action, template in TEMPLATES:
        for i in range(per_template):
            bank = random.choice(BANKS)
            text = _fill(template, bank)
            rows.append({
                "id": f"{template_id}-{i:03d}", "text": text, "label": label, "language": lang,
                "template_id": template_id, "primary_action": action,
                "zero_link": int("[.]" not in text and "http" not in text),
                "source": "synthetic-v1", "needs_native_review": int(lang in ("si", "singlish")),
            })
    return rows


def main():
    rows = generate()
    SYNTH_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNTH_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic messages to {SYNTH_CSV}")


if __name__ == "__main__":
    main()
