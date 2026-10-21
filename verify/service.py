"""Run the whole verify step on one detection result."""
from verify import explain, fact_check, risk


def verify(detection, sender=None, explain_method="occlusion"):
    anatomy = detection["anatomy"]
    checks = fact_check.check(anatomy, sender)
    return {
        "fact_checks": checks,
        "explanation": explain.explain(detection["normalized_text"], explain_method),
        "risk": risk.assess(detection["scam_score"], anatomy["primary_action"], checks, anatomy.get("action_uncertainty", "rule_based")),
        "official_contact": fact_check.official_contact(anatomy),
    }
