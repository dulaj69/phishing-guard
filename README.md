# Banking Smishing Detection (J26-IT-442)

Final-year research project. This repo holds the detection part (model + API).
Right now it contains a **small test model** so the whole team can build against a working API.

## 1. What you need
- Python 3.11 or newer
- Git
- VS Code (or any editor)

## 2. First-time setup
```bash
git clone <your-repo-url>
cd banking-phish-nlp

python -m venv .venv
# Windows:      .venv\Scripts\activate
# Mac / Linux:  source .venv/bin/activate

pip install -r requirements.txt
```

## 3. Train the test model
```bash
python -m src.train_baseline
```
It prints some scores. Ignore them: the data is tiny. A file `models/baseline.joblib` is created.

## 4. Run the API
```bash
uvicorn api.main:app --reload
```
Open http://127.0.0.1:8000/docs in your browser. Click `POST /predict`, then "Try it out",
paste a message, and press Execute.

## 5. Run the tests
```bash
pytest
```

## Folder map
| Folder | What is inside |
|--------|----------------|
| `data/seed/` | The small hand-made starter dataset |
| `src/` | Model training and prediction code |
| `api/` | The web API other members call |
| `tests/` | Automatic checks |
| `docs/` | API contract and data source log |
| `notebooks/` | Experiments (Jupyter) |

## Team rules
1. Never work directly on `main`. Make a branch, push it, open a Pull Request, and let a teammate check it.
2. Never commit real messages, passwords, or keys. `data/real/` and `.env` are ignored by Git, keep it that way.
3. Do not change the API fields without telling everyone (see `docs/api_contract.md`).
4. Write every data source in `docs/data_sources.md`.

## Daily Git commands
```bash
git checkout -b my-task-name      # start a branch
git add .
git commit -m "short message"
git push -u origin my-task-name   # then open a Pull Request on GitHub
```
