# Supervisor demonstration: research workbench

This is a working mid-project demonstration, not proof that 50% of the research is validated. No detailed rubric has been provided; the working assumption is a runnable backend with small-data experiments and a credible second-semester plan. Candidate novelty requires full-paper comparison and empirical evaluation.

## What each member can own and defend

| Member | Proposed contribution | Implemented experiment | Evidence still needed |
|---|---|---|---|
| Sanmith | Action understanding that is stable under meaning-preserving changes and sensitive to meaning-changing contrasts in Sinhala/Singlish/English | Raw vs normalised classifier, keyword vs contextual action comparator, 18 authored fixtures, action spans, fixed perturbations, exact model fingerprint, downloadable results | Native-adjudicated contrast pairs; real campaign-held-out test data; trained joint model; paired statistical comparisons |
| Perera | Auditable risk decisions under incomplete or conflicting evidence | Score/harm/evidence policy comparisons, stale and missing evidence interventions, leave-one-fact-out audit and exact minimum-cardinality sufficient sets | Official field-scoped bank facts, expert risk rankings, validation of policy thresholds and source freshness |
| Rathnayake | Evidence-aware warning policy evaluated through comprehension and independent transfer | Three server-assigned conditions, initial/final confidence, action choice, comprehension questions, six advice trials and three new no-advice trials, server-tracked outcomes | Approved protocol, power analysis, representative participants, controlled linguistic variants, delayed transfer and inferential analysis |

The minimum sufficient set is relative to a policy's tier and abstention output. It is not proof of real-world causal importance. The no-advice block measures immediate performance on different items; it does not establish long-term learning or improvement over baseline ability.

## Suggested 10-minute demonstration

1. **Overview (1 minute).** Identify the three questions and who owns them. Distinguish live diagnostics, controlled simulations and pilot observations. The actual model fingerprint identifies the loaded classifier, not the dataset or code revision.
2. **Action lab (3 minutes).** Select the English credential request and run the contrast test. Inspect raw vs normalised output and action spans. Then choose a negation fixture. Run all cases; show every mismatch, including the indirect English request and reported Sinhala/Singlish speech. Explain that these authored fixtures are diagnostic, possibly overlapping training patterns, not a gold test set. The keyword comparator deliberately ignores clause scope; it is a controlled ablation, not a claim about the strongest prior method.
3. **Evidence lab (3 minutes).** Start with callback, score 0.55, supported contradiction and matching domain. Run the audit. Remove the contradiction: a matching domain does not resolve the request to call a different number, so the policy abstains at a middle score. Make the source stale: unsupported evidence becomes unknown and the policy can abstain. Remove all evidence. Switch to credential request with score 0.10: the credential floor can retain High risk without external facts, so the minimum sufficient set can legitimately be empty. Every score and fact in this view is a controlled simulation.
4. **Human decisions (2 minutes).** Compare the three warning conditions for a selected simulated profile. Begin a demo rehearsal. Explain server assignment and the initial/advice/final sequence. Show the later transfer block if time permits; a full nine-trial run is better completed before a live presentation. Rehearsals are labelled as such and must not be included in research findings.
5. **Remaining work (1 minute).** Present the real data, expert and participant milestones. Do not describe authored examples or test-suite success as completed validation.

## Session protocol

The server balances conditions across started sessions within each mode, randomly breaking ties. Advice and transfer items are shuffled within their respective blocks. There are six English advice items (two deliberately incorrect advice cases) and three English transfer items. Content is fictional. The same comprehension prompts are used across conditions. Guided-trial feedback is the same across conditions; transfer truth is withheld until the block is complete. Condition assignment is not evidence of a successful randomized trial: attrition, sample size, item difficulty and carryover still need a formal analysis plan.

The pre-advice prompt is an experimental intervention. The current wording invites independent checking, but this fictional pilot cannot verify that a participant actually consulted an external source. Do not call a click on that prompt verified human fact checking.

All choices are simulated; no real number is dialled and no link is opened. Session tokens and decision records are local SQLite data under ignored `data/runtime/`. No name, email, contact number or full SMS text is stored in the new pilot tables. Rendered warning templates are stored to reproduce the advice shown. The session token is a bearer identifier; this is not an authenticated public multi-user deployment.

Consent is mandatory for the pilot mode. Demo rehearsals do not require participant consent and are excluded conceptually from pilot findings. The checkbox is an instrument-level consent mechanism, not institutional ethics approval. If a participant stops, the partial local record remains; establish retention and withdrawal procedures before formal recruitment.

## What is new in the implementation

- `/app/lab/`: responsive research workbench; `/app/`: original SMS app.
- `/research/catalog`, `/research/robustness`, `/research/benchmark`: diagnostics.
- `/research/evidence`: controlled evidence audit; no registry mutation.
- `/research/warning-preview`: simulated profile comparison; no logging.
- `/research/pilot/sessions`, `/{token}/initial`, `/{token}/final`, `/{token}/report`: bounded, ordered pilot trials.
- JSON exports contain provenance, denominators and interpretation limits. Custom/private message entry is deliberately absent from the diagnostic fixture lab.

## Claims to avoid

- “No one has studied robustness or adaptive warnings.” These areas have prior work.
- “The rule extractor understands all Sinhala/Singlish.” Known counterexamples remain visible.
- “100% on a few examples means the model is accurate.” It does not.
- “The risk slider is probability.” It is a manually controlled score.
- “Transfer accuracy proves learning.” Item difficulty and prior ability are alternative explanations.
- “The site proves the project is 50% complete.” Completion must be assessed against the marking rubric.

## Closest prior work to review

- Adversarial robustness in smishing (2026 preprint): https://arxiv.org/abs/2608.12889
- Appropriate reliance and its measurement: https://arxiv.org/abs/2302.02187
- Trust-adaptive interventions: https://doi.org/10.1145/3742413.3789136
- Judging Phishing Under Uncertainty (CHI 2025): https://vaniea.com/publication/saka2025chi/saka2025chi.pdf

These references motivate precise comparison; they do not establish that our proposed combination is novel.

## Midyear delivery and next semester

The backend implements detection, action extraction, evidence checking, risk policy, warning composition and an ordered pilot session. This is a functional prototype; the trained joint multilingual model and research validation remain incomplete. Avoid describing every research backend as finished.

A fresh small-data baseline experiment used 936 rows: 36 authored seed examples and 900 synthetic examples (569 English, 244 Singlish, 123 Sinhala). It trained TF-IDF character n-grams plus logistic regression with template-grouped evaluation and random seed 7. Macro-F1 was 0.556. This run does not replace the current live model. The Singlish phishing test support was only one item, so its perfect recall is not meaningful evidence of language coverage. These results show a running training pipeline and a concrete data/split weakness to address.

The separate live action diagnostic matched 15/18 authored cases with contextual extraction versus 11/18 with the keyword comparator. These are different experiments; do not combine their metrics.

### Next week's presentation package

- Demonstrate the end-to-end SMS backend and all three research workbench views.
- Explain one research question, baseline, proposed method and measurable outcome per member.
- Show the small-data experiment, failures and language support, alongside automated backend checks.
- Present dataset provenance and explain why synthetic examples cannot validate real-world performance.
- Complete a labelled rehearsal before the presentation; do not count rehearsal responses as study participants.

### Second-semester milestones (proposed)

1. Weeks 1–3: agree annotation guidelines, privacy/consent protocol and native-language reviewers; collect and deduplicate an initial real-data batch; reserve a campaign-separated gold test set before tuning.
2. Weeks 4–7: Sanmith trains and compares the multilingual action model and robustness objective against TF-IDF and rule baselines; report per-language/action support, uncertainty and failures. Perera curates official facts with source/date/field scope and obtains independent expert risk judgements.
3. Weeks 8–10: freeze the candidate pipeline and thresholds after development-set analysis; run action/evidence ablations and error analysis. Rathnayake pilots item difficulty and comprehension, finalizes study design and determines sample size from power analysis.
4. Weeks 11–14: after required institutional approval, run the participant study with all three conditions; measure appropriate reliance, comprehension and transfer, accounting for attrition and repeated measurements.
5. Weeks 15–16: evaluate once on the reserved test set, report confidence intervals and limitations, document reproducibility and prepare the final dissertation/demo.

These are planning windows, not a guarantee that recruitment or data collection will fit. Reserve time for annotation disagreements and failed experiments. A defensible negative result is more useful than an inflated novelty claim.
