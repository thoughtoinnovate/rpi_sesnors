# AQI Scheduler

Automated air quality monitoring scheduler that runs at specified intervals and collects sensor readings for configured locations.

## Features

- **Flexible Time Intervals**: Support for hours, minutes, seconds (e.g., '1h2m1s', '30m', '45s')
- **Continuous Monitoring**: Runs indefinitely until stopped with Ctrl+C
- **Location-Based**: Monitor specific locations from your database
- **Robust Error Handling**: Continues running even if individual readings fail
- **Real-Time Logging**: Detailed status updates and statistics
- **Graceful Shutdown**: Clean termination with comprehensive final statistics

## Usage

### Command Line

```bash
cd app/

# Basic usage - 30 minute intervals
python run_scheduler.py "Home Office" "30m"

# Hourly monitoring
python run_scheduler.py "Backyard" "1h"

# Complex intervals
python run_scheduler.py "Living Room" "1h15m30s"

# Custom database and logging
python run_scheduler.py "Office" "5m" --db my_database.db --log-level DEBUG

# Dry run to validate configuration
python run_scheduler.py "Home Office" "30m" --dry-run
```

### Programmatic Usage

```python
from app.scheduler import AQIScheduler, TimeParser

# Parse interval string
interval_seconds = TimeParser.parse_time_interval("30m")  # 1800 seconds

# Create and run scheduler
scheduler = AQIScheduler("Home Office", interval_seconds, "aqi_demo.db")
scheduler.run()
```

## Time Format

The scheduler accepts flexible time formats:

- **Hours**: `2h`, `1h`
- **Minutes**: `30m`, `5m`
- **Seconds**: `45s`, `10s`
- **Combined**: `1h30m`, `2h15m45s`, `1h2m1s`

### Examples:
- `"30m"` → 30 minutes
- `"1h"` → 1 hour
- `"45s"` → 45 seconds
- `"1h30m"` → 1 hour 30 minutes
- `"2h15m45s"` → 2 hours, 15 minutes, 45 seconds

## Command Line Options

```
positional arguments:
  location              Location name to monitor (must exist in database)
  interval              Time interval between readings

options:
  -h, --help            Show help message
  --db DB               Database file path (default: aqi_monitoring.db)
  --log-level LEVEL     Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
  --dry-run             Validate configuration without starting scheduler
```

## Output Example

```
🚀 AQI Monitoring Scheduler
========================================
📍 Location: Home Office
⏰ Interval: 30m (30m)
💾 Database: aqi_demo.db
📝 Log Level: INFO
========================================
🟢 Starting scheduler... (Press Ctrl+C to stop)

2025-11-18 13:08:03 - ✅ Reading #1: PM2.5=49.0 μg/m³, PM10=61.0 μg/m³, AQI=134 (Unhealthy for Sensitive Groups)
2025-11-18 13:08:13 - ✅ Reading #2: PM2.5=50.0 μg/m³, PM10=62.0 μg/m³, AQI=136 (Unhealthy for Sensitive Groups)
2025-11-18 13:08:23 - ✅ Reading #3: PM2.5=49.0 μg/m³, PM10=60.0 μg/m³, AQI=134 (Unhealthy for Sensitive Groups)

^C🛑 Received SIGINT, initiating graceful shutdown...

============================================================
SCHEDULER STOPPED
============================================================
Total readings taken: 3
Total runtime: 1h30m
Average interval: 30.0 minutes
Readings per hour: 2.0
============================================================
```

## Requirements

- **Location Setup**: Location must exist in the AQI database
- **Sensor Access**: PM25 sensor must be connected and accessible
- **Database**: SQLite database with proper schema
- **Python**: Compatible with existing AQI app environment

## Error Handling

- **Invalid Location**: Scheduler validates location exists before starting
- **Sensor Failures**: Individual reading failures don't stop the scheduler
- **Database Issues**: Comprehensive error logging and recovery
- **Time Format Errors**: Clear validation with helpful error messages

## Integration

The scheduler integrates seamlessly with the existing AQI app:

- Uses the same `AQIApp` class for data collection
- Stores data in the same SQLite database schema
- Compatible with all existing AQI app features
- Can run alongside manual readings and other tools

## Best Practices

1. **Start with Dry Run**: Use `--dry-run` to validate configuration
2. **Choose Appropriate Intervals**: Balance data needs with sensor wear
3. **Monitor Logs**: Use appropriate log levels for your needs
4. **Graceful Shutdown**: Always use Ctrl+C for clean termination
5. **Regular Backups**: Schedule database backups for long-term monitoring

## Troubleshooting

**Location not found:**
```bash
# Add location first
python run_aqi_app.py  # This will create locations
```

**Invalid time format:**
```bash
# Use correct format
python run_scheduler.py "Location" "30m"  # ✓ Correct
python run_scheduler.py "Location" "30"   # ✗ Missing unit
```

**Sensor connection issues:**
- Check sensor is connected to I2C bus
- Verify sensor address (default: 0x19)
- Check sensor power and wiring