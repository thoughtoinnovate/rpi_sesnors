## AQI Scheduler

Run the single-instance scheduler to persist readings into `sensor.db`:

```bash
python3 -m aqi.scheduler --config-name lab-standard
```

### Arguments

- `--config-name` / `--config-id`: Load location/frequency/type/retention from the `aqi.schedule_configs` table (create/update/delete them via the REST API).
- `--location`, `--frequency`, `--type`, `--retention`: Manual overrides when no stored config is supplied; support the same value set exposed by the API.
- `--retention`: Optional window (`7d`, `30d`, etc.) that deletes older rows after every sample (default: keep everything) or `none`.
- `--powersave`: When set (manual mode), parks the sensor in low-power mode between samples.

Optional: `--max-iterations` limits the number of samples (useful for testing).

### Stored Configurations

Scheduler presets live in `sensor.db` (`aqi.schedule_configs` table). Use the API:

```bash
# Create a config
curl -s -X POST http://localhost:8080/api/schedules \
  -H "Content-Type: application/json" \
  -d '{"name": "lab-standard", "location": "lab", "frequency": "5m", "type": "standard", "retention": "30d", "powersave": true}'

# List configs
curl -s http://localhost:8080/api/schedules
```

### Storage

Data lands in `sensor.db` under schema `aqi`, table `schedule_readings`:

| Column     | Type    | Notes                               |
| ---------- | ------- | ----------------------------------- |
| `timestamp`| TEXT    | UTC ISO8601 when the sample logged  |
| `location` | TEXT    | User-provided label                 |
| `type`     | TEXT    | `standard` or `atmospheric`         |
| `pm1`      | INTEGER | µg/m³                               |
| `pm2_5`    | INTEGER | µg/m³                               |
| `pm10`     | INTEGER | µg/m³                               |
| `particles_0_3um` | INTEGER | Count / 0.1 L (0.3 µm)       |
| `particles_0_5um` | INTEGER | Count / 0.1 L (0.5 µm)       |
| `particles_1_0um` | INTEGER | Count / 0.1 L (1.0 µm)       |
| `particles_2_5um` | INTEGER | Count / 0.1 L (2.5 µm)       |
| `particles_5_0um` | INTEGER | Count / 0.1 L (5.0 µm)       |
| `particles_10um`  | INTEGER | Count / 0.1 L (10 µm)        |

Only one scheduler instance can run at a time—starting a second process exits
immediately with an error until the first stops (file lock `scheduler.lock`).
