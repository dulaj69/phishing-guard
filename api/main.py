"""The team API: one server for all three parts, plus the study web app.

Run from the project root:
    uvicorn api.main:app --reload
Then open:
    http://127.0.0.1:8000/        -> the SMS inbox app (Rathnayake's part)
    http://127.0.0.1:8000/docs    -> try every API endpoint in the browser

PRIVACY: never print or log message text.
"""
import json
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from api import pipeline
from detection.config import MODEL_VERSION
from detection.model import detect
from verify.service import verify as run_verify
from warn import reliance, study
from research.lab.api import router as research_router

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "warn" / "data" / "scenarios.json"
STATIC = ROOT / "warn" / "static"

app = FastAPI(title="J26-IT-442 Verify-then-Warn API", version=MODEL_VERSION)
app.include_router(research_router)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Message(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    sender: Optional[str] = Field(None, max_length=40)


class MessageBatch(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=500)


class AnalyzeRequest(Message):
    language: Optional[Literal["en", "si", "singlish"]] = None
    user_id: Optional[str] = Field(None, max_length=64)
    scenario_id: Optional[str] = None
    explain_method: Literal["occlusion", "lime"] = "occlusion"
    study_mode: bool = False
    initial_choice: Optional[Literal["scam", "safe"]] = None
    condition: Literal["static", "user_only", "evidence_aware"] = "evidence_aware"
    session: int = Field(1, ge=1)



class Decision(BaseModel):
    user_id: str = Field(..., max_length=64)
    message_id: str
    analysis_id: Optional[str] = None
    ai_advice: Literal["scam", "safe", "uncertain"]
    final_choice: Literal["scam", "safe"]
    truth: Optional[Literal["scam", "safe"]] = None
    initial_choice: Optional[Literal["scam", "safe"]] = None
    action: Optional[str] = None
    intervention: Optional[str] = None
    session: Optional[int] = None
    condition: Optional[str] = None
    seconds: Optional[float] = Field(None, ge=0, allow_inf_nan=False)


def _scenarios():
    return json.loads(SCENARIOS.read_text(encoding="utf-8"))["scenarios"]


def _guard(fn):
    try:
        return fn()
    except FileNotFoundError:
        raise HTTPException(503, "Model not trained yet. Run: python -m detection.train")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"model_version": MODEL_VERSION}


# ---------- Part 1: detection (Sanmith) ----------
@app.post("/detect")
def detect_one(message: Message):
    return _guard(lambda: detect([message.text], [message.sender])[0])


@app.post("/predict_batch")
def predict_batch(batch: MessageBatch):
    """Many messages at once. LIME/SHAP call this with many changed versions of one message."""
    return _guard(lambda: {"results": detect(batch.texts)})


# ---------- Part 2: verify (Perera) ----------
@app.post("/verify")
def verify_one(message: Message):
    def run():
        detection = detect([message.text], [message.sender])[0]
        return {"detection": detection, "verification": run_verify(detection, message.sender)}
    return _guard(run)


# ---------- Full pipeline + Part 3: warn (Rathnayake) ----------
@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    scenario = None
    if req.study_mode:
        scenario = next((s for s in _scenarios() if s["id"] == req.scenario_id), None)
        if not scenario or not req.user_id or req.initial_choice is None:
            raise HTTPException(422, "Study mode requires a scenario, participant ID and initial decision.")
        if req.text != scenario["text"] or req.sender != scenario.get("sender"):
            raise HTTPException(422, "Study text and sender must match the fixed scenario.")
    result = _guard(lambda: pipeline.analyze(req.text, req.sender, req.language,
                    req.user_id if req.study_mode else None,
                    bool(scenario and scenario.get("planted_error")), req.explain_method,
                    req.condition, req.session, scenario["truth"] if scenario else None))
    if scenario:
        result["analysis_id"] = study.create(req.user_id, scenario, req.initial_choice,
                                             result, req.condition, req.session)
    return result


@app.get("/scenarios")
def scenarios():
    # Hide the answers from the browser.
    return [{k: v for k, v in s.items() if k not in ("truth", "planted_error")} for s in _scenarios()]


@app.post("/decision")
def decision(d: Decision):
    if not d.analysis_id:
        raise HTTPException(422, "A server-issued study analysis_id is required; demo feedback is not labelled research data.")
    try:
        return study.record(d.analysis_id, d.user_id, d.final_choice, d.action, d.seconds)
    except ValueError as error:
        raise HTTPException(409, str(error))


@app.get("/profile/{user_id}")
def profile(user_id: str):
    return reliance.profile(user_id)


# ---------- Web app ----------
app.mount("/app", StaticFiles(directory=STATIC, html=True), name="app")


@app.get("/")
def home():
    return RedirectResponse("/app/")
