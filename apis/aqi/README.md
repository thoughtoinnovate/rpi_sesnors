## AQI REST APIs

Run the HTTP server from the repo root:

```bash
python3 apis/aqi/server.py --host 0.0.0.0 --port 8080
```

Sensor bus/address/retry settings are read from `config/aqi.toml` (override with
the `AQI_CONFIG_FILE` environment variable if needed).

### Endpoints

| Method | Path                | Description                                |
| ------ | ------------------- | ------------------------------------------ |
| GET    | `/health`           | Basic liveness check                       |
| GET    | `/api/snapshot`     | Full set of readings (also served at `/`) |
| GET    | `/api/config`       | Effective sensor configuration             |
| GET    | `/api/status`       | Sensor status + firmware/config metadata   |
| GET    | `/api/firmware`     | Firmware version                           |
| GET    | `/api/pm/standard`  | CF=1 (standard) particulate mass data      |
| GET    | `/api/pm/atmosphere`| Atmospheric particulate mass data          |
| GET    | `/api/particle-counts` | Particle counts for all size bins     |
| GET    | `/api/readings`       | Fetch stored scheduler samples (supports filters) |
| DELETE | `/api/readings`       | Delete stored samples (optional `before` filter)  |
| POST   | `/api/power/low`    | Put the sensor into low-power mode         |
| POST   | `/api/power/wake`   | Wake the sensor back up                    |
| GET    | `/api/schedules`    | List stored scheduler configs              |
| POST   | `/api/schedules`    | Create a scheduler config                  |
| GET    | `/api/schedules/{id}` | Fetch a specific scheduler config       |
| PATCH  | `/api/schedules/{id}` | Update part of a scheduler config       |
| DELETE | `/api/schedules/{id}` | Remove a scheduler config               |
| GET    | `/api/scheduler/status` | Report scheduler runtime state        |
| POST   | `/api/scheduler/start` | Launch scheduler using a stored config |
| POST   | `/api/scheduler/stop`  | Terminate the running scheduler        |

All responses are JSON. Non-existent paths return `404` with an error payload.

Scheduler configs accept `name`, `location`, `frequency` (`5s`…`4h`), `type`
(`standard`/`atmospheric`), optional `retention` (`10s`…`90d` or `none`),
`powersave` (boolean to park the sensor between samples), and `enabled`
(default `true`). Use these endpoints to provision configs that the CLI
scheduler loads via `--config-name` / `--config-id`.

`/api/readings` query parameters:

- `limit` (default 100, max 1000)
- `location` (exact match)
- `type` (`standard`/`atmospheric`)
- `since` (ISO8601 timestamp, e.g., `2025-12-01T00:00:00+00:00`)
- `DELETE /api/readings?before=...&location=...` removes rows older than a
  timestamp and/or for a specific location; omit parameters to clear the table
  (use cautiously).

`POST /api/scheduler/start` expects JSON with either `config_name` or
`config_id`. `GET /api/scheduler/status` returns `{running, config_name,
config_id, powersave}`. `POST /api/scheduler/stop` terminates the active
process.
