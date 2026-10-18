"""Step 2b: find the 'scam anatomy' with rules.

For every message we find:
  - claimed_bank:   which bank it says it is from
  - actions:        what it wants you to do (share OTP, pay, install, call, reply, click)
  - contacts:       the phone numbers and links it pushes
  - tactics:        pressure tricks (urgency, account threat, reward, authority, fee)
  - spans:          where each of these sits in the text, for highlighting

This is version 0 (rules). In Phase 3 a trained model (Head B) does the same job;
these rules stay as a safety net so a phone number or link is never missed.
English, Singlish and Sinhala keywords are included. Sinhala keywords need a
native-speaker check.
"""
import json
import re
from functools import lru_cache

from detection.config import REGISTRY_PATH

HARM = {"share_credential": 3, "pay": 3, "install": 3, "call": 2, "reply": 2,
        "click": 1, "none": 0}

PHONE = re.compile(
    r"(?<![\w])(?:\+94|0094|0)\s?(?:7[\dX](?:[\s-]?[\dX]){7}|[1-9]\d(?:[\s-]?\d){7})(?![\w])"
)
SHORT_CODE = re.compile(r"(?i)\b(?:call|dial|sms)\b\D{0,6}(\b\d{4,5}\b)")
URL = re.compile(
    r"(?i)\b(?:(?:https?|hxxps?)://\S+|www\.\S+|[a-z0-9][a-z0-9-]*(?:\.|\[\.\])"
    r"(?:lk|com|net|org|info|xyz|top|link|site|online|app|me|co|example|biz|cc|ly)(?:/\S*)?)"
)

ACTION_WORDS = {
    "share_credential": {
        "terms": r"\b(otp|pin|password|cvv|card number|card details|expiry|verification code|"
                 r"one[- ]time|username|last four digits)\b|otp\s*eka|pin\s*eka|ඕටීපී|OTP\s*අංකය|මුරපදය",
        "verbs": r"\b(reply|send|share|provide|confirm|enter|submit|give|forward|tell|update|"
                 r"evanna|ewanna|yawanna|denna|kiyanna)\b|එවන්න|ලබා\s*දෙන්න|දෙන්න|කියන්න",
    },
    # Extract requested payments even in legitimate reminders; action is not a fraud label.
    "pay": r"\b(pay|transfer (?:money|funds|rs|lkr)|send money|processing fee|release fee|handling fee|fee of|charges? of|"
           r"pay .{0,25}\bto (?:release|unlock|activate|receive|claim|cancel)|"
           r"deposit .{0,25}\bto|send (?:rs\.?|lkr) ?[\d,]+)\b|gewanna|ගාස්තුව ගෙවන්න",
    "install": r"\b(install|download (?:the |our |an? )?app|anydesk|teamviewer|quicksupport)\b|\.apk\b|install\s*karanna",
    "call": r"\b(call|dial|contact|phone|ring)\b|call\s*karanna|katha\s*karanna|අමතන්න|ඇමතුමක්|කතා\s*කරන්න",
    "reply": r"\b(reply|respond|text back|sms .{0,10} to)\b|reply\s*karanna|පිළිතුරු",
    "click": r"\b(click|tap|visit|open|login|log in|verify (?:at|here|now)|update (?:at|here)|here:)\b|"
             r"link\s*eka|click\s*karanna|ක්ලික්",
}
NEGATION = re.compile(
    r"(?i)\b(do not|don't|dont|never|will never|no one|not share|do not share)\b|epa\b|නොදෙන්න|එපා|කිසිවෙකුට"
)

TACTICS = {
    "URGENCY": r"\b(immediately|urgent|urgently|now|asap|today|within \d+ ?(hours|hrs|minutes|mins)|"
               r"\d+ ?hours|expires?|last chance|wahama|ikmanin|dan ma)\b|වහාම|ඉක්මනින්|දැන්ම|පැය",
    "ACCOUNT_THREAT": r"\b(suspend\w*|block\w*|lock\w*|deactivat\w*|restrict\w*|clos\w* your|"
                      r"legal action|unauthori[sz]ed|unusual|suspicious activity|"
                      r"kyc|verification (?:is )?(?:incomplete|pending|required))\b|"
                      r"block\s*wenawa|අවහිර|අත්හිටුව",
    "REWARD_LURE": r"\b(won|winner|reward|cashback|prize|refund|congratulations|pre-?approved|"
                   r"approved|gift|bonus|free|earn)\b|dinum|ත්‍යාග|මුදල් ලැබ",
    "AUTHORITY": r"\b(security team|fraud desk|fraud team|officer|regulatory|central bank|cbsl|"
                 r"police|government|dispute team)\b",
    "FEE_REQUEST": r"\b(processing fee|release fee|fee of|pay .{0,15} to release|charges? of)\b",
}


@lru_cache(maxsize=1)
def _banks():
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    banks = []
    for bank in data.get("banks", []):
        names = [bank["name"].lower()] + [a.lower() for a in bank.get("aliases", [])]
        names += bank.get("aliases_si", [])
        banks.append((bank["id"], bank["name"], sorted(set(names), key=len, reverse=True)))
    return banks


def normalize_phone(raw):
    digits = re.sub(r"[^\dX]", "", raw.upper())
    if digits.startswith("0094"):
        digits = "0" + digits[4:]
    elif digits.startswith("94") and len(digits) == 11:
        digits = "0" + digits[2:]
    return digits


def normalize_url(raw):
    url = raw.replace("[.]", ".").replace("hxxp", "http").rstrip(".,);")
    url = re.sub(r"(?i)^https?://", "", url)
    domain = url.split("/")[0].lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _find_bank(text, sender=None):
    low = text.lower()
    for bank_id, name, names in _banks():
        for n in names:
            i = low.find(n.lower()) if n.isascii() else text.find(n)
            if i >= 0:
                return {"id": bank_id, "name": name, "via": "text"}, (i, i + len(n))
    m = re.search(r"\b([A-Z][A-Za-z&]+(?: [A-Z][A-Za-z&]+)? (?:Bank|BANK))\b", text)
    if m:
        return {"id": None, "name": m.group(1), "via": "text"}, m.span(1)
    for bank_id, name, names in _banks():
        if sender and sender.upper() in [s.upper() for s in _sender_ids(bank_id)]:
            return {"id": bank_id, "name": name, "via": "sender"}, None
    return None, None


@lru_cache(maxsize=64)
def _sender_ids(bank_id):
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    for bank in data.get("banks", []):
        if bank["id"] == bank_id:
            return tuple(bank.get("sender_ids", []))
    return ()


# These are interpretable baseline rules, not a trained or calibrated extractor.
# Clause boundaries keep a safety notice from suppressing a later scam request.
CLAUSES = re.compile(r".+?(?:[.!?;](?=\s|$)|\n|$)")
REPORTED = re.compile(r"(?i)\b(?:someone|a caller|they|he|she|the scammer)\s+(?:called|asked|told|requested)|\b(?:asked|told) me\b|\b(?:I|we) (?:received|reported)\b")


def action_evidence(text):
    evidence = []
    for sentence in CLAUSES.finditer(text):
        # Split contrast clauses while preserving offsets into normalized_text.
        for part in re.finditer(r".+?(?=,|\bbut\b|$)", sentence.group(), re.I):
            clause = part.group()
            start = sentence.start() + part.start()
            status = ("negated" if NEGATION.search(clause) else
                      "reported" if REPORTED.search(clause) else "requested")
            rule = ACTION_WORDS["share_credential"]
            candidates = []
            if re.search(rule["terms"], clause, re.I) and re.search(rule["verbs"], clause, re.I):
                candidates.append("share_credential")
            for action in ("pay", "install", "call", "reply", "click"):
                if re.search(ACTION_WORDS[action], clause, re.I):
                    if action == "call" and not (PHONE.search(clause) or SHORT_CODE.search(clause)):
                        continue
                    if action == "click" and not URL.search(clause):
                        continue
                    candidates.append(action)
            for action in candidates:
                evidence.append({"action": action, "status": status,
                                 "text": clause, "start": start, "end": start + len(clause),
                                 "method": "clause_rules_v1"})
    return evidence


def extract(text, sender=None):
    """Return the scam anatomy for one (already cleaned) message."""
    spans = []
    bank, bank_span = _find_bank(text, sender)
    if bank_span:
        spans.append({"type": "BANK", "text": text[bank_span[0]:bank_span[1]],
                      "start": bank_span[0], "end": bank_span[1]})

    contacts = []
    taken = []
    for m in URL.finditer(text):
        contacts.append({"type": "url", "value": m.group(0), "normalized": normalize_url(m.group(0))})
        spans.append({"type": "CONTACT", "text": m.group(0), "start": m.start(), "end": m.end()})
        taken.append(m.span())
    for m in PHONE.finditer(text):
        if any(a <= m.start() < b for a, b in taken):
            continue
        contacts.append({"type": "phone", "value": m.group(0), "normalized": normalize_phone(m.group(0))})
        spans.append({"type": "CONTACT", "text": m.group(0), "start": m.start(), "end": m.end()})
    for m in SHORT_CODE.finditer(text):
        contacts.append({"type": "short_code", "value": m.group(1), "normalized": m.group(1)})

    has_phone = any(c["type"] in ("phone", "short_code") for c in contacts)
    has_url = any(c["type"] == "url" for c in contacts)

    evidence = action_evidence(text)
    actions = list(dict.fromkeys(e["action"] for e in evidence if e["status"] == "requested"))
    for e in evidence:
        if e["status"] == "requested":
            spans.append({"type": "ACTION", "text": e["text"], "start": e["start"], "end": e["end"]})
    # A URL alone is a contact, not proof that the recipient was asked to open it.
    if not actions:
        actions = ["none"]
    primary = max(actions, key=lambda a: (HARM[a], -list(HARM).index(a)))
    uncertain = any(e["status"] == "reported" for e in evidence) or (has_url and actions == ["none"])

    tactics = []
    for name, pattern in TACTICS.items():
        m = re.search(pattern, text, re.I)
        if m:
            tactics.append(name)
            spans.append({"type": name, "text": m.group(0), "start": m.start(), "end": m.end()})
    if bank and "AUTHORITY" not in tactics:
        tactics.append("AUTHORITY")

    spans.sort(key=lambda s: s["start"])
    return {
        "claimed_bank": bank,
        "primary_action": primary,
        "harm": HARM[primary],
        "actions": actions,
        "action_evidence": evidence,
        "action_uncertainty": "uncertain" if uncertain else "rule_based",
        "action_method": "clause_rules_v1",
        "contacts": contacts,
        "tactics": tactics,
        "zero_link": not has_url,
        "spans": spans,
    }
