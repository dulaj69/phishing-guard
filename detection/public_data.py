"""Turn the public datasets into ONE clean file with our labels.

Run:  python -m detection.public_data   (after python -m detection.get_datasets)
Out:  data/processed/public_v1.csv      (Git ignores it, because of licences)

Our labels:
  legit       normal messages (ham, real bank alerts)
  suspicious  unwanted or possibly harmful, but not clear phishing (spam, ads, job/romance lures)
  phishing    tries to steal money, credentials or data (smishing)

Sources and how each label was mapped (write this in the thesis):
  smishtank  Timko & Rahman 2024. All messages are user-reported smishing.
             Category -> phishing: Account Alert, Delivery, Prize/Contest, Finance/Crypto,
                                   Lawsuits/Settlements, Loans/Credit
             Category -> suspicious: Advertisement, Job Advertisement, Wrong Number/Romance, Other
  mendeley   Mishra & Soni 2022. ham -> legit, spam -> suspicious, smishing -> phishing
  exais      Abayomi-Alli et al. 2016 (Nigeria). HAM -> legit, SPAM -> suspicious
  uci        Almeida et al. 2011. ham -> legit, spam -> suspicious
             (Mendeley re-labelled many UCI messages; duplicates keep the Mendeley label)
  indian     Revised Indian dataset (Hindi / Telugu / code-mixed). ham -> legit, spam -> suspicious

NOT used, and why:
  Combined-Labeled (84k)  labelled by keyword matching, so labels are unreliable
  SMS Gateway / Spam Hunter / NUS  no labels
  Kor-Smishing  Korean, not our languages
"""
import hashlib
import re

import pandas as pd

from detection.config import ROOT

EXTERNAL = ROOT / "data" / "external"
REFINED = EXTERNAL / "smish_dt" / "Refined Datasets"
OUT = ROOT / "data" / "processed" / "public_v1.csv"

SMISHTANK_PHISHING = {"Account Alert", "Delivery", "Prize/Contest", "Finance/Crypto",
                      "Lawsuits/Settlements", "Loans/Credit"}
INDIAN_LANG = {1: "en", 2: "hi-mixed", 3: "te", 4: "te-roman"}


def _clean_text(s):
    s = str(s).replace("\t", " ").strip()
    return re.sub(r"\s+", " ", s)


def dedup_key(text):
    """Same message with different numbers/case/punctuation = duplicate."""
    t = re.sub(r"\d", "0", text.lower())
    t = re.sub(r"[^\w]+", "", t)
    return hashlib.md5(t.encode("utf-8")).hexdigest()


def near_dup_group(text):
    """Messages from the same template (same first 40 characters) share a group,
    so a train/test split never puts the same template on both sides."""
    t = re.sub(r"\d", "0", text.lower())
    t = re.sub(r"[^\w ]+", "", t)
    return "pub-" + hashlib.md5(t[:40].encode("utf-8")).hexdigest()[:12]


def load_smishtank():
    d = pd.read_csv(REFINED / "Refined_Smishtank_Dataset.csv", low_memory=False)
    text = d["MainText"].fillna(d["Fulltext"])
    cat = d["Message Categories"].fillna("Other")
    label = cat.map(lambda c: "phishing" if c in SMISHTANK_PHISHING else "suspicious")
    return pd.DataFrame({"text": text, "label": label, "language": "en", "source": "smishtank",
                         "category": cat})


def load_mendeley():
    d = pd.read_csv(REFINED / "Refined_Mendeley_Smishing_Dataset.csv")
    label = d["LABEL"].str.lower().map({"ham": "legit", "spam": "suspicious", "smishing": "phishing"})
    return pd.DataFrame({"text": d["TEXT"], "label": label, "language": "en", "source": "mendeley",
                         "category": d["LABEL"].str.lower()})


def load_exais():
    d = pd.read_csv(REFINED / "Refined_ExAIS_SMS_Spam_Dataset.csv")
    label = d["Label"].str.upper().map({"HAM": "legit", "SPAM": "suspicious"})
    return pd.DataFrame({"text": d["Message"], "label": label, "language": "en", "source": "exais",
                         "category": d["Label"].str.lower()})


def load_uci():
    d = pd.read_csv(REFINED / "Refined_UCI_ML_Repo_Dataset.csv")
    label = d["label"].map({"ham": "legit", "spam": "suspicious"})
    return pd.DataFrame({"text": d["message"], "label": label, "language": "en", "source": "uci",
                         "category": d["label"]})


def load_indian():
    base = EXTERNAL / "indian" / "Presentation"
    csv = base / "revisedindiandataset.csv"
    if csv.exists():
        d = pd.read_csv(csv, encoding_errors="replace")
    else:
        # .xls needs xlrd. Without it, convert once with LibreOffice:
        #   soffice --headless --convert-to csv --outdir . revisedindiandataset.xls
        d = pd.read_excel(base / "revisedindiandataset.xls")   # needs: pip install xlrd
    d = d[d["code"].isin(INDIAN_LANG)]
    label = d["label"].str.lower().map({"ham": "legit", "spam": "suspicious"})
    return pd.DataFrame({"text": d["msg"], "label": label, "language": d["code"].map(INDIAN_LANG),
                         "source": "indian", "category": d["label"]})


# Order matters: when two sources have the same message, the earlier one wins.
LOADERS = [load_smishtank, load_mendeley, load_exais, load_uci, load_indian]


def build():
    parts, skipped = [], []
    for loader in LOADERS:
        try:
            part = loader()
        except FileNotFoundError as e:
            print(f"  skipped {loader.__name__}: {e.filename} not found")
            continue
        except Exception as e:                      # one broken source must not kill the rest
            print(f"  SKIPPED {loader.__name__}: {type(e).__name__}: {e}")
            skipped.append(loader.__name__)
            continue
        print(f"  {loader.__name__:15s} {len(part):6d} rows")
        parts.append(part)
    if not parts:
        raise SystemExit("No datasets found. Run: python -m detection.get_datasets")
    data = pd.concat(parts, ignore_index=True)
    data["text"] = data["text"].map(_clean_text)
    data = data[(data["text"].str.len() >= 8) & data["label"].notna()]
    data["dedup"] = data["text"].map(dedup_key)
    before = len(data)
    data = data.drop_duplicates("dedup", keep="first")
    print(f"  removed {before - len(data)} duplicates")
    data["template_id"] = data["text"].map(near_dup_group)
    data["id"] = data["source"] + "-" + data.index.astype(str)
    data["channel"] = "sms"
    cols = ["id", "text", "label", "language", "source", "category", "template_id", "channel"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data[cols].to_csv(OUT, index=False)
    print(f"\nWrote {len(data)} messages to {OUT}")
    if skipped:
        print(f"WARNING: these sources were skipped and are NOT in the file: {', '.join(skipped)}")
    print(data.groupby(["source", "label"]).size().unstack(fill_value=0))
    return data[cols]


if __name__ == "__main__":
    build()
