from src import predict
from src.train_baseline import train


def test_predict_returns_valid_result(tmp_path):
    model_file = tmp_path / "model.joblib"
    train(model_path=model_file, show_report=False)
    predict.load_model(model_file)

    result = predict.predict_texts(["Your account is blocked. Call 07XXXXXXXX now."])[0]

    assert result["label"] in {"legit", "suspicious", "phishing"}
    assert abs(sum(result["probabilities"].values()) - 1.0) < 0.01
    assert "model_version" in result
