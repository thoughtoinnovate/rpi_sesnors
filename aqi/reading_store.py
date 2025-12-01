"""Helper functions to read AQI samples from SQLite."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from aqi import db


def list_readings(
    limit: int = 100,
    location: Optional[str] = None,
    reading_type: Optional[str] = None,
    since: Optional[str] = None,
) -> List[Dict[str, Any]]:
    limit = max(1, min(limit, 1000))
    if since:
        datetime.fromisoformat(since.replace("Z", "+00:00"))
    conn = db.connect()
    clauses = []
    params: List[Any] = []
    if location:
        clauses.append("location = ?")
        params.append(location)
    if reading_type:
        clauses.append("type = ?")
        params.append(reading_type)
    if since:
        clauses.append("timestamp >= ?")
        params.append(since)
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"""
        SELECT timestamp, location, type, pm1, pm2_5, pm10,
               particles_0_3um, particles_0_5um, particles_1_0um,
               particles_2_5um, particles_5_0um, particles_10um
        FROM {db.SCHEMA_NAME}.schedule_readings
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (*params, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_readings(before: Optional[str] = None, location: Optional[str] = None) -> int:
    clauses = []
    params: list[Any] = []
    if before:
        datetime.fromisoformat(before.replace("Z", "+00:00"))
        clauses.append("timestamp < ?")
        params.append(before)
    if location:
        clauses.append("location = ?")
        params.append(location)
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    conn = db.connect()
    cur = conn.execute(
        f"DELETE FROM {db.SCHEMA_NAME}.schedule_readings {where_clause}",
        tuple(params),
    )
    conn.commit()
    conn.close()
    return cur.rowcount
