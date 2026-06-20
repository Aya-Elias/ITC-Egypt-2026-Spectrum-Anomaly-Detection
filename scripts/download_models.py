"""Validate that required model artifacts are present.

The trained model is intentionally not downloaded from an unknown external
source. Use this script in CI or setup flows to fail clearly when artifacts are
missing.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ROOT / "src" / "ai_model" / "saved_models" / "best_model.keras",
    ROOT / "src" / "ai_model" / "saved_models" / "norm_params.npy",
    ROOT / "src" / "ai_model" / "saved_models" / "model_report.json",
]


def main() -> None:
    missing = [str(path) for path in REQUIRED if not path.exists() or path.stat().st_size <= 1]
    if missing:
        raise SystemExit("Missing model artifacts:\n" + "\n".join(missing))
    print("All required model artifacts are present.")


if __name__ == "__main__":
    main()
