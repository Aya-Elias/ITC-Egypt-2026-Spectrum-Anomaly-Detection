"""Create a timestamped SQLite database backup."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "database" / "spectrum.db"
BACKUP_DIR = ROOT / "data" / "backups"


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"Database not found: {DB}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"spectrum-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
    shutil.copy2(DB, target)
    print(f"Backup written: {target}")


if __name__ == "__main__":
    main()
