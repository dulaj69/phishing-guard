PHISHING GUARD - COMPONENT 2
Explainable AI, Evidence Verification and Risk Assessment (J26-IT-442)
Owner: Sonal Perera
Component branch: component2

Final-year research project. Component 2 explains the detector's output, checks
available bank-policy and contact evidence, and assesses the risk of the action
requested in a banking message. It receives structured detection results from
Sanmith (Component 1) and supplies explanations, evidence and risk information
to Ravindi's warning and guidance component (Component 3).

The component branches contain the integrated application so each member can
run the system locally. This README focuses on Sonal's responsibilities.
Current verification uses a local registry with fictional demonstration banks.
It does not authenticate SMS senders or verify a real bank through those fixtures.

1. WHAT YOU NEED
---------------
- Python (3.11 is a suggested setup version; verify dependencies and tests on
  your machine).
- Git.
- VS Code or another editor.
- Access to the private GitHub repository.
- Internet for cloning and installing dependencies.

No GPU is required for the current baseline and default explanations.
The earlier handoff was checked on macOS with Python 3.9.6. Run the tests on
Windows or other Python versions before relying on that setup.

2. FIRST-TIME SETUP
------------------
Clone Sonal's branch:

    git clone --branch component2 https://github.com/dulaj69/banking-phish-nlp.git
    cd banking-phish-nlp

Open this folder in VS Code, then select Terminal > New Terminal.
Run all commands from the project root.

Mac / Linux:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt

Windows PowerShell:

    py -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt

The Windows commands use the environment's Python directly; activation and
PowerShell execution-policy changes are not required.

If you already have a clone, preserve local changes before switching branches.
Use component2 exactly: the older Component-2 branch is a different branch.
Use your own GitHub credentials; never share passwords or access tokens.

3. PREPARE THE DETECTOR USED BY COMPONENT 2
-----------------------------------------
Component 2 needs Component 1's saved classifier to obtain scores and generate
perturbation explanations. Create it locally:

Mac / Linux:

    python -m detection.train

Windows:

    .venv\Scripts\python.exe -m detection.train

This trains Sanmith's TF-IDF/logistic-regression baseline, not a separate risk
model belonging to Sonal. It creates:

    models/detector.joblib
    models/detector_results.json

Minimal setup uses the seed and generated synthetic data. If the optional
processed public dataset exists, training includes it too. Results are
preliminary; the weighted score is not a calibrated probability of fraud.

Training replaces existing model/report files. Preserve any needed version
before retraining. A usable existing model can be reused without retraining.

4. RUN THE API AND WEBSITE
-------------------------
Mac / Linux:

    python -m uvicorn api.main:app --reload --port 8000

Windows:

    .venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000

Open:

    API documentation: http://127.0.0.1:8000/docs
    Message checker:  http://127.0.0.1:8000/app/

In the API documentation, select POST /verify, click "Try it out", paste the
following fictional example and click "Execute":

    {
      "text": "Demo Bank: reply with your OTP to unlock your account immediately.",
      "sender": "Demo Bank"
    }

The response contains both detection and verification results. Do not enter
real OTPs, account details or private messages in demonstrations.

Useful endpoints:
- GET /health: check whether the API is running.
- POST /detect: inspect Sanmith's upstream detection output.
- POST /verify: run detection plus Sonal's verification with default occlusion.
- POST /analyze: run the integrated pipeline and select an explanation method.

Stop the server with Ctrl+C. Restart after replacing the model or cached registry
so the process loads the changed resources. If port 8000 is occupied, select
another port and use it in the browser URL.

5. HOW THE XAI PART WORKS
------------------------
Default method: word removal (occlusion).

The explainer calculates the original weighted model score, removes one
whitespace-separated word at a time, and scores each modified message.

    Word contribution = original score - score after removing that word

It returns up to six positive contributions. These show which removals reduced
the model score; they are not independent proof of fraud, and they do not
necessarily add up to the original score.

Optional method: LIME.

Install it separately if you want to use the implemented LIME path:

Mac / Linux:

    python -m pip install lime

Windows:

    .venv\Scripts\python.exe -m pip install lime

Restart the server, then use POST /analyze with:

    {
      "text": "Demo Bank: reply with your OTP immediately.",
      "sender": "Demo Bank",
      "language": "en",
      "explain_method": "lime",
      "study_mode": false
    }

POST /verify does not expose the explanation-method selector; use /analyze for
this example. Change explain_method to "occlusion" for the default method.

LIME generates perturbed text samples and fits a local approximation of the
weighted score. The current implementation uses 500 samples and a fixed random
seed. If LIME cannot be imported, the code falls back to occlusion. A successful
response alone therefore does not prove LIME was used.

Current status:
- Occlusion: implemented and default.
- LIME: implemented as an optional method.
- SHAP: listed in optional dependencies, but not implemented in the live explainer.
- Integrated Gradients: future work, not an implemented explanation path.

Installing a library alone does not activate a new explanation method.

6. HOW EVIDENCE VERIFICATION WORKS
--------------------------------
The local registry is:

    verify/data/bank_registry.json

The checker uses Sanmith's extracted bank claim, contacts and actions to inspect
supported bank-policy rules and contact fields. Checks return pass, fail or
unknown, with relevant source metadata.

Key behaviour:
- Source metadata includes a URL and checked date.
- A provisional 180-day freshness policy is applied.
- Missing or stale evidence cannot be treated as current verified support.
- An unmatched contact is not automatically contradictory when coverage is partial.
- A matching public detail does not authenticate the sender.
- The checker does not browse the bank website live on each request.
- Fictional records cannot supply real verified-contact buttons.

For real registry entries, research official sources, record field-specific
provenance and dates, and review the entries. Do not relabel fictional records
as real. Do not assume a published contact list is exhaustive.

7. HOW RISK ASSESSMENT WORKS
---------------------------
Risk assessment is currently a programmed policy, not a separately trained ML
classifier. It combines:

    Model score + requested-action harm + evidence + extraction uncertainty

Current score bands:
- Low: score below 0.40.
- Medium: score from 0.40 to below 0.75.
- High: score at least 0.75.

The policy combines the band and action harm using a matrix to produce Low,
Medium, High or Critical risk. Contradictory evidence can raise the tier, capped
at Critical. Credential-sharing requests have a minimum High tier. Matching
public details never lower the tier automatically.

Certain unresolved cases return an abstention flag, indicating that the system
cannot provide a firm verdict. The policy also checks whether supporting
evidence concerns the requested action, rather than an unrelated copied detail.

Thresholds, harm values and matrix entries are provisional design choices.
They require evaluation against independent expert judgements.

8. INPUTS, OUTPUTS AND TEAM CONNECTIONS
--------------------------------------
Inputs from Sanmith:
- Normalized message and weighted model score.
- Primary action and action uncertainty.
- Claimed bank, extracted contacts and other message anatomy.

Sonal's verification result contains:
- fact_checks: outcomes, details and source metadata.
- explanation: words and positive attribution weights.
- risk: final tier, score band, harm, adjustments, reasons, evidence quality,
  abstention and policy version.
- official_contact: an eligible registry contact, or null when unavailable.

Ravindi uses these results to select and compose warnings and guidance.
Model explanation answers "Why did the classifier react?" Evidence verification
answers "What supports or contradicts the requested action?" These are different.

9. RUN THE TESTS
---------------
Mac / Linux:

    python -m pytest -q

Focused Component 2 and API checks:

    python -m pytest tests/test_verify.py tests/test_api.py -q

Windows:

    .venv\Scripts\python.exe -m pytest -q

Passing software tests does not demonstrate real-world accuracy, explanation
faithfulness, calibrated risk or research novelty.

10. FOLDER MAP
--------------
verify/explain.py             Occlusion and optional LIME explanations.
verify/fact_check.py          Registry checks, provenance and contact eligibility.
verify/risk.py                Risk matrix, evidence adjustments and abstention.
verify/service.py             Combines explanations, verification and risk.
verify/data/bank_registry.json  Local bank-policy/contact registry.
detection/                   Sanmith's upstream model and extractors.
api/                         Shared FastAPI routes and pipeline.
research/lab/evidence.py     Evidence research-workbench logic.
warn/                        Ravindi's warning logic and shared web interfaces.
tests/                       Automated tests.
docs/                        API contract, data sources and research plans.
models/                      Locally generated detector files; ignored by Git.

New action-destination binding experiments may be present on the integration
branch before they reach component2. Check branch contents before claiming an
experimental feature is available in a teammate's checkout.

11. FUTURE RESEARCH
-------------------
- Implement and compare SHAP with LIME and occlusion.
- Evaluate explanation faithfulness, stability and runtime.
- Investigate agreement/conflict between model influence, action context and
  independent verification evidence.
- Evaluate risk decisions under missing, stale and conflicting evidence.
- Study action-specific verification steps and unnecessary-check reduction.
- Validate risk thresholds with independent expert-labelled cases.

Using SHAP or LIME alone is not a novelty claim. The proposed contribution must
be supported by comparative evaluation of the evidence-aware explanation and
risk method. Proposed features and benefits are not established results.

12. TEAM RULES AND DAILY GIT COMMANDS
------------------------------------
- Use component2 as Sonal's development base; never work directly on main.
- Coordinate shared API-field changes using docs/api_contract.md.
- Record evidence/data sources in docs/data_sources.md and registry metadata.
- Never commit private messages, study logs, passwords or tokens.
- Keep data/real/, data/runtime/ and .env ignored by Git.
- Review staged changes and run relevant tests before requesting a merge.

Start with a clean working tree:

    git switch component2
    git pull --ff-only origin component2
    git switch -c component2/my-task-name

After editing, stage only intended files. Replace the example path as needed:

    git status
    git add verify/explain.py
    git diff --cached
    git commit -m "Describe the Component 2 change"
    git push -u origin component2/my-task-name

Open a Pull Request targeting component2 and request teammate review. Integrate
approved changes into the shared integration branch through the agreed workflow.
