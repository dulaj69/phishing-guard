"""Provisional harm matrix with evidence-aware abstention.

Matches never authenticate an SMS. Explicit contradictions raise risk. Thresholds
must be validated against held-out expert judgements before deployment.
"""

TIERS = ["Low", "Medium", "High", "Critical"]
LIKELIHOOD_THRESHOLDS = {"High": 0.75, "Medium": 0.40}

HARM_LEVEL = {"share_credential": 3, "pay": 3, "install": 3, "call": 2, "reply": 2,
              "click": 1, "none": 0}
HARM_WORDS = {
    "share_credential": "asks for your OTP, PIN or card details",
    "pay": "asks you to pay money",
    "install": "asks you to install an app",
    "call": "asks you to call a number",
    "reply": "asks you to reply",
    "click": "asks you to open a link",
    "none": "does not ask you to do anything",
}

#            harm:   0         1         2         3
MATRIX = {
    "Low":    ["Low",    "Low",    "Low",    "Medium"],
    "Medium": ["Low",    "Medium", "Medium", "High"],
    "High":   ["Medium", "High",   "High",   "Critical"],
}


def likelihood(score):
    if score >= LIKELIHOOD_THRESHOLDS["High"]:
        return "High"
    if score >= LIKELIHOOD_THRESHOLDS["Medium"]:
        return "Medium"
    return "Low"


def _move(tier, step):
    i = max(0, min(len(TIERS) - 1, TIERS.index(tier) + step))
    return TIERS[i]


def assess(scam_score, primary_action, fact_checks, action_uncertainty="rule_based"):
    like = likelihood(scam_score)
    harm = HARM_LEVEL.get(primary_action, 0)
    matrix_tier = MATRIX[like][harm]
    results = [c["result"] for c in fact_checks if c["check"] != "bank_known"]
    failed = "fail" in results
    # Published details are copyable; matches must never lower the risk tier.
    adjustment, tier = ("up", _move(matrix_tier, 1)) if failed else ("none", matrix_tier)
    if primary_action == "share_credential" and TIERS.index(tier) < TIERS.index("High"):
        tier, adjustment = "High", "up"
    evidence = ("conflicting" if failed and "pass" in results else "contradicted" if failed else
                "supported" if "pass" in results else "insufficient")
    # Supporting a copied domain does not resolve a request to call a different
    # number. Evidence must address the extracted action to resolve a middle score.
    relevant_check = {"call": "official_number", "click": "official_domain",
                      "share_credential": "bank_rule", "pay": "bank_rule",
                      "install": "bank_rule", "reply": "bank_rule"}.get(primary_action)
    relevant_support = any(c["check"] == relevant_check and c["result"] == "pass" for c in fact_checks)
    abstain = (not failed and primary_action != "share_credential" and
               ((like == "Medium" and not relevant_support) or action_uncertainty == "uncertain"))
    reasons = [f"Model score {scam_score:.2f}; not a calibrated probability of fraud.",
               f"The message {HARM_WORDS.get(primary_action, 'has an uncertain action')}."]
    reasons += [c["detail"] for c in fact_checks]
    if abstain:
        reasons.append("Insufficient evidence for a firm verdict; verify independently.")
    return {"tier": tier, "likelihood": like, "harm": harm, "matrix_tier": matrix_tier,
            "adjustment": adjustment, "reasons": reasons, "abstain": abstain,
            "decision": "abstain" if abstain else "assessed", "evidence_quality": evidence,
            "action_uncertainty": action_uncertainty, "action_relevant_support": relevant_support,
            "policy_version": "evidence_v2_action_relevance", "score_semantics": "uncalibrated_weighted_score"}
