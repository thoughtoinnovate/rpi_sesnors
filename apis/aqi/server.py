"""Minimal HTTP API for exposing AQI sensor readings."""
from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aqi import config_store  # noqa: E402
from aqi import reading_store  # noqa: E402
from aqi.aqi_index import AQIResult, compute_aqi  # noqa: E402
from aqi.core import air_quality_module as aqm  # noqa: E402
from aqi.schedule_defs import normalize_type  # noqa: E402
from aqi.scheduler_manager import SCHEDULER_MANAGER  # noqa: E402
from aqi.system_info import get_system_info  # noqa: E402

SENSOR = aqm.create_sensor()
STATIC_DIR = Path(__file__).resolve().parents[2] / "ui"


class AQIRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler that routes requests to the AQI core helpers."""

    def _build_aqi_payload(self, pm_standard: dict[str, int], pm_atmosphere: dict[str, int]) -> dict[str, dict[str, AQIResult]]:
        return {
            "us_epa": {
                "standard": compute_aqi(pm_standard, method="us_epa"),
                "atmospheric": compute_aqi(pm_atmosphere, method="us_epa"),
            },
            "purpleair": {
                "standard": compute_aqi(pm_standard, method="purpleair"),
                "atmospheric": compute_aqi(pm_atmosphere, method="purpleair"),
            },
        }

    def _json_response(self, payload: Any, status: int = HTTPStatus.OK.value) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_error(self, error: Exception) -> None:
        self._json_response({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR.value)

    def _read_json(self) -> Any:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON payload") from exc

    def _handle_schedule_collection(self, method: str) -> None:
        if method == "GET":
            self._json_response(config_store.list_configs())
            return
        if method == "POST":
            try:
                payload = self._read_json()
                config = config_store.create_config(payload)
                self._json_response(config, status=HTTPStatus.CREATED.value)
            except ValueError as exc:
                self._json_response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST.value)
            except Exception as exc:  # pragma: no cover - defensive
                self._handle_error(exc)
            return
        self._json_response({"error": "Method not allowed"}, status=HTTPStatus.METHOD_NOT_ALLOWED.value)

    def _handle_schedule_item(self, config_id: int, method: str) -> None:
        try:
            if method == "GET":
                config = config_store.get_config_by_id(config_id)
                if not config:
                    self._json_response({"error": "Not found"}, status=HTTPStatus.NOT_FOUND.value)
                    return
                self._json_response(config)
            elif method in ("PUT", "PATCH"):
                payload = self._read_json()
                config = config_store.update_config(config_id, payload)
                self._json_response(config)
            elif method == "DELETE":
                config_store.delete_config(config_id)
                self._json_response({"status": "deleted"})
            else:
                self._json_response({"error": "Method not allowed"}, status=HTTPStatus.METHOD_NOT_ALLOWED.value)
        except ValueError as exc:
            self._json_response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST.value)
        except KeyError:
            self._json_response({"error": "Not found"}, status=HTTPStatus.NOT_FOUND.value)
        except Exception as exc:  # pragma: no cover - defensive
            self._handle_error(exc)

    def _handle_readings(self, query: dict[str, list[str]]) -> None:
        limit_param = query.get("limit", ["100"])[0]
        try:
            limit = int(limit_param)
        except ValueError:
            self._json_response({"error": "limit must be an integer"}, status=HTTPStatus.BAD_REQUEST.value)
            return
        location = query.get("location", [None])[0]
        reading_type = query.get("type", [None])[0]
        since = query.get("since", [None])[0]
        try:
            normalized_type = normalize_type(reading_type) if reading_type else None
        except ValueError as exc:
            self._json_response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST.value)
            return
        try:
            readings = reading_store.list_readings(
                limit=limit,
                location=location,
                reading_type=normalized_type,
                since=since,
            )
            self._json_response(readings)
        except ValueError as exc:
            self._json_response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST.value)
        except Exception as exc:  # pragma: no cover - defensive
            self._handle_error(exc)

    def _maybe_serve_static(self, path: str) -> bool:
        if path == "/" or path == "":
            candidate = STATIC_DIR / "index.html"
        else:
            candidate = STATIC_DIR / path.lstrip("/")
        if candidate.is_file():
            try:
                data = candidate.read_bytes()
            except OSError:
                return False
            self.send_response(HTTPStatus.OK.value)
            self.send_header("Content-Length", str(len(data)))
            content_type = "text/plain"
            if candidate.suffix == ".html":
                content_type = "text/html; charset=utf-8"
            elif candidate.suffix == ".css":
                content_type = "text/css; charset=utf-8"
            elif candidate.suffix == ".js":
                content_type = "application/javascript; charset=utf-8"
            elif candidate.suffix in (".png", ".jpg", ".jpeg"):
                content_type = f"image/{candidate.suffix.lstrip('.')}"
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(data)
            return True
        return False

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if not path.startswith("/api/"):
            if self._maybe_serve_static(path):
                return
            # Serve SPA entry point for other front-end routes
            if self._maybe_serve_static("/index.html"):
                return
        try:
            if path == "/api/snapshot":
                snapshot = aqm.snapshot(SENSOR)
                snapshot["aqi"] = self._build_aqi_payload(snapshot["pm_standard"], snapshot["pm_atmosphere"])
                self._json_response(snapshot)
            elif path in ("/health", "/api/health"):
                self._json_response({"status": "ok"})
            elif path in ("/api/config",):
                self._json_response(aqm.load_config())
            elif path in ("/api/status",):
                self._json_response(aqm.sensor_status(SENSOR))
            elif path == "/api/readings":
                self._handle_readings(query)
            elif path == "/api/schedules":
                self._handle_schedule_collection("GET")
            elif path.startswith("/api/schedules/"):
                try:
                    config_id = int(path.split("/")[-1])
                except ValueError:
                    self._json_response({"error": "Invalid schedule id"}, status=HTTPStatus.BAD_REQUEST.value)
                    return
                self._handle_schedule_item(config_id, "GET")
            elif path == "/api/scheduler/status":
                self._json_response(SCHEDULER_MANAGER.status())
            elif path in ("/api/firmware",):
                self._json_response({"firmware": {"version": aqm.get_firmware_version(SENSOR)}})
            elif path in ("/api/pm/standard",):
                self._json_response(aqm.read_standard_pm(SENSOR))
            elif path in ("/api/pm/atmosphere",):
                self._json_response(aqm.read_atmospheric_pm(SENSOR))
            elif path == "/api/aqi":
                pm_standard = aqm.read_standard_pm(SENSOR)
                pm_atmosphere = aqm.read_atmospheric_pm(SENSOR)
                payload = self._build_aqi_payload(pm_standard, pm_atmosphere)
                payload["pm_standard"] = pm_standard
                payload["pm_atmosphere"] = pm_atmosphere
                self._json_response(payload)
            elif path == "/api/system/info":
                self._json_response(get_system_info())
            elif path in ("/api/particle-counts",):
                self._json_response(aqm.read_particle_counts(SENSOR))
            else:
                self._json_response({"error": "Not found"}, status=HTTPStatus.NOT_FOUND.value)
        except Exception as exc:  # pragma: no cover - defensive logging
            self._handle_error(exc)

    def do_POST(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/api/schedules":
                self._handle_schedule_collection("POST")
            elif path == "/api/scheduler/start":
                try:
                    payload = self._read_json()
                    config_name = payload.get("config_name")
                    config_id = payload.get("config_id")
                    result = SCHEDULER_MANAGER.start(config_name, config_id)
                    self._json_response(result, status=HTTPStatus.ACCEPTED.value)
                except ValueError as exc:
                    self._json_response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST.value)
                except RuntimeError as exc:
                    self._json_response({"error": str(exc)}, status=HTTPStatus.CONFLICT.value)
                except Exception as exc:  # pragma: no cover
                    self._handle_error(exc)
            elif path == "/api/scheduler/stop":
                try:
                    result = SCHEDULER_MANAGER.stop()
                    self._json_response(result)
                except RuntimeError as exc:
                    self._json_response({"error": str(exc)}, status=HTTPStatus.CONFLICT.value)
                except Exception as exc:  # pragma: no cover
                    self._handle_error(exc)
            elif path.startswith("/api/schedules/"):
                self._json_response({"error": "Method not allowed"}, status=HTTPStatus.METHOD_NOT_ALLOWED.value)
            elif path in ("/api/power/low",):
                aqm.enter_low_power(SENSOR)
                self._json_response({"status": "entering_low_power"})
            elif path in ("/api/power/wake",):
                aqm.wake_up(SENSOR)
                self._json_response({"status": "awake"})
            else:
                self._json_response({"error": "Not found"}, status=HTTPStatus.NOT_FOUND.value)
        except Exception as exc:  # pragma: no cover - defensive logging
            self._handle_error(exc)

    def do_PUT(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path.startswith("/api/schedules/"):
            try:
                config_id = int(path.split("/")[-1])
            except ValueError:
                self._json_response({"error": "Invalid schedule id"}, status=HTTPStatus.BAD_REQUEST.value)
                return
            self._handle_schedule_item(config_id, "PUT")
        else:
            self._json_response({"error": "Not found"}, status=HTTPStatus.NOT_FOUND.value)

    def do_PATCH(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path.startswith("/api/schedules/"):
            try:
                config_id = int(path.split("/")[-1])
            except ValueError:
                self._json_response({"error": "Invalid schedule id"}, status=HTTPStatus.BAD_REQUEST.value)
                return
            self._handle_schedule_item(config_id, "PATCH")
        else:
            self._json_response({"error": "Not found"}, status=HTTPStatus.NOT_FOUND.value)

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path.startswith("/api/schedules/"):
            try:
                config_id = int(path.split("/")[-1])
            except ValueError:
                self._json_response({"error": "Invalid schedule id"}, status=HTTPStatus.BAD_REQUEST.value)
                return
            self._handle_schedule_item(config_id, "DELETE")
        elif path == "/api/readings":
            before = query.get("before", [None])[0]
            location = query.get("location", [None])[0]
            try:
                deleted = reading_store.delete_readings(before, location)
                self._json_response({"deleted": deleted})
            except ValueError as exc:
                self._json_response({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST.value)
            except Exception as exc:  # pragma: no cover
                self._handle_error(exc)
        else:
            self._json_response({"error": "Not found"}, status=HTTPStatus.NOT_FOUND.value)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003 - matches BaseHTTPRequestHandler
        """Trim noisy default logging."""
        return


def run_server(host: str, port: int) -> None:
    """Start the HTTP server."""
    server = ThreadingHTTPServer((host, port), AQIRequestHandler)
    print(f"Starting AQI API server on {host}:{port}")  # noqa: T201 - CLI feedback
    server.serve_forever()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Expose AQI helper APIs over HTTP.")
    parser.add_argument("--host", default="0.0.0.0", help="Host/IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
