"""Settings for the detection part. Change values here, not all over the code."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_CSV = ROOT / "data" / "seed" / "banking_smishing_seed_v1.csv"
SYNTH_CSV = ROOT / "data" / "synthetic" / "synthetic_v1.csv"
# Public datasets, built by detection.public_data. Git ignores it (licences).
PUBLIC_CSV = ROOT / "data" / "processed" / "public_v1.csv"
# Languages our own project is actually about. Everything else is extra training signal.
LOCAL_LANGUAGES = ["en", "si", "singlish"]
MODEL_PATH = ROOT / "models" / "detector.joblib"
MODEL_VERSION = "tfidf-lr-0.3"
REGISTRY_PATH = ROOT / "verify" / "data" / "bank_registry.json"
LABELS = ["legit", "suspicious", "phishing"]
