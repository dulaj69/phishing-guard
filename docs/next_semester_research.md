# Three defensible research extensions

These are candidate directions, not established novelty claims or completed features. A larger website is not automatically a larger contribution. Give each member a precise failure mode, a method, a baseline and an outcome.

| Owner | Candidate next contribution | Concrete demonstration | Evaluation that matters |
|---|---|---|---|
| Sanmith | Detect intent distributed across a short conversation, including Sinhala/Singlish and benign negation | “We are your bank” → “A code will arrive” → “Read it to us”: compare each message alone with the combined action sequence | Campaign-separated conversation splits; action F1, harmful-request recall, false alarms on genuine support, language-specific counts; compare latest-message-only and concatenation baselines |
| Perera | Recommend the next useful independent verification step under an evidence budget | A copied genuine domain is present, but the requested callback is unverified: show why checking the callback route matters more than rechecking the copied domain | Compare fixed checklist, score-only and action-specific evidence policy; measure harmful decisions, unnecessary checks and abstention; expert review of suggested checks |
| Rathnayake | Teach the highest-risk misconception, then fade assistance and measure retention | A confident wrong callback reason selects route verification; test new examples without advice now and later | Static vs adaptive teaching; judgement/reason correctness, confidence error, immediate and delayed transfer, dropout; participant-level randomisation and matched alternate forms |

Rathnayake's initial individual learning instrument is now implemented. Sanmith and Perera already have action-contrast and evidence-dependency workbenches; the conversation and next-check methods above are proposed additions, not deployed capabilities.

## A common scientific story

The integrated question is: **Can action-specific evidence improve both the current decision and a person's next unaided decision?** Sanmith supplies the requested action and its uncertainty. Perera identifies evidence relevant to that action, including what remains unknown. Rathnayake turns that gap into a warning or a teaching target and measures human outcomes. Keep ownership and evaluation separate even when components exchange data.

Example: a genuine bank domain in an SMS does not validate a different callback number. Sanmith extracts “call”; Perera recognises the unsupported route; Rathnayake can teach “matching identity detail is not route verification.” In a future conversation experiment, the dangerous action might only become clear after several messages.

## What to present this Thursday

Show the working baseline and its measured limitations, all three current labs, the new individual accounts, and the executable static/adaptive lesson comparison. Describe delayed transfer as scheduled measurement until a person genuinely returns. Explain the next semester's data collection and evaluation. Do not claim that authentication is research novelty, that all personalised teaching is new, or that a successful demo proves learning.

## Literature boundary

[ADVERT, Huang et al.](https://arxiv.org/abs/2106.06907) already studies adaptive visual assistance using attention information. [Appropriate reliance, Schemmer et al.](https://arxiv.org/abs/2302.02187) is relevant to the existing advice study. These are starting points, not an exhaustive novelty review. Your proposed distinction is action-specific evidence and misconception-driven teaching in the target language setting, evaluated with independent transfer. A systematic comparison is still required before calling it novel.

## What I would defer

Company workspaces, invitations, group aggregation and campaign administration belong after the individual flow is tested. So do automatic live bank crawling, free-form generative lessons and deployment. Each adds engineering or validation work without replacing the core experiments above. A reviewed fictional scenario bank and transparent deterministic teaching are easier to defend at the current milestone.
