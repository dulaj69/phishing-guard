# Three component research extensions: implementation, claims and evidence

22 October 2026 · Verify-then-Warn · Progress presentation preparation

## The correction

The previous classifier, rules, risk matrix and personalised warnings are useful foundations. They do not, by themselves, establish three original research contributions. Earlier descriptions that suggested otherwise were too strong. The same standard applies to every member.

The extensions below are working experimental mechanisms with testable hypotheses. They are not proof of worldwide novelty. A new implementation can differ from one paper while still overlapping another. A positive result against our old code is an engineering improvement, not a state-of-the-art comparison.

Our narrower research theme is: **Can preserving uncertainty about the requested action, binding evidence to its exact destination, and teaching the resulting distinction reduce unsafe decisions in banking messages?**

This supports three individual investigations. The common application connects them, but each needs its own evaluation. Novelty might ultimately lie in a carefully defined method, an independently annotated local-language resource, or an empirical finding. The current rule implementation alone is not enough to establish that.

## 1. Sanmith: interpreting incomplete requests without hiding ambiguity

### Customer problem

A sender says, “Your OTP is ready.” Then: “Send it to us.” The previous clause rules cannot connect the object in the first message to the action in the second. Simply concatenating the messages does not fix that rule limitation.

Now consider: “Your OTP and receipt are ready. Send it to us.” Automatically choosing OTP or receipt would conceal uncertainty. The distinction matters: disclosing an OTP and sending a document have different consequences. A document can still contain private information; it is never automatically safe.

### Implemented extension

The experimental extractor normalises each message, preserves its speaker label, and creates records for supported requests. For a reference such as “send it,” it looks for credential/document mentions in the last three sender clauses. It returns all supported object types instead of choosing one arbitrarily. Each object has its message number, text span and normalized-text offsets.

It records requested, negated and reported status using the existing patterns. Recipient speech does not become a sender request. Direct call/link actions reuse the existing extractor with contacts collected from the relevant action clause.

The output is a set of interpretations with evidence, not a new probability. Sonal evaluates each interpretation. If the interpretations change the provisional risk or recommendation, the interface requests clarification without collecting an actual code or document.

Technologies: Python, Unicode normalization, regular expressions, typed JSON via FastAPI/Pydantic. This extension is deterministic; it is not a trained coreference model, a transformer, or conformal prediction. The existing TF-IDF/logistic-regression classifier remains the baseline elsewhere in the app.

### Research question and comparison

**Does preserving alternative action–object interpretations reduce missed credential requests and unsafe single interpretations in English/Sinhala/Singlish banking conversations, at an acceptable clarification burden?**

Compare: last-message classifier/extractor; concatenated-message baseline; a context model that selects one interpretation; an uncertainty-aware method with clarification disabled; the same method with clarification enabled. Include a trained contextual baseline before making strong comparative claims.

Measure action/object precision, recall and F1; antecedent identification; dangerous requests missed; erroneous credential warnings on benign messages; unresolved-case rate; questions per conversation; and risk versus coverage when the system declines to commit. Returning every possible action must be penalised through precision and set size.

### Closest prior work and boundary of the claim

- [DIDECO, LREC 2026](https://aclanthology.org/2026.lrec-1.542/) already distinguishes explicit goals and persuasion mechanisms in annotated spear-phishing emails. Therefore “we detect intent” is not our novelty. Our narrower target is object references and uncertainty propagation in banking-message sequences. This is a task distinction, not proof DIDECO cannot support it.
- [Conversational smishing dataset, 2026](https://arxiv.org/abs/2604.11752) already provides multi-round conversations and detection baselines. Therefore “we analyse multiple messages” is not our novelty. Our target additionally requires action/object/reference annotations and consequences of ambiguity.
- [Conformal Intent Classification and Clarification, 2024](https://arxiv.org/abs/2403.18973) already studies intent clarification. Our proposed question-selection criterion is downstream banking-action consequence, not merely uncertainty about an intent label. Our current rules provide none of that paper’s statistical coverage guarantees.

These sources establish overlap and motivate comparisons; this is a focused literature screen, not an exhaustive review proving an unoccupied gap.

### Present limitations

Only a bounded list of object/verb patterns is supported. There is no general syntax, coreference, quotation parser or authenticated speaker identity. English and limited Sinhala/Singlish patterns do not establish multilingual robustness. “Authentication secret,” “pass the above,” and “the caller said send it” expose retained failures. The independent multilingual dataset and trained context model remain future work.

## 2. Sonal: evidence must support the actual requested destination

### Customer problem

“Orion Bank: published number 0112345678. Call 0771234567.” A matching published number somewhere in a message must not validate the different number the customer is asked to call.

The earlier policy checked the evidence category: an official-number match could count as relevant support for a call. The extension requires the action AND normalized requested destination to match. It also keeps evidence availability distinct from sender authenticity.

### Implemented extension

For each interpretation from Sanmith, the binding evaluator records which facts were used and why others were rejected. A fact must match action and destination, have accepted provenance, and be marked current. Stale/missing or different-destination facts cannot resolve the uncertainty.

Each interpretation gets its own existing provisional risk assessment. The UI displays the minimum/maximum tiers across interpretations, without treating that range as a statistical confidence interval. A credential interpretation retains the existing minimum-High rule. User clarification is explicitly labelled as user-supplied, not independently verified.

The same input is also processed by the older check-type-only policy to show exactly when its abstention decision differs. A current matching destination still does not prove that the message or sender is authentic.

Technologies: Python, explicit evidence records, exact normalized-value matching and the existing deterministic risk policy. No web crawler or new learned risk model is introduced. The new workbench uses a fictional registry; its current/stale state is a controlled experimental input, not a real-time provenance check.

### Research question and comparison

**Does binding evidence to the requested action and destination reduce false support from copied legitimate details, while preserving useful decision coverage under missing or stale evidence?**

Compare no verification, category-only verification, exact destination binding, and destination binding with propagated action uncertainty. Hold the message/model score fixed while swapping one evidence fact. Evaluate contradictory sources and complete versus incomplete registries in the later study.

Measure incorrect-support rate, dangerous false reassurance, abstention/coverage, expert agreement on decisions, and stability under irrelevant evidence insertion. Report whether lower error comes merely from abstaining more often. Use the same coverage point where possible. Do not call exact matching a newly invented algorithm.

### Closest prior work and boundary of the claim

[Provenance-Guided Evidence Contracts, Xu and Luo, 2026](https://www.techscience.com/cmc/online/detail/28363) already binds admissible evidence, provenance and intent–artifact consistency in LLM phishing detection. Therefore provenance, structured evidence, deterministic validation, and consistency checks are not first contributions here.

Our narrower experimental setting is external bank evidence tied to an SMS-requested destination, combined with alternative action interpretations and abstention. That differs from the webpage/LLM setting described in the paper’s abstract. It does not establish that every mechanism is absent from that paper or the wider literature. Its full method and other verification systems must be assessed before a strong originality claim.

### Present limitations

The new demonstration contains one fictional phone fact and current/stale/missing toggles. It does not validate real banks, fetch authoritative sources, infer freshness from dates, or authenticate users/senders. Existing public verification is still the earlier pipeline; the experimental binding method is in the signed-in lab. A real evidence adapter and independent source review are required before public integration.

## 3. Ravindi: teach the decision-relevant distinction, then test transfer

### Customer problem

A warning may persuade a person to avoid one message without teaching why. A person might learn the wrong shortcut: “the bank name looks genuine,” “any matching contact makes it safe,” or “missing evidence proves a scam.”

### Implemented extension

The rehearsal selects one of three concepts from the preceding analysis: what an ambiguous object refers to; whether evidence covers the requested destination; or what missing/stale evidence means.

It presents a pair of authored examples differing in that concept, asks the learner which feature matters, and explains the response. It then removes that explanation and presents a new example for the learner to answer. The application evaluates the answer but does not log it as participant data or report a learning gain.

This is a decision-distinction rehearsal. It is not machine-learning contrastive training, causal inference, or a validated educational intervention. The three lessons and transfer examples are fixed English templates. A learner’s response does not yet update a persistent mastery model.

Technologies: Python-authored lesson specifications, server-side answer evaluation, JavaScript/HTML interface, and existing individual-account access controls. No LLM generates these lessons.

### Research question and comparison

**Do matched examples focused on a user’s specific misunderstanding improve independent action choices and reasoning on unseen banking scenarios more than an equally informative ordinary warning?**

Compare a standard warning, an equally long explanation, a randomly selected matched-pair lesson, and a concept-targeted matched-pair lesson. The final two conditions separate the effect of pairing from targeting. Keep reading time, difficulty, language, and exposure comparable.

Measure safe action selection AND correct reason, confidence on errors, false alarms on legitimate messages, immediate transfer, and delayed transfer. Use new brands, surface wording, objects and routes at transfer; do not reuse the teaching template. Balance scam/legitimate proportions across phases. Randomise answer positions and record stable option IDs in a future study.

Do not infer durable learning from a correct immediate answer. The current new page is a rehearsal interface, not a randomised study implementation. The older learning/pilot system remains separate; adapting its logging and allocation to this instrument is a next milestone.

### Closest prior work and boundary of the claim

- [ADVERT](https://arxiv.org/abs/2106.06907) already studies adaptive phishing assistance. Adaptive warnings are not new in themselves.
- [It’s a Match, CHI 2025](https://doi.org/10.1145/3706598.3713845) investigates personalised phishing training. Personalisation alone is not our novelty.
- [Improving online anti-phishing training using cognitive large language models, 2026](https://www.sciencedirect.com/science/article/abs/pii/S0747563225002079) uses a cognitive model to select examples and inform feedback. Selecting a lesson based on a user need is already established.

The proposed distinction is teaching action/evidence relationships identified by this pipeline and measuring independent transfer under copied legitimate details and uncertainty. This is a narrower hypothesis. Paired examples and counterfactual explanations are established ideas too; their application here needs comparative evidence, not a new name.

## Shared evaluation contract

1. Freeze development rules before building the final test set. Have independent annotators create/review examples without seeing predictions. Use native Sinhala/Singlish reviewers.
2. Annotate requested action, object, antecedent span, requested destination, speech status, ambiguity and acceptable clarification. Retain unresolved/disputed cases with documented adjudication.
3. Split by scenario/campaign/template family; translations and paraphrases of one source stay in the same partition. Randomly splitting near-duplicate messages exaggerates generalisation.
4. Register hypotheses, comparators, metrics, exclusions and analysis before looking at final results. Report confidence intervals and per-language denominators. Determine dataset/participant size from the analysis and a justified precision or power target.
5. For human studies, obtain institutional approval as required, informed consent and a debrief. Pilot the wording and difficulty before recruitment. Rehearsals must not become participant findings.
6. Preserve negative findings. Failure to beat a baseline does not justify changing test labels or dropping hard cases. It narrows the claim and guides the second-semester work.

## What the current checks establish

The extension suite tests source-span integrity, interpretation alternatives, explicit clarification, recipient/request separation, mismatched destinations, stale/missing evidence, unaccepted provenance, credential safeguards, account requirements, bounds and answer withholding.

There are 12 authored development fixtures. The extension gets 9 exact action-set matches; both older last-message and concatenated-message rules get 6. These fixtures were constructed alongside the implementation, so these counts are development diagnostics only. The set-returning interface also changes the ambiguity task; an independent evaluation must control for that and measure false extra interpretations. There is no state-of-the-art result or human-learning result.

The original 18-case comparison remains a different diagnostic. Do not combine its denominator with these 12 cases or quote either as real-world accuracy.

## Demo sequence and ownership

Open the signed-in research workbench and choose **New: requests, evidence & learning**. The experimental page is `/app/lab/boundary.html`.

1. **Sanmith:** choose “OTP request split across messages.” Show the OTP antecedent in message 1 and the requested action in message 2. Then choose “Two possible objects.” Explain why a single label loses information.
2. **Sonal:** show Medium–High interpretations and the clarification question. Select document; explain that the interpretation narrowed because the user clarified, not because the bank verified anything. Next select “Published number beside a different requested number.” Contrast category-only support with exact destination binding. Switch current to stale on “Exact requested number match.”
3. **Ravindi:** answer the selected pair exercise, then try its new example without example-specific advice. Explain what the future controlled study measures and why this rehearsal cannot establish effectiveness.
4. Show one known limitation from the menu. Explain the next experiment needed to address it.

Presentation wording: “We have implemented the baseline and three experimental extensions. Our research hypotheses concern ambiguity-aware request interpretation, destination-bound evidence, and decision-relevant learning. We can demonstrate the mechanisms and comparisons today. Independent multilingual and participant evaluations are the next stage.”

Do not say: “We invented intent detection,” “we are first to verify evidence,” “we invented adaptive training,” “this has proven novelty,” or “the extension is 75% accurate on real messages.”

## Implementation map

- Sanmith: `detection/context.py`
- Sonal: `verify/binding.py`
- Ravindi: `warn/contrast.py`
- Shared orchestration/fixtures: `research/lab/decision_boundary.py`
- Authenticated endpoints: `/research/boundary/catalog`, `/analyze`, `/benchmark`, `/answer` under the same prefix.
- UI: `warn/static/lab/boundary.html` and `boundary.js`
- Checks: `tests/test_decision_boundary.py`

These are local working-tree changes on the integration branch. They have not been pushed to the three member branches. The existing public detector and presentation tag have not been replaced by these experimental methods.
