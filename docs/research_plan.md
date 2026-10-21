# Research plan: three independently testable contributions

Status: implemented research scaffolding and provisional policies, not validated novelty or final results.

## Sanmith: robust action understanding

Question: can action supervision and meaning-preserving language variants improve action extraction across English, Sinhala and Singlish?

Implemented: clause-scoped request/negation/reported-speech rules, exact normalized-text evidence spans, explicit uncertain extraction, a supervised character-ngram multilabel baseline trainer, and action/pair-consistency evaluation. Legitimate payment requests remain payment actions; a harmful action is not itself a phishing label. Bare URLs are contacts, not automatic click requests.

Remaining: collect consented, redacted local SMS; independently annotate and adjudicate actions; run and compare the supplied experimental joint XLM-R action/classification trainer and paired-view consistency loss once labels exist. The transformer training path has not been executed here (no gold labels or transformer runtime); its dataset/pair validation is tested. The current live extractor remains a rule baseline, not a learned semantic model. Reported speech, clause linking, actor/recipient resolution, and Sinhala negation are not fully solved. Native speakers must validate variants.

Compare rules, supervised character baseline, standard multilingual model, joint model, and joint model with consistency training. Report action micro/macro-F1 with label support, exact set match, and consistency alongside accuracy (consistent mistakes are still mistakes). Include negations, reports of scams, legitimate requests, obfuscation, zero-link scams, and unknown bank names. Fit thresholds on validation only. Group campaigns, template families and all language variants together; audit cross-source duplicates. Hold out a real local gold test set.

## Perera: risk under incomplete evidence

Question: how does the decision policy behave as evidence coverage and source freshness deteriorate?

Implemented: field-specific source provenance, a provisional 180-day freshness limit, partial versus explicitly complete registry coverage, no risk reduction for copyable matching details, credential-request risk floor, action-uncertainty propagation and abstention. Public-policy contradictions are checked against the actual credential request. Fictional or stale contact entries never produce verified contact buttons.

Compare likelihood-only, matrix-only and evidence policy; the executable evaluator currently provides matrix versus evidence with gold and predicted actions at three simulated coverage levels. Add the likelihood-only threshold baseline with thresholds fixed on validation for the formal experiment. Registry entries remain fictional until official facts are researched and reviewed; do not infer that a list is exhaustive merely because a bank published it. Re-check stale facts manually. A matching sender ID does not authenticate a sender.

Obtain independent expert judgements, record expert agreement, and report false-low-risk rate among answered high-harm phishing, decision coverage, tier error and weighted kappa. Always report abstained dangerous cases separately in the final paper; abstention can otherwise make results appear better. The evaluator's `score` must come from held-out predictions; it cannot verify that provenance automatically. It must not be called calibrated probability until independently calibrated and evaluated. Freshness and risk thresholds need validation/sensitivity experiments.

## Rathnayake: user and evidence adaptation

Question: does evidence-aware adaptation improve decisions relative to static warnings and user-only adaptation?

Implemented: three selectable pilot conditions, condition/session-isolated profiles, an independent-check prompt before advice, explicit uncertainty messages, safe-contact choice separate from message judgement, initial/final decisions, and server-owned single-use study trials. RAIR and RSR only use eligible initial-disagreement trials with known truth and definite AI advice. Missing denominators are null, not zero. Abstentions stay in logs but are excluded from binary reliance measures. Unknown real-world truth cannot update accuracy/reliance. Planted advice errors are study-only and opposite the scenario truth; factual evidence itself is retained.

The UI is a simulated pilot: buttons never dial numbers or open SMS links. The condition selector is for the facilitator; it is not randomized assignment. Keep condition and language fixed per participant in a formal study, counterbalance scenario order, use different equivalent items for repeated sessions, and pre-register sample size with a power analysis. Current ten fictional scenarios and provisional three-decision adaptation are insufficient for strong findings. A checkbox is pilot consent only, not institutional approval or a complete participant information sheet. Obtain study approval, full consent, native-language review and debrief planted errors before formal recruitment. Add a delayed no-advice transfer session as a separately specified experiment.

Run `python -m research.study_report decisions.csv --output work/study_summary.json` after export. It reports participant/session summaries and denominators, not significance tests over dependent repeated trials. Study logs remain local and ignored by Git.

## Annotation format and commands

Use JSONL, one record per SMS. Store consented/redacted real data under ignored `data/real/`. Minimum fields:

```json
{"id":"unique-id","group_id":"campaign-or-template-family","pair_id":"optional-equivalent-variant-family","split":"train","language":"singlish","text":"redacted message","label":"phishing","actions":["share_credential"],"primary_action":"share_credential"}
```

`split`: train / validation / test. `label`: legit / spam / phishing. `actions`: share_credential / pay / install / call / reply / click / none. Do not use `none` with other actions. Annotate all requested actions even when the message is legitimate. Add annotator IDs, annotation version, evidence spans, source/consent provenance, and adjudication notes in extra fields. Double-annotate a subset; measure agreement before adjudication. Do not silently map public spam to phishing. The existing classifier's legacy `suspicious` label remains for compatibility; retraining with new label definitions is a separate migration.

Optional verification fields: `score` (held-out weighted score), `checks` (list using the shared fact-check format), and `expert_tier` (Low/Medium/High/Critical). Group all equivalent variants in the same split. The loader rejects duplicate IDs, invalid labels and cross-split group/pair/normalized-text leakage. This cannot replace manual near-duplicate/campaign review.

```sh
python -m research.evaluate data/real/annotations.jsonl --output work/component_report.json
python -m research.train_actions data/real/annotations.jsonl --output work/actions.joblib
# Optional transformer experiments (install requirements-ml.txt first):
python -m research.train_joint data/real/annotations.jsonl --out work/joint --consistency 0
python -m research.train_joint data/real/annotations.jsonl --out work/joint_consistent --consistency 0.2
python -c "from warn import reliance; reliance.export_csv('data/runtime/decisions.csv')"
python -m research.study_report data/runtime/decisions.csv --output work/study_summary.json
```

Create `work/` first. The action trainer saves an experimental model; it does not replace the installed classifier or extractor. No real evaluation data or fabricated participant records are supplied.

## Prior work and claim boundaries

These are candidate contributions. Never claim novelty because a feature was added, a model is larger, or a Sinhala translation exists. Maintain a comparison table of task, language, method, datasets and evaluation against full papers.

- Smishing adversarial robustness and code-switching: https://arxiv.org/abs/2608.12889 (preprint).
- External knowledge in phishing detection: https://arxiv.org/abs/2403.02253 (KnowPhish; webpages).
- Trust-adaptive interventions: https://doi.org/10.1145/3742413.3789136.
- Appropriate reliance measurement: https://arxiv.org/abs/2302.02187.

The earlier PDF's broad “nobody has done this” claims need revision. The PDF is unchanged reference material.
