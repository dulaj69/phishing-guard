# Team handoff for the progress presentation

Prepared 20 October 2026. All three component branches start from the same integrated version and contain the entire working application. They are development ownership boundaries, not three separate applications.

| Branch | Owner | Primary files |
|---|---|---|
| `component1` | Sanmith | `detection/`, `research/lab/robustness.py`, action fixtures and corresponding tests |
| `component2` | Sonal Perera | `verify/`, `research/lab/evidence.py`, corresponding tests |
| `component3` | Ravindi Rathnayake | `warn/composer.py`, `warn/phrases.py`, `warn/reliance.py`, `research/lab/pilot.py`, `research/lab/learning.py`, corresponding views/tests |

Integration branch: `research/evidence-aware-actions`. Presentation snapshot tag: `pp1-presentation-2026-10-20`. `main` is still the starter and should not be used for this presentation. The older remote `Component-2` remains unchanged; it is different from `component2`.

## 1. Repository access

This repository is private. Each teammate needs their own GitHub account with collaborator access and must accept the invitation. Authenticate through their own GitHub credentials or credential manager; never share the owner's token or password. Email addresses alone do not prove that an invitation has been accepted.

## 2. Clone the correct branch

Choose ONE command for your role:

```sh
# Sanmith
 git clone --branch component1 https://github.com/dulaj69/banking-phish-nlp.git
# Sonal
 git clone --branch component2 https://github.com/dulaj69/banking-phish-nlp.git
# Ravindi
 git clone --branch component3 https://github.com/dulaj69/banking-phish-nlp.git
```

Then `cd banking-phish-nlp`. If you already have a clone, commit or stash your work before switching, then run `git fetch origin` and `git switch --track origin/component2` (substitute your assigned branch; if it already exists locally, use `git switch component2`). Do not discard changes to make switching work.

## 3. Minimal local setup

The handoff check uses Python 3.9.6 on macOS. Other platforms/Python versions must run the checks below; no Windows verification is claimed. The basic requirements are intentionally separate from optional transformer/Colab dependencies.

macOS/Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m detection.train
python -m pytest -q
python run_app.py
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m detection.train
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe run_app.py
```

Using the virtual-environment interpreter directly avoids needing to change PowerShell execution policy. Python itself must already be installed.

The dependency installation needs internet. Minimal training uses the committed fictional seed data and generates synthetic examples locally. It does not need public-data downloads. Avoid `run_setup.py` immediately before the viva: that optional route downloads public datasets and retrains a different model.

`run_app.py` selects a free local port starting at 8000 and prints/opens the checker URL. Use the printed port, not a hard-coded assumption. The application uses localhost; each laptop runs its own server.

- `/app/`: anonymous checker and all three component outputs.
- `/app/workspace/`: individual account creation/login, learning sessions.
- `/app/lab/`: signed-in research experiments.
- `/docs`: API documentation.

Create a local practice account using a pseudonymous username and a passphrase of at least 15 characters. Accounts, logs and learning history are local to that machine; they are not copied through GitHub. Use rehearsal mode for viva practice, not a consented participant session.

## 4. What Git includes and excludes

Source, tests, fictional seed examples, registry fixtures and documentation are versioned. `.venv`, model weights, synthetic output, downloaded/public data, private messages, account databases, participant logs and secrets are excluded. A successful clone is not a trained application until the training step finishes.

Do not commit real SMS, participant records, credentials or local account databases. Do not copy the owner's working environment as your setup method. A fresh trained baseline may differ from a model trained with optional public data or another dependency version.

For a consistent demonstration, use the same setup path, record `python --version`, `python -m pip freeze`, and the model fingerprint:

```sh
python -c "from research.lab.robustness import fingerprint; print(fingerprint())"
```

The version string alone is not an artifact checksum. If outputs differ, inspect training data and dependencies instead of silently quoting another member's numbers. A local result report in `models/detector_results.json` is preliminary and mostly synthetic for this minimal setup.

## 5. Safe workflow before the viva

Keep the presentation snapshot stable. Rehearse exact inputs and record actual limitations. Any fixes should be small, reviewed, tested, and integrated before everyone updates. Avoid independent model changes in the final rehearsal window.

Each person works on their assigned component branch, commits named files and pushes that branch. Open a pull request with base `research/evidence-aware-actions`. The integration branch is where the team verifies the complete application before merging. Git merges do not automatically update the other component branches.

To bring integrated updates into a component branch after saving your work:

```sh
git fetch origin
git merge origin/research/evidence-aware-actions
python -m pytest -q
# Push your current assigned branch only after resolving any conflicts.
git push
```

Coordinate edits to `api/`, `shared/contract.md`, requirements, account code and common frontend renderers such as `warn/static/analysis.js`. Owning a component does not mean claiming all historical code as individual authorship. Branches preserve shared history; new commits and experiments document subsequent contributions.

## 6. Presentation recovery

To make a separate copy of the frozen source without resetting ongoing work:

```sh
git clone --branch pp1-presentation-2026-10-20 https://github.com/dulaj69/banking-phish-nlp.git banking-phish-viva
```

A tag checkout is detached. Use it for rehearsal/recovery; create a branch before editing. Repeat environment setup and training because the tag freezes source, not ignored datasets, model files or account state.

Keep a recorded demonstration as a fallback. Do not present synthetic experiments or your own rehearsal logs as participant findings.
