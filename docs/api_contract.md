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

## Research workbench endpoints

The `/research` router serves fixed diagnostic fixtures and controlled simulations separately from `/analyze`.

- `GET /research/catalog`: case list, contribution descriptions, current loaded-model fingerprint.
- `POST /research/robustness`: `case_id`; returns fixed variants, raw/normalised scores and action evidence.
- `POST /research/benchmark`: all 18 authored diagnostics, denominators and limitations.
- `POST /research/evidence`: scenario (callback/credential/link), score [0,1], and booleans contradiction/copied_domain/stale/missing/uncertainty. All supplied evidence is explicitly fictional. No global bank registry is mutated.
- `POST /research/warning-preview`: case_id and persona (new/over_reliant/under_reliant/balanced); no participant records created.
- `POST /research/pilot/sessions`: mode (rehearsal/pilot) and consent. Pilot requires consent=true; condition assigned by server.
- `GET /research/pilot/{token}`: active item and progress; truth/plant flags omitted.
- `POST /research/pilot/{token}/initial`: index [0,8], choice (safe/scam), confidence [0,100]. Initial answers lock before advice; identical retry returns the stored warning.
- `POST /research/pilot/{token}/final`: initial fields plus action (independent_check/follow_sms/ignore_report) and comprehension answer index [0,2], required for advice trials. Completion is atomic; duplicate/out-of-order submissions fail.
- `GET /research/pilot/{token}/report`: session-only summary. Transfer answers and correctness are hidden until all trials finish. Missing denominators remain null.

No message text is written to the new pilot tables; fixtures are referenced by ID. Rehearsal and consented-pilot modes remain labelled separately in session reports. These endpoints are intended for local research use, not an authenticated internet-facing deployment.
