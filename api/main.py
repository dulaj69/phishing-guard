"""Stub detection API. Run from the project root:
    uvicorn api.main:app --reload
Then open http://127.0.0.1:8000/docs to try it in the browser.

PRIVACY: never print or log the message text.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import MODEL_VERSION
from src.predict import predict_texts

app = FastAPI(title="Banking Smishing Detector (stub)", version=MODEL_VERSION)

# Lets the web page (a different port) call this API during development.
# Before any real deployment, replace "*" with the real website address.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class MessageBatch(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=200)


def _predict(texts):
    try:
        return predict_texts(texts)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Model file not found. Run: python -m src.train_baseline",
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"model_version": MODEL_VERSION}


@app.post("/predict")
def predict(message: Message):
    return _predict([message.text])[0]


@app.post("/predict_batch")
def predict_batch(batch: MessageBatch):
    # Batch endpoint is needed by LIME/SHAP, which send many variations of one message.
    return {"results": _predict(batch.texts)}
