# How to explain our research contribution

A specific methodological difference can support a novelty claim. A working prototype demonstrates implementation. A literature comparison supports originality. Experiments establish whether the method works well. These are different claims: novelty does not require an accuracy improvement, and an accuracy improvement alone does not establish novelty.

## A comparison we can make now

[ADVERT by Huang and colleagues](https://arxiv.org/abs/2106.06907) describes an adaptive phishing-prevention method using eye-tracking to estimate visual and attention states and adapt visual assistance during phishing-email recognition. Our current learning instrument uses a different input and selection mechanism: judgement correctness, reason correctness, confidence and provisional harm weights select a misconception lesson, followed by different no-advice questions and a 24-hour follow-up gate.

| Dimension | ADVERT's described approach | Our implemented prototype |
|---|---|---|
| Adaptation signals | Eye-tracking-derived visual and attention states | Judgement error, reasoning error and stated confidence |
| Adapted output | Visual assistance directed at attention | A lesson on credentials, borrowed identity or uncertainty |
| Selection mechanism | Attention-oriented adaptation described in the paper | Transparent harm-weighted misconception priority |
| Measurement in our work | Do not infer ADVERT's entire evaluation protocol from its abstract | Separate judgement/reason measures, confidence error, immediate transfer and gated delayed transfer instrument |
| Present evidence | ADVERT reports a human-subject evaluation | Our software and authored examples work; learning benefit has not been established in a participant study |

This supports a difference relative to ADVERT. It does not establish that no other paper uses misconception-based teaching. Nor does it establish superiority over ADVERT. Compare appropriate baselines and related learning literature before making those broader claims.

## Wording for the viva

“Our proposed contribution is an action-specific, evidence-aware banking SMS framework with misconception-targeted teaching. In contrast to ADVERT's eye-tracking-based attention adaptation, our teaching policy uses the user's judgement, explanation choice and confidence, weighted by the potential harm of the misconception. We have implemented the policy, a static-lesson comparison and immediate and delayed transfer instruments. Our next stage is to evaluate whether this selection method improves unaided decisions.”

Use “proposed contribution” confidently: it states what you are contributing without claiming a completed systematic novelty review. Do not describe the teaching instrument as multilingual yet; its current nine questions are English. The wider detection pipeline supports English, Sinhala and Singlish with important validation limitations.

## Each member's current contribution

- **Sanmith:** contextual requested-action extraction alongside multilingual SMS classification and spelling/negation diagnostics. Explain why “share an OTP” and “never share an OTP” require different treatment. TF-IDF and logistic regression themselves are established methods. The candidate contribution lies in the action-aware method and its evaluation in the target setting.
- **Perera:** action-relevant evidence policy, source freshness/coverage handling, uncertainty and auditable risk decisions. A matching published domain cannot verify a separate callback route. The candidate contribution is the policy and its evidence-dependency analysis, not merely adding an explanation table.
- **Rathnayake:** evidence-aware warning selection and reliance evaluation, extended with harm-weighted misconception teaching and independent transfer measurement. The new teaching experiment is distinct from the advice pilot; it does not itself measure reliance on AI advice.

For each member, write a related-work comparison table with named papers, exact supported differences, implementation status, baseline and planned test. Record “not established” where a source does not support an absence claim. Three different technical tasks do not automatically mean three independently novel contributions.

## Product and research views

The public checker should help a person understand and respond to a message. It now shows risk, requested action, reasons, evidence checks and next steps. Team names and internal model/policy outputs belong to the protected research analysis page and viva documentation. The detailed live analysis remains available at `/app/lab/message.html` after sign-in.
