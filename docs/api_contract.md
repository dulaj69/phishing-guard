# API contract

The full data format is now in `shared/contract.md`, with real examples in `shared/examples/`.

| Endpoint | Owner | What it does |
|---|---|---|
| `POST /detect` | Sanmith | Text in, label + scam score + language + scam anatomy out |
| `POST /predict_batch` | Sanmith | Many texts at once (for LIME/SHAP) |
| `POST /verify` | Perera | Detection + fact checks + explanation + risk tier |
| `POST /analyze` | All | Full pipeline: detect, verify, then the warning |
| `GET /scenarios` | Rathnayake | Study messages (answers hidden) |
| `POST /decision` | Rathnayake | Log one participant decision, returns their reliance profile |
| `GET /profile/{user_id}` | Rathnayake | Reliance profile (over/under-reliance, RAIR, RSR, intervention) |

Try them all at http://127.0.0.1:8000/docs while the server runs.

## Study/research upgrade (2026-10-18)

`POST /analyze` adds `study_mode` (default false), `initial_choice` (safe/scam), `condition` (static/user_only/evidence_aware; default evidence_aware), and `session` (positive integer; default 1). Study mode requires user_id, scenario_id, initial_choice, and the exact server scenario text and sender. Demo requests never activate planted errors. No study trial is created in demo mode.

A study response contains an opaque `analysis_id`. Send it with user_id, final_choice, action and seconds to `/decision`; legacy message_id and ai_advice remain required for compatibility but are not trusted for attribution. The server takes truth, initial choice, advice, intervention, condition and session from its trial record. Client `truth` cannot override it. Duplicate, expired (>2 hours) or wrong-user tokens return 409; missing analysis_id returns 422. Trials and decisions are recorded atomically without SMS text. This is a local research prototype, not an authenticated multi-user service.

`ai_advice` now also supports `uncertain`; check `verification.risk.abstain` before using its tier. Abstention is not a fourth ground-truth label. UI action buttons simulate decisions and do not place calls or open links. Export still uses `warn.reliance.export_csv`.
