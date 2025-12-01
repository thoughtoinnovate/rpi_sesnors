"""Scheduler configuration persistence helpers."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from aqi import db
from aqi.schedule_defs import (
    normalize_frequency,
    normalize_retention,
    normalize_type,
    parse_bool,
)


def _row_to_dict(row) -> Dict[str, Any]:
    keys = row.keys()
    return {
        "id": row["id"],
        "name": row["name"],
        "location": row["location"],
        "type": row["type"],
        "frequency_label": row["frequency_label"],
        "frequency_seconds": row["frequency_seconds"],
        "retention_label": row["retention_label"],
        "retention_seconds": row["retention_seconds"],
        "enabled": bool(row["enabled"]),
        "powersave": bool(row["powersave"]) if "powersave" in keys else False,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_configs() -> List[Dict[str, Any]]:
    conn = db.connect()
    rows = conn.execute(
        f"SELECT * FROM {db.SCHEMA_NAME}.schedule_configs ORDER BY id"
    ).fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def get_config_by_id(config_id: int) -> Optional[Dict[str, Any]]:
    conn = db.connect()
    row = conn.execute(
        f"SELECT * FROM {db.SCHEMA_NAME}.schedule_configs WHERE id = ?",
        (config_id,),
    ).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def get_config_by_name(name: str) -> Optional[Dict[str, Any]]:
    conn = db.connect()
    row = conn.execute(
        f"SELECT * FROM {db.SCHEMA_NAME}.schedule_configs WHERE name = ?",
        (name,),
    ).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def create_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "name" not in payload:
        raise ValueError("Missing required field 'name'.")
    if "location" not in payload:
        raise ValueError("Missing required field 'location'.")
    if "frequency" not in payload:
        raise ValueError("Missing required field 'frequency'.")
    if "type" not in payload:
        raise ValueError("Missing required field 'type'.")
    freq_label, freq_seconds = normalize_frequency(payload["frequency"])
    reading_type = normalize_type(payload["type"])
    retention_label, retention_seconds = normalize_retention(payload.get("retention"))
    enabled = bool(payload.get("enabled", True))
    powersave = parse_bool(payload.get("powersave", False))
    now = datetime.now(timezone.utc).isoformat()
    conn = db.connect()
    try:
        conn.execute(
            f"""
        INSERT INTO {db.SCHEMA_NAME}.schedule_configs
        (name, location, type, frequency_label, frequency_seconds,
         retention_label, retention_seconds, enabled, powersave, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["name"],
            payload["location"],
            reading_type,
            freq_label,
            freq_seconds,
            retention_label,
            retention_seconds,
            1 if enabled else 0,
            1 if powersave else 0,
            now,
            now,
        ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.close()
        raise ValueError("Config name must be unique.") from exc
    config = conn.execute(
        f"SELECT * FROM {db.SCHEMA_NAME}.schedule_configs WHERE name = ?",
        (payload["name"],),
    ).fetchone()
    conn.close()
    return _row_to_dict(config)


def update_config(config_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    existing = get_config_by_id(config_id)
    if not existing:
        raise KeyError("Config not found")
    freq_label = existing["frequency_label"]
    freq_seconds = existing["frequency_seconds"]
    reading_type = existing["type"]
    retention_label = existing["retention_label"]
    retention_seconds = existing["retention_seconds"]
    enabled = existing["enabled"]
    location = existing["location"]
    name = existing["name"]
    powersave = existing.get("powersave", False)

    if "name" in payload:
        name = payload["name"]
    if "location" in payload:
        location = payload["location"]
    if "frequency" in payload:
        freq_label, freq_seconds = normalize_frequency(payload["frequency"])
    if "type" in payload:
        reading_type = normalize_type(payload["type"])
    if "retention" in payload:
        retention_label, retention_seconds = normalize_retention(payload["retention"])
    if "enabled" in payload:
        enabled = bool(payload["enabled"])
    if "powersave" in payload:
        powersave = parse_bool(payload["powersave"])

    now = datetime.now(timezone.utc).isoformat()
    conn = db.connect()
    try:
        conn.execute(
            f"""
        UPDATE {db.SCHEMA_NAME}.schedule_configs
        SET name = ?, location = ?, type = ?, frequency_label = ?, frequency_seconds = ?,
            retention_label = ?, retention_seconds = ?, enabled = ?, powersave = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            name,
            location,
            reading_type,
            freq_label,
            freq_seconds,
            retention_label,
            retention_seconds,
            1 if enabled else 0,
            1 if powersave else 0,
            now,
            config_id,
        ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.close()
        raise ValueError("Config name must be unique.") from exc
    row = conn.execute(
        f"SELECT * FROM {db.SCHEMA_NAME}.schedule_configs WHERE id = ?",
        (config_id,),
    ).fetchone()
    conn.close()
    return _row_to_dict(row)


def delete_config(config_id: int) -> None:
    conn = db.connect()
    cur = conn.execute(
        f"DELETE FROM {db.SCHEMA_NAME}.schedule_configs WHERE id = ?",
        (config_id,),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise KeyError("Config not found")
