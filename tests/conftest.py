import pytest

from detection import model
from detection.train import train


@pytest.fixture(scope="session", autouse=True)
def trained_model(tmp_path_factory):
    """Train a fresh model once for all tests (takes a few seconds)."""
    path = tmp_path_factory.mktemp("models") / "detector.joblib"
    train(model_path=path, show_report=False)
    model.load_model(path)
    return path


@pytest.fixture(autouse=True)
def temp_reliance_db(tmp_path, monkeypatch):
    from warn import reliance
    monkeypatch.setattr(reliance, "DB_PATH", tmp_path / "reliance.db")
