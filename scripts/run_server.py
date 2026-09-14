"""Run from a source checkout without an editable installation."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from stock_predictor.app import run


if __name__ == "__main__":
    run()
