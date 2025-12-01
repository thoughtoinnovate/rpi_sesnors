# AQI Sensor Service

Raspberry Pi–friendly service that reads the SEN0460 particulate sensor,
exposes the data over a minimal REST API, and ships with a lightweight Alpine.js
dashboard that runs comfortably on a Pi 3.

## Quick Start

```bash
make start             # starts the REST API + UI (defaults to port 9000)
PORT=7000 make start   # override listen port/host via env vars
make status            # prints whether the API is running
make stop              # stops the API and any running scheduler processes
```

Visit `http://<device-ip>:<PORT>/` (default `http://localhost:9000/`) to open
the dashboard. `make start` handles restarts automatically and refuses to start
if the port is already bound.

> Tip: when you are working headless you can still inspect the UI with
> [Browsh](https://www.brow.sh/) or by SSH port‑forwarding to a desktop browser.

## Features

- **Live snapshot** – `/api/snapshot` returns PM mass concentrations, particle
  counts, and precomputed AQI scores (US EPA + PurpleAir correction) for both
  `pm_standard` (CF=1) and `pm_atmosphere`.
- **AQI endpoint** – `/api/aqi` exposes the AQI payload by itself plus the PM
  inputs used to compute it.
- **Scheduler** – run timed captures via `/api/schedules` and
  `/api/scheduler/*` endpoints (see below).
- **Dashboard** – tabbed UI (“Air Quality” section) with real‑time AQI card,
  scheduler controls, reports (Chart.js graphs with metric/window/location
  filters), and sensor/system status pages. You can choose which AQI method to
  display (US EPA, PurpleAir, or a browser fallback).

## API Cheatsheet

| Endpoint | Description |
| --- | --- |
| `GET /api/snapshot` | Full sensor snapshot with `pm_standard`, `pm_atmosphere`, `particle_counts`, and `aqi` results. |
| `GET /api/aqi` | AQI payload (US EPA + PurpleAir) and the PM readings used for each calculation. |
| `GET /api/readings?limit=100&location=<name>&type=standard` | Historical scheduler readings from SQLite. |
| `GET /api/schedules` | List saved scheduler configs. |
| `POST /api/schedules` | Create a config (`name`, `location`, `type`, `frequency`, …). |
| `POST /api/scheduler/start` | Start the scheduler with `{ "config_name": "..."} or { "config_id": N }`. |
| `POST /api/scheduler/stop` | Stop the running scheduler. |
| `GET /api/system/info` | Pi OS/CPU/memory/disk details for the “OS & Hardware” tab. |

All endpoints return JSON; most errors include `{ "error": "..." }`.

Common sanity checks:

```bash
curl -s http://localhost:9000/api/snapshot | jq
curl -s http://localhost:9000/api/aqi       | jq '.us_epa.standard'
```

## Scheduler

Manage scheduler configurations via the REST API (`/api/schedules`). Start or
stop the scheduler using:

- `POST /api/scheduler/start` with `{ "config_name": "lab-standard" }`
- `POST /api/scheduler/stop`
- `GET /api/scheduler/status`

See `aqi/SCHEDULER.md` for detailed CLI usage and config options.

## UI Guide

- **Dashboard** – pick “Atmospheric” or “Standard” readings and choose the AQI
  method (US EPA, PurpleAir, or browser fallback). Snapshot data is refreshed
  every 30 s; use the “Refresh Snapshot” button when you need an immediate read.
- **Scheduler** – start/stop the background capture process, manage configs,
  and clean up readings without touching SQLite manually.
- **Reports** – choose a location/metric/time window and Chart.js renders the
  series; if no data exists the UI shows a “No data” hint instead of failing.
- **Sensor Hardware** – firmware, bus/address, and power‑save controls (wake or
  enter low‑power mode).
- **OS & Hardware** – Pi load averages, memory, disk, uptime, and CPU temps.

All menu items for air quality now live under the **Sensors → Air Quality**
group so additional sensor types can be added later without reshuffling the UI.

## Troubleshooting

- **API / sensor sanity** – compare `/api/snapshot` against the vendor library
  in `../test/DFRobot_AirQualitySensor` (the service and the legacy driver
  should match byte‑for‑byte).
- **UI errors** – open browser devtools (or run Browsh) and check the console.
  Alpine/Chart.js exceptions usually indicate a missing dataset or filter typo.
- **Headless testing** – Browsh or SSH tunneling lets you exercise the SPA
  without installing a full desktop environment on the Pi.

## Directory Layout

- `apis/` – HTTP server and request handler.
- `aqi/` – sensor drivers, scheduler helpers, DB access, and the new
  `aqi_index.py` AQI calculations.
- `ui/` – static HTML/CSS/JS served directly by the API.
- `scripts/manage.sh` – wrapper used by the Makefile to start/stop processes.
- `sensor.db` – SQLite database storing scheduler readings/configs.
