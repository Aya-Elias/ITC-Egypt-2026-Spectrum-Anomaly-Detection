"""Initialize the local SADAR SQLite database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "database" / "spectrum.db"
MIGRATION = ROOT / "src" / "database" / "migrations" / "001_initial.sql"


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(MIGRATION.read_text(encoding="utf-8"))
    print(f"Initialized database: {DB_PATH}")


if __name__ == "__main__":
    main()
