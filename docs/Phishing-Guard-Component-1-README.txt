PHISHING GUARD - COMPONENT 1
Banking Smishing Detection and Action Extraction (J26-IT-442)
Owner: D J D Sanmith | IT23183940
Component branch: component1

Final-year research project. Component 1 analyses banking messages using a
character TF-IDF and logistic-regression classifier, alongside rule-based
extraction of requested actions, claimed banks, contacts and pressure tactics.
It supplies structured results to the explanation, verification and risk
component (Sonal), which feeds the warning and guidance component (Ravindi).

The component branches contain the integrated application so that each member
can run the system locally. This README focuses on Component 1.
The baseline is a research prototype; its score is not a verified probability
that a message is fraudulent.

1. WHAT YOU NEED
---------------
- Python (3.11 is a suggested setup version; verify dependencies and tests on
  your machine).
- Git.
- VS Code or another editor.
- Access to the private GitHub repository.
- Internet for cloning and installing dependencies.

A GPU is not required for the current TF-IDF/logistic-regression baseline.
The previously documented handoff was checked on macOS with Python 3.9.6;
Windows and other Python versions should run the tests locally.

2. FIRST-TIME SETUP
-------------------
Open a terminal and clone the component branch:

    git clone --branch component1 https://github.com/dulaj69/banking-phish-nlp.git
    cd banking-phish-nlp

Open this folder in VS Code. Select Terminal > New Terminal.
Run all commands below from the project root.

Mac / Linux:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt

Windows PowerShell:

    py -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt

The Windows commands below use the environment's Python directly, so activation
and PowerShell execution-policy changes are not needed.

If the project is already cloned, do not clone over it or discard local changes.
Commit or stash your work before switching branches. Use your own GitHub account;
never share passwords or access tokens.

3. TRAIN THE BASELINE MODEL
--------------------------
Mac / Linux (with the virtual environment activated):

    python -m detection.train

Windows:

    .venv\Scripts\python.exe -m detection.train

The script:
- Loads the seed dataset and synthetic examples.
- Generates synthetic examples if the synthetic file is missing.
- Applies text normalization.
- Evaluates a character TF-IDF + logistic-regression pipeline using a
  template-group train/test split.
- Fits a fresh deployment pipeline on all available examples.
- Saves models/detector.joblib and models/detector_results.json.

Minimal setup uses 36 seed messages and 900 synthetic messages (936 total).
If data/processed/public_v1.csv exists, the script also includes that data.
Check the actual inputs before reporting the dataset size.

Read the printed precision, recall and F1 results, but describe them as
preliminary: the minimal dataset is mostly synthetic. Reported evaluation
scores come from the held-out split, not an independent test of the deployment
model subsequently fitted on all examples. Class outputs and the weighted
score are uncalibrated.

Retraining replaces the saved model and report. Back up any result you need
before rerunning. Model files are ignored by Git; teammates recreate them locally.

4. RUN THE API AND WEBSITE
-------------------------
Mac / Linux:

    python -m uvicorn api.main:app --reload --port 8000

Windows:

    .venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000

Open:

    API documentation: http://127.0.0.1:8000/docs
    Message checker:  http://127.0.0.1:8000/app/

For Component 1, select POST /detect in the API documentation, click
"Try it out", enter the JSON below and click "Execute":

    {
      "text": "Demo Bank: reply with your OTP to unlock your account immediately.",
      "sender": "Demo Bank"
    }

This is a fictional example. Never enter an actual OTP or private account details.
The sender field is optional. Message text must contain 1-2,000 characters.

Useful endpoints:
- GET /health: check whether the server is running.
- GET /version: inspect the configured model version.
- POST /detect: analyse one message with Component 1.
- POST /predict_batch: analyse a list of messages.
- POST /analyze: run the integrated detection, verification and warning pipeline.

Example body for POST /predict_batch:

    {"texts": ["Please send your OTP.", "Never share your OTP."]}

Stop the server with Ctrl+C. Restart after replacing the saved model so the
process loads the new model. If port 8000 is occupied, select another port
and use that port in the browser URL.

5. WHAT COMPONENT 1 RETURNS
--------------------------
- Predicted class: legit, suspicious or phishing.
- Per-class model outputs.
- Weighted score: P(phishing) + 0.5 * P(suspicious), on a 0-1 scale.
- Heuristic language tag, normalized text and normalization changes.
- Requested actions and a primary action.
- Claimed bank and extracted links/phone numbers.
- Pressure tactics, such as urgency.
- Supporting text spans and extraction status.
- Model version and detection latency.

Classification is learned from data. The current public action extractor uses
programmed patterns and clause-level rules, not a trained transformer.
A bank mention is a claimed identity, not sender authentication.

Sonal owns model explanations/XAI, evidence verification and final risk.
Ravindi owns warning composition, guidance and learning behaviour.

6. RUN THE TESTS
---------------
Mac / Linux:

    python -m pytest -q

Windows:

    .venv\Scripts\python.exe -m pytest -q

Focused Component 1 checks (Mac / Linux):

    python -m pytest tests/test_preprocess.py tests/test_anatomy.py tests/test_api.py -q

The API tests include shared integration behaviour. Passing software tests does
not establish real-world detection accuracy or research novelty.

7. FOLDER MAP
-------------
detection/          Preprocessing, classification, action extraction and training.
data/seed/          Committed fictional starter examples.
data/synthetic/     Generated synthetic examples; ignored by Git.
models/             Locally generated model and reports; ignored by Git.
api/                Shared FastAPI application and integration.
research/           Experimental trainers, evaluations and research labs.
verify/             Sonal's explanation, verification and risk component.
warn/               Ravindi's warning logic and shared web interfaces.
tests/              Automated checks.
docs/               API contract, data-source records and research plans.

Main Component 1 files:
- detection/preprocess.py: normalization and heuristic language tagging.
- detection/anatomy.py: actions, tactics, contacts and bank mentions.
- detection/train.py: TF-IDF/logistic-regression training and evaluation.
- detection/model.py: load the saved model and produce detection results.
- detection/config.py: paths, class names and model version.

8. FUTURE RESEARCH
------------------
- Collect consented, redacted messages and independently annotate them.
- Compare the baseline with multilingual XLM-R classification/action prediction.
- Investigate action-object references across short banking conversations.
- Evaluate negation, ambiguity and Sinhala/Singlish robustness.
- Report false alarms, missed harmful requests, language-specific performance
  and latency on independent evaluation data.

Experimental transformer training code exists, but the website's current
classifier is TF-IDF + logistic regression. Conversation research changes may
exist only on the integration branch until reviewed and merged into component1.
Do not describe planned capabilities as deployed or proven superior.

9. TEAM RULES
-------------
- Use component1 as Sanmith's development base; do not work directly on main.
- Make a task branch, push it and open a Pull Request for teammate review.
- Coordinate edits to shared API fields; consult docs/api_contract.md.
- Record dataset sources and usage conditions in docs/data_sources.md.
- Never commit private messages, actual OTPs, passwords, tokens or keys.
- Keep data/real/, data/runtime/ and .env ignored by Git.
- Review staged changes before committing.
- Run relevant tests before requesting a merge.

10. DAILY GIT COMMANDS
---------------------
Start from component1 with a clean working tree:

    git switch component1
    git pull --ff-only origin component1
    git switch -c component1/my-task-name

After making your changes, replace the example file path below with the files
you actually changed:

    git status
    git add detection/anatomy.py
    git diff --cached
    git commit -m "Describe the Component 1 change"
    git push -u origin component1/my-task-name

Open a Pull Request targeting component1. Integrate reviewed component changes
into the shared integration branch using the team's agreed workflow.
