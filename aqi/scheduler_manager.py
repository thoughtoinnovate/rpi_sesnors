"""Manage scheduler lifecycle within the API process."""
from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

from aqi import config_store

class SchedulerManager:
    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen[bytes]] = None
        self._lock = threading.Lock()
        self._config_name: Optional[str] = None
        self._config_id: Optional[int] = None
        self._powersave: bool = False

    def status(self) -> dict:
        with self._lock:
            running = self._process is not None and self._process.poll() is None
            return {
                "running": running,
                "config_name": self._config_name,
                "config_id": self._config_id,
                "powersave": self._powersave if running else False,
            }

    def start(self, config_name: Optional[str], config_id: Optional[int]) -> dict:
        with self._lock:
            if self._process and self._process.poll() is None:
                raise RuntimeError("Scheduler already running.")
            if not config_name and config_id is None:
                raise ValueError("Provide config_name or config_id to start scheduler.")
            config = None
            if config_name:
                config = config_store.get_config_by_name(config_name)
            elif config_id is not None:
                config = config_store.get_config_by_id(config_id)
            if not config:
                raise ValueError("Scheduler config not found.")
            if not config["enabled"]:
                raise ValueError("Scheduler config is disabled.")
            powersave = bool(config.get("powersave", False))
            chosen_name = config_name or config["name"]
            chosen_id = config_id or config["id"]
            repo_root = Path(__file__).resolve().parents[1]
            cmd = [
                sys.executable,
                "-m",
                "aqi.scheduler",
            ]
            if config_name:
                cmd += ["--config-name", config_name]
            else:
                cmd += ["--config-id", str(chosen_id)]
            process = subprocess.Popen(
                cmd,
                cwd=str(repo_root),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._process = process
            self._config_name = chosen_name
            self._config_id = chosen_id
            self._powersave = powersave
            return {
                "pid": process.pid,
                "config_name": chosen_name,
                "config_id": chosen_id,
                "powersave": powersave,
            }

    def stop(self) -> dict:
        with self._lock:
            if not self._process or self._process.poll() is not None:
                raise RuntimeError("Scheduler not running.")
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            pid = self._process.pid
            self._process = None
            self._config_name = None
            self._config_id = None
            self._powersave = False
            return {"stopped_pid": pid}


SCHEDULER_MANAGER = SchedulerManager()
