"""The reliance engine: learn how each user trusts the AI, then adapt the warning.

For each decision we store (no message text, no personal data):
  initial_choice  what the user thought BEFORE seeing the AI (study mode only)
  ai_advice       what the AI said: "scam" or "safe"
  final_choice    what the user decided AFTER seeing the AI
  truth           the real answer (known for study scenarios)

From these we measure (Schemmer et al., IUI 2023; Raees & Papangelis, 2026):
  over-reliance   user followed the AI when the AI was WRONG
  under-reliance  user ignored the AI when the AI was RIGHT
  RAIR            of the times the user was wrong and the AI right, how often they switched to the AI
  RSR             of the times the user was right and the AI wrong, how often they kept their own answer

Then we pick an intervention:
  standard         not enough decisions yet (fewer than MIN_DECISIONS)
  verify_first     user over-relies -> make them check the real number first (cognitive forcing)
  strong_evidence  user under-relies -> show every fact and its source
  light            reliance looks right -> short warning, to avoid warning fatigue
"""
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "runtime" / "reliance.db"
MIN_DECISIONS = 3
OVER_LIMIT = 0.34
UNDER_LIMIT = 0.34


def _connect(db_path=None):
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE IF NOT EXISTS decisions (
        user_id TEXT, message_id TEXT, session INTEGER, condition TEXT,
        initial_choice TEXT, ai_advice TEXT, final_choice TEXT, truth TEXT,
        action TEXT, intervention TEXT, seconds REAL, ts REAL)""")
    return con


def record(decision, db_path=None):
    fields = ["user_id", "message_id", "session", "condition", "initial_choice", "ai_advice",
              "final_choice", "truth", "action", "intervention", "seconds"]
    values = [decision.get(f) for f in fields] + [time.time()]
    with _connect(db_path) as con:
        con.execute(f"INSERT INTO decisions ({', '.join(fields)}, ts) VALUES ({', '.join('?' * len(values))})",
                    values)
    return profile(decision["user_id"], db_path)


def _rate(num, den):
    return round(num / den, 3) if den else None


def profile(user_id, db_path=None, condition=None, session=None):
    with _connect(db_path) as con:
        query = "SELECT initial_choice, ai_advice, final_choice, truth FROM decisions WHERE user_id = ? AND truth IN ('safe', 'scam') AND ai_advice IN ('safe', 'scam') AND initial_choice IN ('safe', 'scam')"
        args = [user_id]
        if condition is not None:
            query += " AND condition = ?"
            args.append(condition)
        if session is not None:
            query += " AND session = ?"
            args.append(session)
        rows = con.execute(query, args).fetchall()
    n = len(rows)
    ai_wrong = [r for r in rows if r[1] != r[3] and r[0] == r[3]]
    ai_right = [r for r in rows if r[1] == r[3] and r[0] != r[3]]
    over = sum(r[2] == r[1] for r in ai_wrong)        # followed a wrong AI
    under = sum(r[2] != r[1] for r in ai_right)       # ignored a right AI

    # Two-step measures (only rows with an initial choice that disagreed with the AI).
    two = [r for r in rows if r[0] and r[0] != r[1]]
    par = sum(r[0] != r[3] and r[1] == r[3] and r[2] == r[1] for r in two)   # positive AI reliance
    nsr = sum(r[0] != r[3] and r[1] == r[3] and r[2] == r[0] for r in two)   # negative self-reliance
    psr = sum(r[0] == r[3] and r[1] != r[3] and r[2] == r[0] for r in two)   # positive self-reliance
    nar = sum(r[0] == r[3] and r[1] != r[3] and r[2] == r[1] for r in two)   # negative AI reliance

    result = {
        "user_id": user_id, "decisions": n,
        "accuracy": _rate(sum(r[2] == r[3] for r in rows), n),
        "over_reliance": _rate(over, len(ai_wrong)),
        "under_reliance": _rate(under, len(ai_right)),
        "RAIR_opportunities": par + nsr,
        "RSR_opportunities": psr + nar,
        "RAIR": _rate(par, par + nsr),
        "RSR": _rate(psr, psr + nar),
    }
    result["intervention"] = choose_intervention(result)
    return result


def choose_intervention(p):
    if p["decisions"] < MIN_DECISIONS:
        return "standard"
    over, under = p.get("over_reliance"), p.get("under_reliance")
    if over is not None and over >= OVER_LIMIT:
        return "verify_first"
    if under is not None and under >= UNDER_LIMIT:
        return "strong_evidence"
    return "light" if p.get("RAIR") is not None and p.get("RSR") is not None else "standard"


def export_csv(path, db_path=None):
    """Write all decisions to a CSV for the statistics (R / Python)."""
    import csv
    with _connect(db_path) as con:
        cur = con.execute("SELECT * FROM decisions")
        cols = [d[0] for d in cur.description]
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(cur.fetchall())


def choose_warning(profile, risk, condition='evidence_aware'):
    """Experimental policies. Thresholds are provisional, not validated findings."""
    if condition == 'static':
        return 'standard'
    user_policy = profile['intervention'] if profile else 'standard'
    if condition == 'user_only':
        return user_policy
    if risk.get('abstain') or risk.get('evidence_quality') == 'insufficient':
        return 'uncertainty'
    if user_policy == 'verify_first':
        return 'verify_first'
    if risk.get('evidence_quality') in ('contradicted', 'conflicting'):
        return 'strong_evidence'
    return user_policy
