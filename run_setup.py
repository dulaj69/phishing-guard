"""One-press setup: download the public datasets, build them, retrain the model.

In VS Code: open this file and press the ▶ Run button (top right of the editor).
Takes a few minutes. Safe to run again -- already-downloaded data is reused.

After this finishes, open run_app.py and press ▶ to see the app.
"""
import subprocess
import sys


def step(number, title, fn):
    print(f"\n{'=' * 58}\n  STEP {number}: {title}\n{'=' * 58}")
    fn()


def ensure_xlrd():
    """One of the public datasets is an old .xls file, which needs xlrd."""
    try:
        import xlrd  # noqa: F401
        print("xlrd already installed.")
    except ImportError:
        print("Installing xlrd (needed for the Indian dataset) ...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "xlrd"], check=False)


def main():
    from detection import get_datasets, public_data, train

    step(1, "Download the public datasets (about 34,000 files, be patient)",
         get_datasets.main)
    step(2, "Make sure xlrd is available", ensure_xlrd)
    step(3, "Build the combined dataset -> data/processed/public_v1.csv",
         public_data.build)
    step(4, "Train the model on everything", train.train)

    print(f"\n{'=' * 58}\n  Done. Now open run_app.py and press the Run button.\n{'=' * 58}")


if __name__ == "__main__":
    main()
