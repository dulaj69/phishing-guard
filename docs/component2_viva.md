# Component 2 viva guide: Verify and risk assessment

## What the score means

The detector supplies Component 2 with `scam_score`, a value from 0 to 1,
computed as:

```text
min(1, P(phishing) + 0.5 × P(suspicious))
```

This is an **uncalibrated weighted model score**, not a probability or a
percentage chance that a message is fraudulent. In the Evidence Lab, the score
is manually controlled to compare policy outcomes; it is not a live model
prediction.

Component 2 combines that score with the requested action and available
evidence. It outputs a provisional risk tier and an assessment/abstention
decision, not a second numeric probability.

## How Component 2 derives the tier

1. **Map the model score to a likelihood band.**

   | Model score | Likelihood band |
   |---|---|
   | Below `0.40` | Low |
   | `0.40` to below `0.75` | Medium |
   | `0.75` or above | High |

2. **Assign an ordinal harm level to the detected action.** No action = `0`,
   opening a link = `1`, calling or replying = `2`, and sharing credentials,
   paying, or installing an app = `3`. This is a policy category, not a
   measured amount of harm.

3. **Look up the initial tier in the likelihood-by-harm matrix.**

   | Likelihood \ Harm | 0 | 1 | 2 | 3 |
   |---|---|---|---|---|
   | Low | Low | Low | Low | Medium |
   | Medium | Low | Medium | Medium | High |
   | High | Medium | High | High | Critical |

4. **Apply evidence policy.** An explicit, source-supported contradiction
   raises the tier by one step, capped at Critical. A passing match never
   lowers risk: a copied bank name, sender ID, or domain does not authenticate
   the SMS. Missing, stale, or incomplete evidence is not automatically a
   contradiction. A credential-sharing request has a minimum High tier.

5. **Decide whether to abstain.** At a Medium likelihood, absent
   action-relevant supporting evidence, the policy abstains rather than
   presenting a firm verdict. It also abstains when action extraction is
   uncertain (except for the credential-request floor). The tier remains
   visible, but advice should respect the abstention.

The implementation is in [`verify/risk.py`](../verify/risk.py); the detector
score formula is in [`detection/model.py`](../detection/model.py). The
Component 2 output exposes likelihood, harm level, matrix tier, evidence
adjustment, final tier, and abstention state.

## Demonstration steps

1. Start the application from the project root:

   ```powershell
   .\.venv\Scripts\python.exe run_app.py
   ```

   Open the printed URL, sign in with a local practice account, open
   `/app/lab/`, and select **Evidence Lab**. Use rehearsal mode, not a
   participant session.

2. Select **Call a number**, leave the score at `0.55`, and keep **Explicit
   supported contradiction** and **Matching published domain** selected.
   Leave stale evidence, remove all evidence, and uncertain action unchecked.
   Run the evidence audit.

3. Explain the steps shown: `0.55` maps to Medium likelihood; calling is harm
   level 2; the matrix gives Medium; the explicit contradiction raises the
   final tier one step. The matching domain does not lower it.

4. Uncheck the contradiction but keep the domain match. Run the audit again.
   The domain does not verify the callback number, so the policy abstains at
   this middle likelihood. This shows why evidence must be relevant to the
   action in the message.

5. Optionally select **Share an OTP**, set the score to `0.10`, and run the
   audit. The credential action's harm level and minimum-High policy floor
   prevent a Low final tier.

The lab uses controlled scores and fictional evidence. It demonstrates policy
behavior; it is not real-bank verification or an evaluation of real-world
accuracy.

## Suggested viva answer

> “Component 2 does not turn the score into a probability. It takes the
> detector's uncalibrated weighted score, maps it to a Low, Medium, or High
> likelihood band, and combines that band with the harm category of the
> requested action using a lookup matrix. Explicit source-supported
> contradictions can raise the tier, while a matching bank detail cannot lower
> it because details can be copied. If evidence is insufficient for a
> confident decision, the system can abstain and advise independent
> verification. The thresholds and policy are provisional and still need
> validation with independent data and expert judgements.”

## Limitations to state

- The thresholds and harm matrix are provisional policy choices, not validated
  risk levels.
- The detector score is uncalibrated and must not be described as a fraud
  probability.
- Lab simulations do not establish that a real message or bank contact is
  authentic.
- A passing check supports only the specific published detail checked; it
  cannot prove who sent the SMS.
- Threshold sensitivity and risk-tier decisions still need held-out evaluation
  and independent expert judgements.
