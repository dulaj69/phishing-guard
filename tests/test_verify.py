from verify import fact_check, risk


def anatomy(**kw):
    base = {"claimed_bank": {"id": "orion", "name": "Orion Bank"}, "primary_action": "none",
            "contacts": [], "tactics": []}
    base.update(kw)
    return base


def phone(n):
    return {"type": "phone", "value": n, "normalized": n}


def test_unofficial_number_fails_and_official_passes():
    fail = fact_check.check(anatomy(primary_action="call", contacts=[phone("0771234567")]))
    ok = fact_check.check(anatomy(primary_action="call", contacts=[phone("0112000100")]))
    assert fail[0]["result"] == "unknown" and fail[0]["source"]["url"]
    assert ok[0]["result"] == "pass"


def test_lookalike_domain_fails():
    url = {"type": "url", "value": "orion-verify[.]example", "normalized": "orion-verify.example"}
    c = fact_check.check(anatomy(primary_action="click", contacts=[url]))
    assert c[0]["result"] == "unknown" and "absence alone" in c[0]["detail"]


def test_otp_request_breaks_bank_rule():
    c = fact_check.check(anatomy(primary_action="share_credential", action_evidence=[{"action": "share_credential", "status": "requested", "text": "send OTP"}]))
    assert c[0]["check"] == "bank_rule" and c[0]["result"] == "fail"


def test_unknown_bank_gives_unknown():
    c = fact_check.check(anatomy(claimed_bank={"id": None, "name": "Fake Bank"}, contacts=[phone("0771234567")]))
    assert {x["result"] for x in c} == {"unknown"}


def test_risk_matrix_and_adjustment():
    # High likelihood x call (harm 2) = High; a failed check moves it to Critical.
    assert risk.assess(0.92, "call", [{"check": "official_number", "result": "fail", "detail": "x"}])["tier"] == "Critical"
    # Low likelihood x nothing asked = Low; passing checks keep it at Low (the floor).
    assert risk.assess(0.05, "none", [{"check": "sender_id", "result": "pass", "detail": "x"}])["tier"] == "Low"
    # Matching a domain does not authenticate the SMS or lower risk.
    r = risk.assess(0.5, "click", [{"check": "official_domain", "result": "pass", "detail": "x"}])
    assert (r["matrix_tier"], r["adjustment"], r["tier"]) == ("Medium", "none", "Medium")
    # No checks possible -> no adjustment.
    assert risk.assess(0.8, "share_credential", [])["tier"] == "Critical"


def test_likelihood_threshold_boundaries_and_action_harm_matrix():
    cases = [
        (0.3999, "Low", ["Low", "Low", "Low", "Medium"], ["Low", "Low", "Low", "High"]),
        (0.40, "Medium", ["Low", "Medium", "Medium", "High"], ["Low", "Medium", "Medium", "High"]),
        (0.7499, "Medium", ["Low", "Medium", "Medium", "High"], ["Low", "Medium", "Medium", "High"]),
        (0.75, "High", ["Medium", "High", "High", "Critical"], ["Medium", "High", "High", "Critical"]),
    ]
    actions = ["none", "click", "call", "share_credential"]

    for score, expected_likelihood, expected_matrix, expected_final in cases:
        for action, matrix_tier, final_tier in zip(actions, expected_matrix, expected_final):
            result = risk.assess(score, action, [])
            assert result["likelihood"] == expected_likelihood
            assert result["matrix_tier"] == matrix_tier
            assert result["tier"] == final_tier


def test_otp_scam_is_never_low():
    for score in (0.4, 0.6, 0.9):
        checks = fact_check.check(anatomy(primary_action="share_credential"))
        assert risk.assess(score, "share_credential", checks)["tier"] in ("High", "Critical")
