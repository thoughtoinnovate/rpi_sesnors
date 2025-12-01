"""Shared constants and validators for scheduler configuration."""
from __future__ import annotations

from typing import Dict, Tuple

FREQUENCY_SECONDS: Dict[str, int] = {
    "5s": 5,
    "15s": 15,
    "30s": 30,
    "1m": 60,
    "5m": 5 * 60,
    "15m": 15 * 60,
    "30m": 30 * 60,
    "1h": 60 * 60,
    "2h": 2 * 60 * 60,
    "4h": 4 * 60 * 60,
}

TYPE_MAP = {
    "standard": "standard",
    "std": "standard",
    "atmospheric": "atmospheric",
    "atm": "atmospheric",
}

RETENTION_SECONDS: Dict[str, int] = {
    "10s": 10,
    "30s": 30,
    "1m": 60,
    "5m": 5 * 60,
    "15m": 15 * 60,
    "30m": 30 * 60,
    "1h": 60 * 60,
    "6h": 6 * 60 * 60,
    "12h": 12 * 60 * 60,
    "1d": 24 * 60 * 60,
    "3d": 3 * 24 * 60 * 60,
    "7d": 7 * 24 * 60 * 60,
    "30d": 30 * 24 * 60 * 60,
    "90d": 90 * 24 * 60 * 60,
}


def parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    val = str(value).strip().lower()
    if val in ("1", "true", "yes", "on"):
        return True
    if val in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"Cannot parse boolean from '{value}'")


def normalize_frequency(value: str) -> Tuple[str, int]:
    key = value.lower()
    if key not in FREQUENCY_SECONDS:
        raise ValueError(f"Unsupported frequency '{value}'. Choose from {', '.join(FREQUENCY_SECONDS)}.")
    return key, FREQUENCY_SECONDS[key]


def normalize_type(value: str) -> str:
    key = value.lower()
    if key not in TYPE_MAP:
        raise ValueError("Type must be 'standard' or 'atmospheric'.")
    return TYPE_MAP[key]


def normalize_retention(value: str | None) -> Tuple[str | None, int | None]:
    if value is None:
        return None, None
    key = value.lower()
    if key in ("none", "off", "infinite"):
        return None, None
    if key not in RETENTION_SECONDS:
        raise ValueError(
            f"Unsupported retention '{value}'. Choose from {', '.join(RETENTION_SECONDS)} or 'none'."
        )
    return key, RETENTION_SECONDS[key]
