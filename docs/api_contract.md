# API contract (all three members use this)

Base address while developing: `http://127.0.0.1:8000`

## POST /predict
Send one message, get one result.

Request:
```json
{ "text": "Your account will be blocked. Call 07XXXXXXXX now." }
```

Response:
```json
{
  "label": "phishing",
  "probabilities": { "legit": 0.05, "suspicious": 0.15, "phishing": 0.80 },
  "model_version": "baseline-tfidf-lr-0.1",
  "latency_ms": 3.2
}
```

## POST /predict_batch
Send many messages (needed by LIME / SHAP).

Request: `{ "texts": ["message 1", "message 2"] }`
Response: `{ "results": [ {...}, {...} ] }` (same fields as /predict)

## GET /health  ->  `{ "status": "ok" }`
## GET /version ->  `{ "model_version": "..." }`

## Rules
- We may ADD new fields later (for example `language`, `tactics`). We never remove or rename a field without telling everyone.
- The API never stores or logs message text.
- Labels are always exactly: `legit`, `suspicious`, `phishing`.

## Planned fields (not built yet)
- `language`: en / si / singlish
- `tactics`: list of cue tags such as `URGENCY`, `CREDENTIAL_REQUEST`
