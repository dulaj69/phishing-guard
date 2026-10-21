"""Join the three parts:  SMS -> detect (Sanmith) -> verify (Perera) -> warn (Rathnayake)."""
import copy

from detection.model import detect
from verify.service import verify
from warn import reliance
from warn.composer import compose

FLIP = {"Critical": "Low", "High": "Low", "Medium": "Low", "Low": "High"}


def ai_advice(tier):
    return "scam" if tier in ("Medium", "High", "Critical") else "safe"


def analyze(text, sender=None, language=None, user_id=None, planted_error=False,
            explain_method="occlusion", condition="evidence_aware", session=None, study_truth=None):
    detection = detect([text], [sender])[0]
    verification = verify(detection, sender, explain_method)

    if planted_error:
        # STUDY ONLY: the AI gives the wrong advice on purpose. Recorded so
        # the analysis knows the AI was wrong. Never used outside the study app.
        verification = copy.deepcopy(verification)
        verification["risk"]["tier"] = ("Low" if study_truth == "scam" else "High" if study_truth == "safe" else FLIP[verification["risk"]["tier"]])
        verification["risk"]["planted_error"] = True
        verification["risk"]["abstain"] = False
        verification["risk"]["decision"] = "assessed"

    profile = reliance.profile(user_id, condition=condition, session=session) if user_id else None
    intervention = reliance.choose_warning(profile, verification["risk"], condition)
    warning = compose(detection, verification, language, intervention, seed=text)

    return {
        "detection": detection,
        "verification": verification,
        "warning": warning,
        "ai_advice": "uncertain" if verification["risk"].get("abstain") else ai_advice(verification["risk"]["tier"]),
        "condition": condition,
        "profile": profile,
    }
