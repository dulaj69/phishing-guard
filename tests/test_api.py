import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

client = TestClient(app)
SCAM = "Orion Bank: obage account eka block wenawa. Wahama 0771234567 ta call karanna."


@pytest.fixture(autouse=True)
def signed_in(temp_reliance_db):
    client.cookies.clear()
    client.headers.update({'X-Research-Request':'1'})
    result=client.post('/account/signup',json={'username':'test_researcher','password':'a long test passphrase'})
    assert result.status_code==201


def test_health_and_app_page():
    assert client.get("/health").json() == {"status": "ok"}
    assert "Verify-then-Warn" in client.get("/app/").text


def test_detect_contract():
    body = client.post("/detect", json={"text": SCAM}).json()
    assert {"label", "probabilities", "scam_score", "language", "anatomy", "model_version"} <= set(body)


def test_analyze_end_to_end():
    body = client.post("/analyze", json={"text": SCAM}).json()
    assert body["verification"]["risk"]["tier"] == "High"
    assert body["warning"]["show"] and body["warning"]["language"] == "singlish"
    assert body["warning"]["safe_action"] is None  # fictional numbers cannot be safe alternatives


def test_scenarios_hide_answers_and_decision_is_logged():
    scenarios = client.get("/scenarios").json()
    assert scenarios and "truth" not in scenarios[0]
    scenario = scenarios[0]
    analyzed = client.post("/analyze", json={"text": scenario["text"], "sender": scenario["sender"],
        "user_id": "P01", "scenario_id": scenario["id"], "study_mode": True, "initial_choice": "safe"}).json()
    p = client.post("/decision", json={"user_id": "P01", "message_id": "s01", "ai_advice": "scam",
        "final_choice": "scam", "analysis_id": analyzed["analysis_id"]}).json()
    assert p["decisions"] == 1



def test_batch_and_validation():
    assert len(client.post("/predict_batch", json={"texts": ["hi", SCAM]}).json()["results"]) == 2
    assert client.post("/detect", json={"text": ""}).status_code == 422


def test_client_truth_cannot_create_research_record():
    r = client.post('/decision', json={'user_id': 'P', 'message_id': 's01', 'ai_advice': 'safe',
                                      'truth': 'safe', 'final_choice': 'safe'})
    assert r.status_code == 422


def test_trial_is_single_use_and_uses_server_truth():
    s = client.get('/scenarios').json()[0]
    request = {'text': s['text'], 'sender': s['sender'], 'scenario_id': s['id'],
               'study_mode': True, 'user_id': 'P', 'initial_choice': 'safe'}
    result = client.post('/analyze', json=request).json()
    decision = {'user_id': 'P', 'message_id': 'forged', 'ai_advice': 'safe', 'truth': 'safe',
                'final_choice': 'scam', 'analysis_id': result['analysis_id']}
    response = client.post('/decision', json=decision)
    assert response.status_code == 200 and response.json()['accuracy'] == 1
    assert client.post('/decision', json=decision).status_code == 409
    request['text'] = 'different message'
    assert client.post('/analyze', json=request).status_code == 422


def test_planted_errors_are_study_only_and_opposite_truth():
    s = next(s for s in client.get('/scenarios').json() if s['id'] == 's09')
    req = {'text': s['text'], 'sender': s['sender'], 'scenario_id': s['id']}
    demo = client.post('/analyze', json=req).json()
    assert not demo['verification']['risk'].get('planted_error')
    req.update(study_mode=True, user_id='P', initial_choice='scam')
    study = client.post('/analyze', json=req).json()
    assert study['verification']['risk']['planted_error'] and study['ai_advice'] == 'safe'
