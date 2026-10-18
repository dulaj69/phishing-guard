"""Build the warning the user sees.

Every sentence comes from a fact check, the requested action, or a detected
trick. Nothing is made up, so each line has a 'source' that says where it came
from. This is the 'fact-grounded' rule from the research plan.
"""
import random

from warn import phrases as P

SHOW_FROM = {"Medium", "High", "Critical"}


def pick_language(detected, wanted=None):
    if wanted in ("en", "si", "singlish"):
        return wanted
    return {"si": "si", "mixed": "si", "singlish": "singlish"}.get(detected, "en")


def _bank_name(detection, verification):
    contact = verification.get("official_contact")
    if contact:
        return contact["bank"]
    bank = detection["anatomy"].get("claimed_bank")
    return bank["name"] if bank else "the bank"


def compose(detection, verification, language=None, intervention="standard", seed=None):
    lang = pick_language(detection["language"], language)
    risk = verification["risk"]
    tier = risk["tier"]
    anatomy = detection["anatomy"]
    bank = _bank_name(detection, verification)
    contact = verification.get("official_contact")

    lines = []
    # 1. Failed fact checks are the strongest evidence, so they go first.
    for c in verification["fact_checks"]:
        if c["result"] == "fail" and c["check"] in P.CHECK_FAIL:
            text = c["detail"] if lang == "en" else P.CHECK_FAIL[c["check"]][lang].format(value=c.get("value", ""), bank=bank)
            lines.append({"text": text, "source": f"fact_check:{c['check']}",
                          "evidence": c.get("source")})
    # 2. What it asks you to do.
    action = anatomy["primary_action"]
    if action in P.ACTION:
        lines.append({"text": P.ACTION[action][lang], "source": f"anatomy:{action}"})
    # 3. Pressure tricks.
    for tactic in anatomy["tactics"]:
        if tactic in P.TACTIC:
            lines.append({"text": P.TACTIC[tactic][lang], "source": f"tactic:{tactic}"})

    uncertain = risk.get("abstain", False)
    show = tier in SHOW_FROM or uncertain or intervention == "uncertainty"
    if uncertain or intervention == "uncertainty":
        lines.insert(0, {"text": P.UNCERTAINTY[lang], "source": "risk:evidence_quality"})
    if intervention == "light":
        lines = lines[:1]
    elif intervention != "strong_evidence":
        lines = lines[:3]

    safe_action = None
    if contact and show:
        safe_action = {"type": "call_official", "number": contact["number"],
                       "text": P.SAFE_ACTION[lang].format(bank=bank, number=contact["number"]),
                       "source": contact["source"]}

    verify_question = None
    scam_numbers = [c["normalized"] for c in anatomy["contacts"] if c["type"] == "phone"]
    if intervention == "verify_first" and show and contact and scam_numbers and contact["number"] != scam_numbers[0]:
        options = [contact["number"], scam_numbers[0]]
        random.Random(seed).shuffle(options)
        verify_question = {"text": P.VERIFY_FIRST[lang].format(bank=bank),
                           "options": options, "answer": contact["number"]}

    lesson_key = action if action in P.LESSON else next(
        (t for t in anatomy["tactics"] if t in P.LESSON), None)

    return {
        "show": show,
        "demo_evidence": any((c.get("source") or {}).get("fictional") for c in verification["fact_checks"]),
        "level": tier,
        "language": lang,
        "title": P.UNCERTAIN_TITLE[lang] if uncertain else P.TITLE[tier][lang],
        "abstain": uncertain,
        "evidence_quality": risk.get("evidence_quality", "insufficient"),
        "verification_prompt": P.INDEPENDENT_CHECK[lang] if intervention == "verify_first" else None,
        "lines": lines,
        "advice": P.ADVICE[lang] if show else None,
        "intervention": intervention,
        "safe_action": safe_action,
        "verify_question": verify_question,
        "show_sources": intervention == "strong_evidence",
        "lesson": P.LESSON[lesson_key][lang] if (show and lesson_key) else None,
        "highlights": [s for s in anatomy["spans"] if s["type"] in ("CONTACT", "ACTION", "URGENCY", "ACCOUNT_THREAT")],
        "needs_language_review": P.NEEDS_REVIEW[lang],
    }
