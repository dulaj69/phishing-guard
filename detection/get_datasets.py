"""Download the public datasets into data/external/ (Git ignores this folder).

Run on a computer with internet:   python -m detection.get_datasets
Then build the combined file:      python -m detection.public_data

We do NOT commit these datasets to our repo: each has its own licence.
Cite every one we use (see docs/data_sources.md).
"""
import subprocess
from pathlib import Path

from detection.config import ROOT

EXTERNAL = ROOT / "data" / "external"

REPOS = {
    # Smishing Data Hub from Pritom et al., "SMS Phishing Attacks and Defenses: A Systematic Review" (2026).
    # Contains cleaned copies of Smishtank, Mendeley smishing, ExAIS and UCI.
    "smish_dt": "https://github.com/MarazMia/SMISH_DT.git",
    # Indian multilingual SMS spam (Hindi / Telugu / code-mixed).
    "indian": "https://github.com/shshnk158/Multilingual-SMS-spam-detection-using-RNN.git",
}


def main():
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    for name, url in REPOS.items():
        target = EXTERNAL / name
        if target.exists():
            print(f"{name}: already downloaded")
            continue
        print(f"{name}: downloading {url}")
        subprocess.run(["git", "clone", "--depth", "1", url, str(target)], check=True)
    print("Done. Now run: python -m detection.public_data")


if __name__ == "__main__":
    main()
