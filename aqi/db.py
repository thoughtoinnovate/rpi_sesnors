"""Shared SQLite helpers for the AQI project."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_NAME = "aqi"
DB_FILENAME = "sensor.db"
REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / DB_FILENAME


def connect(check_same_thread: bool = True) -> sqlite3.Connection:
    """Return a connection with the AQI schema attached and ensured."""
    conn = sqlite3.connect(":memory:", check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    conn.execute(f"ATTACH DATABASE ? AS {SCHEMA_NAME}", (str(DB_PATH),))
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.schedule_readings (
            timestamp TEXT NOT NULL,
            location TEXT NOT NULL,
            type TEXT CHECK(type IN ('standard','atmospheric')) NOT NULL,
            pm1 INTEGER NOT NULL,
            pm2_5 INTEGER NOT NULL,
            pm10 INTEGER NOT NULL,
            particles_0_3um INTEGER NOT NULL DEFAULT 0,
            particles_0_5um INTEGER NOT NULL DEFAULT 0,
            particles_1_0um INTEGER NOT NULL DEFAULT 0,
            particles_2_5um INTEGER NOT NULL DEFAULT 0,
            particles_5_0um INTEGER NOT NULL DEFAULT 0,
            particles_10um INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    _ensure_schedule_columns(conn)
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.schedule_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            location TEXT NOT NULL,
            type TEXT CHECK(type IN ('standard','atmospheric')) NOT NULL,
            frequency_label TEXT NOT NULL,
            frequency_seconds INTEGER NOT NULL,
            retention_label TEXT,
            retention_seconds INTEGER,
            enabled INTEGER NOT NULL DEFAULT 1,
            powersave INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    _ensure_config_columns(conn)
    conn.commit()


def _ensure_schedule_columns(conn: sqlite3.Connection) -> None:
    required_columns = {
        "particles_0_3um": "INTEGER NOT NULL DEFAULT 0",
        "particles_0_5um": "INTEGER NOT NULL DEFAULT 0",
        "particles_1_0um": "INTEGER NOT NULL DEFAULT 0",
        "particles_2_5um": "INTEGER NOT NULL DEFAULT 0",
        "particles_5_0um": "INTEGER NOT NULL DEFAULT 0",
        "particles_10um": "INTEGER NOT NULL DEFAULT 0",
    }
    existing = {
        row["name"]
        for row in conn.execute(f"PRAGMA {SCHEMA_NAME}.table_info(schedule_readings)")
    }
    for column, ddl in required_columns.items():
        if column not in existing:
            conn.execute(
                f"ALTER TABLE {SCHEMA_NAME}.schedule_readings ADD COLUMN {column} {ddl}"
            )


def _ensure_config_columns(conn: sqlite3.Connection) -> None:
    required_columns = {
        "powersave": "INTEGER NOT NULL DEFAULT 0",
    }
    existing = {
        row["name"]
        for row in conn.execute(f"PRAGMA {SCHEMA_NAME}.table_info(schedule_configs)")
    }
    for column, ddl in required_columns.items():
        if column not in existing:
            conn.execute(
                f"ALTER TABLE {SCHEMA_NAME}.schedule_configs ADD COLUMN {column} {ddl}"
            )
