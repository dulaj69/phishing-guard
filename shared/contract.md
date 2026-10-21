# Shared data format (all three members)

This file is the agreement between the three parts. Each part only reads the
fields listed here, so each of you can change your own code freely.

```
SMS text ──► 1. detection (Sanmith) ──► 2. verify (Perera) ──► 3. warn (Rathnayake) ──► user
```

Rules:
- You may ADD new fields. Never rename or remove a field without telling the team.
- Message text is never written to logs.
- Full examples are in `shared/examples/`.

## 1. Detection output (Sanmith → Perera)

| Field | Type | Meaning |
|---|---|---|
| `label` | `legit` / `suspicious` / `phishing` | Model's best guess |
| `probabilities` | object | One probability per label, adds up to 1 |
| `scam_score` | 0–1 | `P(phishing) + 0.5 × P(suspicious)`. Used for the risk tier |
| `language` | `en` / `si` / `singlish` / `mixed` | Detected language |
| `normalized_text` | string | Text after cleaning tricks (homoglyphs, hidden characters, spacing) |
| `tricks_found` | list | e.g. `homoglyph`, `zero_width`, `spaced_letters`, `leetspeak` |
| `anatomy.claimed_bank` | object or null | `{"id": "orion", "name": "Orion Bank"}` |
| `anatomy.primary_action` | string | Most harmful thing the message asks for: `share_credential`, `pay`, `install`, `call`, `reply`, `click`, `none` |
| `anatomy.actions` | list | All actions found |
| `anatomy.contacts` | list | `{"type": "phone"/"url", "value": ..., "normalized": ...}` |
| `anatomy.tactics` | list | `URGENCY`, `ACCOUNT_THREAT`, `REWARD_LURE`, `AUTHORITY`, `FEE_REQUEST` |
| `anatomy.spans` | list | `{"type", "text", "start", "end"}` for highlighting |
| `model_version` | string | Which model made this |

## 2. Verify output (Perera → Rathnayake)

| Field | Type | Meaning |
|---|---|---|
| `fact_checks` | list | `{"check", "result": "pass"/"fail"/"unknown", "detail", "source"}` |
| `explanation` | list | Top words that pushed the score: `{"word", "weight"}` |
| `risk.tier` | `Low` / `Medium` / `High` / `Critical` | Final risk tier |
| `risk.likelihood` | `Low` / `Medium` / `High` | From `scam_score` |
| `risk.harm` | 0–3 | From `primary_action` |
| `risk.matrix_tier` | string | Tier before the fact-check adjustment |
| `risk.adjustment` | `up` / `down` / `none` | What the fact checks did |
| `risk.reasons` | list of strings | Plain-English reasons, shown to the user |
| `official_contact` | object or null | The bank's real hotline, for the "safe alternative" button |

## 3. Warning output (Rathnayake → user)

| Field | Type | Meaning |
|---|---|---|
| `show` | bool | Whether to show a warning at all |
| `level` | tier | Same as `risk.tier` |
| `language` | `en` / `si` / `singlish` | Warning language |
| `title` | string | Short headline |
| `lines` | list | `{"text", "source"}`: every sentence points back to a fact check or reason |
| `intervention` | `standard` / `light` / `verify_first` / `strong_evidence` | Chosen by the reliance engine |
| `safe_action` | object or null | e.g. call the official hotline |
| `needs_language_review` | bool | True if the Sinhala/Singlish wording is not yet checked by a native speaker |

## Research upgrade (2026-10-18)

Existing fields remain; these additions change decision semantics:

- `detection.score_semantics = uncalibrated_weighted_score`. Do not present `scam_score` as a percentage probability.
- `anatomy.action_evidence[]`: action, status (`requested`/`negated`/`reported`), text, start, end, method. Offsets refer to normalized text.
- `anatomy.action_uncertainty`: `rule_based` or `uncertain`; these are categorical statuses, not confidence probabilities.
- `risk.abstain`, `risk.decision`, `risk.evidence_quality`, `risk.action_uncertainty`, `risk.policy_version`, `risk.score_semantics`.
- `risk.tier` remains the provisional tier even when abstaining. Consumers MUST check `abstain` before deriving advice; `/analyze` returns `ai_advice = uncertain` on abstention.
- Evidence quality: supported, contradicted, conflicting, insufficient. Supported details do not authenticate the message. Missing facts are unknown unless completeness is explicitly documented. Source records include field, freshness, fictional.
- `official_contact` is null for fictional, stale, or insufficiently sourced registry entries.
- `warning.intervention` additionally supports `uncertainty`. `verification_prompt` is displayed before advice for verify_first. `abstain` and `evidence_quality` are carried through.
- `condition`: static, user_only, evidence_aware. `/analyze` returns an `analysis_id` only for a valid study trial.

Published details never lower the tier. Existing clients relying on a `down` adjustment, fictional safe-contact buttons, arbitrary `/decision` truth, or scenario IDs enabling planted errors need migration. See `docs/api_contract.md`.
