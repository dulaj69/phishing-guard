# Individual accounts and learning lab

Implemented 19 October 2026. This extends the original technical viva guide (commit `7a99ea3`). Organisation accounts, join codes, email invitations and group reporting are not implemented; the selected scope is individual accounts.

## Start and use

Run `python -m uvicorn api.main:app --host 127.0.0.1 --port 8765` in the project environment. Open `/app/` for the anonymous SMS checker or `/app/workspace/` to create a pseudonymous individual account. Use a username and a passphrase of 15–128 characters. The local build has no email recovery.

Each workspace links clearly to Sanmith's action lab, Perera's evidence lab, and Rathnayake's human learning lab. Existing warning/reliance experiments remain under `/app/lab/#warnings`. Public SMS checks show the full detection, evidence, explanation, risk and warning report, expanded without member names, and do not become participant records. Every returned field is available in the complete-output section and export. The protected `/app/lab/message.html` page uses the same renderer.

## Rathnayake's extension

The existing component composes warnings and measures appropriate reliance on advice. The extension asks a different question: does a short lesson improve later decisions when advice is absent?

1. **Baseline:** three fictional English scenarios. Record judgement, the main reason, and confidence in the judgement. No model advice is supplied.
2. **Lesson selection:** server assigns adaptive or static condition at session creation. Adaptive selection prioritises a concept using `harm weight × (incorrect judgement + incorrect reason) × (1 + confidence/100)`. Credentials have weight 3; borrowed identity and uncertainty each have weight 2. Ties use a fixed concept order. The static condition always uses the credential lesson. These weights are provisional design choices.
3. **Immediate transfer:** three different scenarios without advice or a visible lesson. Correctness, reason correctness and confidence error are computed separately.
4. **Delayed transfer:** three further scenarios open 24 hours after immediate transfer. The server checks time; there is no browser override or public skip-wait endpoint.
5. **Private report:** observations, lesson priorities, condition, denominators and interpretation limits. JSON export contains this account's report. History resumes interrupted sessions.

Reasons are displayed in a stable, session-specific shuffled order. Stored indices refer to canonical authored reasons. Answers are locked after submission. Reports withhold block correctness until the three-question block is complete; the original text's ground truth and answer key are never sent with an active trial. Lesson acknowledgement does not prove engagement.

A worked selection: if the callback judgement and reason are wrong at 100% confidence, its priority is `2 × (1+1) × (1+1) = 8`. If both other concepts are answered correctly their priority is zero; adaptive teaching selects “Verify the requested route.” Static teaching still selects “Protect the secret.”

Confidence error is the mean of `(confidence/100 − judgement_correctness)²`. It is a descriptive Brier-style score for confidence in correctness; with three questions it is not a reliable calibration estimate. Immediate accuracy change is also descriptive, not a causal learning effect.

## Research validity boundary

This is an executable research instrument, not evidence of effectiveness. Only nine authored English questions exist, one per concept in each phase. The blocks are not psychometrically matched and have different safe/risky balances. Reasoning choices can provide cues. Fixed scenarios, repeated exposure, selection effects and small denominators prevent generalised learning claims. No native-language validation, participant recruitment, powered analysis or measured retention results are claimed.

For a defensible study, obtain protocol approval, develop and independently review a larger multilingual bank, balance class and difficulty across alternate forms, pre-register outcomes and exclusion rules, assign conditions at participant level, and measure delayed return/dropout. Use first attempts for the primary between-person analysis. Personal practice can retain repeat sessions, but repeats are not new independent participants. UI QA sessions are fictional engineering checks and must never be reported as research participants.

The older three-condition warning pilot and this two-condition teaching experiment are distinct instruments. Do not pool their scores or claim the new teaching experiment measures RAIR/RSR: it supplies no AI advice. RAIR/RSR remain in the existing advice pilot.

## Account implementation

FastAPI endpoints in `api/accounts.py`; SQLite tables alongside the existing runtime study database. Passwords use PBKDF2-HMAC-SHA256, 600,000 iterations and an independently random 16-byte salt. This explicit profile was chosen because the current macOS Python lacks `hashlib.scrypt`; it is not a silent fallback. The hash profile is fixed for this initial schema and must be versioned before future migration. Never store plaintext passwords.

Opaque random browser session tokens have a 12-hour absolute expiry; only their SHA-256 hashes are stored. Cookies are HttpOnly and SameSite Strict. Logout revokes the current session. Unsafe account/research calls require a custom same-origin header and reject mismatched Origin or cross-site Fetch Metadata. Wildcard CORS was removed. SQLite-backed rate limits apply per source IP and username. Protected pages and responses use no-store caching. Each learning session and pilot is checked against its signed-in owner. Legacy study participant identifiers are derived from the account, ignoring supplied IDs. Previous anonymous pilot records remain in the database but are not assigned to new accounts or exposed through the authenticated API.

Deploying publicly requires HTTPS and `VTW_SECURE_COOKIE=1`, a reviewed authentication/deployment design, recovery and account lifecycle management, retention/deletion procedures, database backup/access controls, operational monitoring, and further abuse testing. This is a local research login, not a claim of production certification. Accounts and study data live under ignored `data/runtime/` and are not committed to GitHub.

## Demonstration sequence

1. Show the anonymous checker and its three expanded member sections.
2. Open the workspace and create your own account; explain login is infrastructure, not novelty.
3. Show the three named laboratory cards.
4. Start learning, answer all baseline questions and explain the server-assigned condition.
5. Show the lesson, complete immediate transfer and inspect the report with denominators.
6. Explain the 24-hour gate. Resume a legitimately due session to demonstrate delayed trials; do not alter timestamps to present fake retention.
7. Sign out and show that lab access redirects to sign-in. Sign back in and resume saved progress.

Source guidance: [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html). Adaptive phishing interventions already exist, for example [ADVERT](https://arxiv.org/abs/2106.06907); this is why the claimed contribution must be narrower and evaluated comparatively.
