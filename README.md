# Verify-then-Warn (J26-IT-442)

Final-year research project. One system, three parts:

```
SMS ──► 1. detection (Sanmith) ──► 2. verify (Perera) ──► 3. warn (Rathnayake) ──► user
         what does it want?          is it true? how risky?    warn in the user's language,
                                                                adapted to how they trust the AI
```

This is the **PP1 prototype**: every part works end to end. The model is a simple
baseline trained on mostly synthetic data, so all numbers are **preliminary**.

## 1. First-time setup (Mac)

Open the project folder in VS Code, then open **Terminal > New Terminal**:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Get the data, train the model, run the tests

```bash
python -m detection.synth          # makes 900 synthetic training messages
python -m detection.get_datasets   # downloads the 5 public datasets (needs internet)
pip install xlrd                   # only for the one Indian .xls file
python -m detection.public_data    # builds data/processed/public_v1.csv (13,021 messages)
python -m detection.train          # trains on all of it, prints preliminary results
pytest -q                          # all tests should pass
```

Optional, and worth a slide:

```bash
python -m detection.experiment_language   # does the English public data help Singlish?
```

### Where we are now (unseen templates only, 18 Oct 2026)

| | Before public data | With public data |
|---|---|---|
| Training messages | 936 | 13,957 |
| Macro-F1 | 0.56 | **0.86** |
| Phishing recall | 0.88 | **0.92** |
| Suspicious recall | 0.03 | **0.81** |
| Zero-link phishing recall | 0.85 | **0.92** |

The `suspicious` class was broken because our synthetic data had almost no
examples of it. Real spam from the public datasets fixed it.

**The honest caveat:** every public phishing message is English. The language
experiment shows no significant change on our own Sinhala and Singlish rows
(McNemar p = 0.41) because our local test set has only 17 unseen templates.
That is too few to conclude anything, and it is the strongest argument for
collecting real local messages next. See `models/experiment_language.json`.

## 3. Run the app

```bash
uvicorn api.main:app --reload
```

- http://127.0.0.1:8000/ → the SMS inbox app (Demo mode shows "Under the hood")
- http://127.0.0.1:8000/docs → try every API endpoint

## 4. Who owns what

| Folder | Owner | What is inside |
|---|---|---|
| `detection/` | Sanmith | `preprocess.py` (undo tricks, language tag), `anatomy.py` (bank, action, contact, tactics), `synth.py`, `train.py`, `model.py`, `train_xlmr.py` (Colab) |
| `verify/` | Perera | `data/bank_registry.json`, `fact_check.py`, `explain.py`, `risk.py` |
| `warn/` | Rathnayake | `phrases.py` (EN/SI/Singlish), `composer.py`, `reliance.py`, `data/scenarios.json`, `static/` (web app) |
| `api/` | All | `main.py` (endpoints), `pipeline.py` (joins the three parts) |
| `shared/` | All | `contract.md` (the data format) and `examples/` |
| `data/seed/`, `data/synthetic/` | Sanmith | 36 hand-written + 900 synthetic messages (fictional banks) |

## 5. Next tasks before PP1

**Sanmith**
- Collect real donated SMS (consent first, remove names/numbers/OTPs, save in `data/real/` which Git ignores). This is now the single biggest blocker: 17 unseen local templates is not a test set.
- Label 300+ real messages with a teammate; write down Cohen's kappa.
- Run `detection/train_xlmr.py` on Colab and compare with the baseline.

**Perera**
- Replace the two fictional banks in `verify/data/bank_registry.json` with 5 real banks. Every fact needs a source URL and date.
- Try LIME: `pip install lime`, then call `/analyze` with `"explain_method": "lime"` and compare with occlusion.

**Rathnayake**
- Get a native speaker to check every Sinhala and Singlish line in `warn/phrases.py`, then set `NEEDS_REVIEW` to `False`.
- Pilot Study mode with 3–5 friends (participant IDs P01, P02, ...). Export logs with
  `python -c "from warn import reliance; reliance.export_csv('decisions.csv')"`.

## Team rules
1. Never work directly on `main`. Make a branch, push it, open a Pull Request.
2. Never commit real messages, study logs, passwords or keys (`data/real/`, `data/runtime/` and `.env` are ignored).
3. Don't rename or remove fields in `shared/contract.md` without telling everyone.
4. Write every data source in `docs/data_sources.md`.

## Honesty notes
- Banks, numbers and links in this repo are fictional.
- Sinhala and Singlish wording is a draft until a native speaker checks it.
- Synthetic data is for training only. Final results must use the real, hand-labelled gold test set.

## Evidence-aware research upgrade

The current implementation adds contextual action rules, incomplete/stale evidence handling,
abstention, three warning-study conditions and server-owned trial logging. Existing preliminary
classifier scores above predate these changes and are not evidence of their benefit.
See `docs/research_plan.md` for each member's question, implemented tools, limitations,
annotation format and experiments. Run `pytest -q` to check the implementation.

The live action extractor is still a rule baseline. Joint XLM-R/consistency training, real local
gold data, official-bank registry population, expert validation and formal user studies remain
research milestones. Fictional registry entries never supply verified contact buttons.
A model score is not a calibrated probability. Treat the original PDF as a concept overview;
its broad novelty assertions require literature review.

## Teammate quick start

Ask the repository owner to add your GitHub username as a collaborator to this
private repository. Until the research pull request is merged, clone its branch:

```bash
git clone --branch research/evidence-aware-actions https://github.com/dulaj69/banking-phish-nlp.git
cd banking-phish-nlp
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m detection.train
pytest -q
python run_app.py
```

This minimal setup trains from the included fictional seed and generated synthetic
examples. Its results differ from training with the optional public datasets.
For the public-data setup, follow section 2 above or run `python run_setup.py`.
Model weights, downloaded datasets, donated SMS and study logs are not uploaded.

Create your own branch before editing, for example `git switch -c feature/my-change`,
then push that branch and open a pull request. Folder ownership is listed above.
Read `docs/research_plan.md` and `shared/contract.md` before changing interfaces.

## Interactive research workbench

Open `/app/lab/` (now the home page) for three independent experiments:

1. **Action lab:** authored contrast cases, raw/normalised model outputs, keyword/contextual action comparisons and a downloadable diagnostic benchmark.
2. **Evidence lab:** controlled missing/stale/conflicting evidence, baseline risk comparisons, leave-one-fact-out sensitivity and minimum sufficient evidence sets.
3. **Human decisions:** simulated warning-policy comparisons and a server-assigned nine-trial rehearsal/pilot with an immediate no-advice transfer block.

The SMS demo remains at `/app/`. Read `docs/workbench_demo.md` before presenting.
These instruments make the research inspectable; they do not establish novelty or
replace real local data, expert validation, or an approved participant study.

## Public checking and practice

The root URL now opens `/app/`, a focused SMS checker. It calls the existing analysis pipeline without participant identity, study mode or planted errors. Results show the requested action, warning explanations, evidence availability and independent verification steps. No check history is stored. The awareness exercises run in browser memory only and are educational, not a validated assessment.

Research experiments remain at `/app/lab/`; the former phone-style study interface is preserved at `/app/study/`. These are separate interfaces, not access-controlled areas. Authentication, account-backed learning history and production deployment hardening remain future work. This release does not provide email-header or attachment scanning.
