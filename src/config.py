"""Shared settings. Change values here, not all over the code."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_CSV = ROOT / "data" / "seed" / "banking_smishing_seed_v1.csv"
MODEL_PATH = ROOT / "models" / "baseline.joblib"
MODEL_VERSION = "baseline-tfidf-lr-0.1"
LABELS = ["legit", "suspicious", "phishing"]
