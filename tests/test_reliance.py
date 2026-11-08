from warn import reliance


def log(user, i, ai, final, truth, initial=None):
    return reliance.record({"user_id": user, "message_id": f"m{i}", "ai_advice": ai,
                            "final_choice": final, "truth": truth, "initial_choice": initial})


def test_new_user_gets_standard():
    assert reliance.profile("new")["intervention"] == "standard"


def test_over_reliant_user_gets_verify_first():
    log("u1", 1, "scam", "scam", "scam", initial="safe")
    log("u1", 2, "safe", "safe", "scam", initial="scam")   # followed a WRONG AI
    p = log("u1", 3, "safe", "safe", "safe", initial="safe")
    assert p["over_reliance"] == 1.0 and p["intervention"] == "verify_first"


def test_under_reliant_user_gets_strong_evidence():
    log("u2", 1, "scam", "safe", "scam", initial="safe")   # ignored a RIGHT AI
    log("u2", 2, "scam", "safe", "scam", initial="safe")
    p = log("u2", 3, "safe", "safe", "safe", initial="safe")
    assert p["under_reliance"] == 1.0 and p["intervention"] == "strong_evidence"


def test_good_reliance_gets_light_and_rair_rsr():
    log("u3", 1, "scam", "scam", "scam", initial="safe")   # wrong at first, switched to right AI
    log("u3", 2, "scam", "safe", "safe", initial="safe")   # AI wrong, kept own right answer
    p = log("u3", 3, "safe", "safe", "safe", initial="safe")
    assert p["RAIR"] == 1.0 and p["RSR"] == 1.0 and p["intervention"] == "light"
