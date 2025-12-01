"""Collect OS/Hardware metrics for display."""
from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path
from typing import Dict, Any


def _read_cpu_temp() -> float | None:
    path = Path("/sys/class/thermal/thermal_zone0/temp")
    try:
        if path.exists():
            value = path.read_text().strip()
            if value:
                return int(value) / 1000.0
    except OSError:
        pass
    return None


def _read_meminfo() -> Dict[str, int]:
    info: Dict[str, int] = {}
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as memfile:
            for line in memfile:
                if ":" not in line:
                    continue
                key, rest = line.split(":", 1)
                parts = rest.strip().split()
                if not parts:
                    continue
                try:
                    info[key] = int(parts[0])
                except ValueError:
                    continue
    except OSError:
        pass
    return info


def _read_uptime() -> float | None:
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as uptime_file:
            return float(uptime_file.readline().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def get_system_info() -> Dict[str, Any]:
    uname = platform.uname()
    load = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
    disk = shutil.disk_usage("/")
    meminfo = _read_meminfo()
    total_mem = meminfo.get("MemTotal", 0) * 1024
    free_mem = meminfo.get("MemAvailable", meminfo.get("MemFree", 0)) * 1024
    used_mem = max(total_mem - free_mem, 0)
    uptime = _read_uptime()
    return {
        "platform": {
            "system": uname.system,
            "node": uname.node,
            "release": uname.release,
            "version": uname.version,
            "machine": uname.machine,
            "processor": uname.processor,
        },
        "load_average": {
            "1m": load[0],
            "5m": load[1],
            "15m": load[2],
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
        },
        "memory": {
            "total": total_mem,
            "used": used_mem,
            "free": free_mem,
        },
        "cpu_temperature_c": _read_cpu_temp(),
        "uptime_seconds": uptime,
    }

