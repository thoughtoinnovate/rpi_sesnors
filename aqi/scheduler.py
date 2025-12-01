"""Single-instance scheduler that logs AQI readings to SQLite."""
from __future__ import annotations

import argparse
import fcntl
import signal
import sqlite3
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Tuple

from aqi import config_store
from aqi import db as aqi_db
from aqi.core import air_quality_module as aqm
from aqi.schedule_defs import normalize_frequency, normalize_retention, normalize_type, parse_bool

TABLE_NAME = "schedule_readings"
REPO_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = REPO_ROOT / "scheduler.lock"
SCHEMA_NAME = aqi_db.SCHEMA_NAME
POWERSAVE_WAKE_SECONDS = 2.0


def _connect_db():
    return aqi_db.connect(check_same_thread=False)


def _insert_row(
    conn: sqlite3.Connection,
    location: str,
    reading_type: str,
    pm: Dict[str, int],
    counts: Dict[str, int],
) -> None:
    conn.execute(
        f"""
        INSERT INTO {SCHEMA_NAME}.{TABLE_NAME} (
            timestamp,
            location,
            type,
            pm1,
            pm2_5,
            pm10,
            particles_0_3um,
            particles_0_5um,
            particles_1_0um,
            particles_2_5um,
            particles_5_0um,
            particles_10um
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            location,
            reading_type,
            pm["pm1_0"],
            pm["pm2_5"],
            pm["pm10"],
            counts["particles_0_3um"],
            counts["particles_0_5um"],
            counts["particles_1_0um"],
            counts["particles_2_5um"],
            counts["particles_5_0um"],
            counts["particles_10um"],
        ),
    )
    conn.commit()


def _apply_retention(conn: sqlite3.Connection, retention_seconds: int | None) -> None:
    if not retention_seconds:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=retention_seconds)
    conn.execute(
        f"DELETE FROM {SCHEMA_NAME}.{TABLE_NAME} WHERE timestamp < ?",
        (cutoff.isoformat(),),
    )
    conn.commit()


@contextmanager
def _single_instance_lock() -> None:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    file = LOCK_PATH.open("w")
    try:
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:  # pragma: no cover - runtime guard
        file.close()
        raise SystemExit("Scheduler already running. Stop it before starting a new instance.") from exc
    try:
        yield
    finally:
        fcntl.flock(file, fcntl.LOCK_UN)
        file.close()
        try:
            LOCK_PATH.unlink()
        except FileNotFoundError:
            pass


def _collect(sensor: aqm.AirQualitySensor, reading_type: str) -> Tuple[Dict[str, int], Dict[str, int]]:
    if reading_type == "standard":
        pm = aqm.read_standard_pm(sensor)
    else:
        pm = aqm.read_atmospheric_pm(sensor)
    counts = aqm.read_particle_counts(sensor)
    return pm, counts


def _scheduler_loop(
    location: str,
    reading_type: str,
    interval: int,
    retention_seconds: int | None,
    max_iterations: int | None,
    powersave: bool,
) -> None:
    stop_event = threading.Event()

    def _handle_signal(signum: int, _frame: object) -> None:
        print(f"Received signal {signum}, stopping scheduler...", file=sys.stderr)  # noqa: T201
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    sensor = aqm.create_sensor()
    conn = _connect_db()
    iterations = 0

    try:
        while not stop_event.is_set():
            if powersave:
                aqm.wake_up(sensor)
                time.sleep(POWERSAVE_WAKE_SECONDS)
            pm, counts = _collect(sensor, reading_type)
            if powersave:
                aqm.enter_low_power(sensor)
            _insert_row(conn, location, reading_type, pm, counts)
            _apply_retention(conn, retention_seconds)
            iterations += 1
            print(
                f"[{datetime.now(timezone.utc).isoformat()}] Logged {reading_type} "
                f"reading for {location}: {pm}",
                file=sys.stderr,
            )
            if max_iterations and iterations >= max_iterations:
                break
            stop_event.wait(interval)
    finally:
        if powersave:
            try:
                aqm.enter_low_power(sensor)
            except Exception:
                pass
        conn.close()


def _resolve_manual_config(args: argparse.Namespace) -> Tuple[str, str, int, int | None, bool]:
    if not args.location or not args.frequency or not args.type:
        raise SystemExit(
            "Provide --location, --frequency, and --type when not using --config-name/--config-id."
        )
    try:
        _, interval = normalize_frequency(args.frequency)
        reading_type = normalize_type(args.type)
        _, retention_seconds = normalize_retention(args.retention)
        powersave = args.powersave
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    return args.location, reading_type, interval, retention_seconds, powersave


def _load_config_from_store(name: str | None, config_id: int | None) -> Tuple[str, str, int, int | None, bool]:
    config = None
    if name:
        config = config_store.get_config_by_name(name)
    elif config_id is not None:
        config = config_store.get_config_by_id(config_id)
    if not config:
        raise SystemExit("Scheduler config not found in database.")
    if not config["enabled"]:
        raise SystemExit("Scheduler config is disabled.")
    return (
        config["location"],
        config["type"],
        config["frequency_seconds"],
        config["retention_seconds"],
        bool(config.get("powersave", False)),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AQI scheduler (single instance).")
    config_group = parser.add_mutually_exclusive_group()
    config_group.add_argument("--config-name", help="Stored scheduler config name")
    config_group.add_argument("--config-id", type=int, help="Stored scheduler config ID")
    parser.add_argument("--location", help="Logical location label (used when no stored config)")
    parser.add_argument("--frequency", help="Sample interval (5s/15s/30s/1m/5m/15m/30m/1h/2h/4h)")
    parser.add_argument(
        "--type",
        help="Reading type: 'standard' or 'atmospheric'",
    )
    parser.add_argument(
        "--retention",
        default=None,
        help="Optional retention window (e.g. 7d, 30d). Use 'none' to disable.",
    )
    parser.add_argument(
        "--powersave",
        action="store_true",
        help="Enable low-power mode between samples for manual configs.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Optional testing override to stop after N samples.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.config_name or args.config_id is not None:
        location, reading_type, interval, retention_seconds, powersave = _load_config_from_store(
            args.config_name, args.config_id
        )
    else:
        location, reading_type, interval, retention_seconds, powersave = _resolve_manual_config(args)
    with _single_instance_lock():
        _scheduler_loop(location, reading_type, interval, retention_seconds, args.max_iterations, powersave)


if __name__ == "__main__":
    main()
