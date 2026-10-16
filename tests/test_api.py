from fastapi.testclient import TestClient

from api.main import app
from src import predict
from src.train_baseline import train


def _client(tmp_path):
    model_file = tmp_path / "model.joblib"
    train(model_path=model_file, show_report=False)
    predict.load_model(model_file)
    return TestClient(app)


def test_health(tmp_path):
    assert _client(tmp_path).get("/health").json() == {"status": "ok"}


def test_predict(tmp_path):
    client = _client(tmp_path)
    response = client.post("/predict", json={"text": "Verify your account now"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"label", "probabilities", "model_version", "latency_ms"}


def test_predict_batch(tmp_path):
    client = _client(tmp_path)
    response = client.post("/predict_batch", json={"texts": ["hello", "Your OTP is 123456"]})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 2


def test_empty_text_rejected(tmp_path):
    client = _client(tmp_path)
    assert client.post("/predict", json={"text": ""}).status_code == 422
