# AQI Monitoring App

A comprehensive air quality monitoring application that stores PM sensor readings and AQI calculations in SQLite database with location tracking.

**📂 Location:** `app/` directory in the PM25 project root

## Features

- **SQLite Database Storage**: Normalized schema for efficient data storage and querying
- **Location Management**: Track air quality at multiple monitoring locations
- **Automated Scheduling**: Continuous monitoring with flexible time intervals
- **Raw Sensor Data**: Store all atmospheric PM readings (PM1.0, PM2.5, PM10)
- **AQI Calculations**: Automatic AQI v2 calculations with complete metadata
- **Historical Data**: Query and analyze historical air quality trends
- **Data Export**: Export data in JSON or CSV format

## Database Schema

### Tables

**locations**
- Monitoring location information with GPS coordinates
- Fields: id, name, latitude, longitude, city, country, description, is_active

**readings**
- Raw sensor readings with timestamps
- Stores atmospheric PM concentrations, particle counts, sensor metadata
- Linked to locations table

**aqi_calculations**
- Calculated AQI values and metadata
- Stores AQI value, level, color, source pollutant, health messages
- Linked to readings table

## Quick Start

```python
# From the app directory
cd app/

# Import and use the AQI app
from aqi_app import AQIApp

# Initialize app
app = AQIApp("my_monitoring.db")

# Add a monitoring location
location_id = app.add_monitoring_location(
    name="Living Room",
    latitude=40.7128,
    longitude=-74.0060,
    city="New York"
)

# Take a reading (connects to PM25 sensor automatically)
result = app.take_reading("Living Room")
if result:
    print(f"AQI: {result['aqi']['aqi_value']} ({result['aqi']['aqi_level']})")

# Get recent readings
readings = app.get_location_readings("Living Room", limit=10)

# Export data
json_data = app.export_data("Living Room", format_type="json")

app.close()
```

**Alternative - Run from project root:**
```bash
# From project root directory
python -c "
import sys
sys.path.append('app')
from aqi_app import AQIApp
app = AQIApp()
# ... use app ...
"
```

## Automated Scheduling

The AQI app includes a powerful scheduler for continuous monitoring:

```bash
cd app/

# Schedule readings every 30 minutes
python run_scheduler.py "Home Office" "30m"

# Schedule readings every hour
python run_scheduler.py "Backyard" "1h"

# Complex intervals (1 hour, 15 minutes, 30 seconds)
python run_scheduler.py "Living Room" "1h15m30s"
```

**Scheduler Features:**
- Flexible time intervals (hours, minutes, seconds)
- Continuous operation until stopped (Ctrl+C)
- Real-time logging and statistics
- Graceful error handling
- Location-based monitoring

See `SCHEDULER_README.md` for complete scheduler documentation.

## API Reference

### AQIApp Class

#### Methods

- `add_monitoring_location(name, **location_data)`: Add a new monitoring location
- `take_reading(location_name)`: Take a complete sensor reading at specified location
- `get_location_readings(location_name, limit=10)`: Get recent readings for a location
- `get_all_locations()`: Get all monitoring locations
- `get_dashboard_data()`: Get summary dashboard data
- `export_data(location_name=None, format_type='json')`: Export data as JSON or CSV

### AQIDatabase Class

#### Location Management
- `add_location(name, **data)`: Add location
- `get_location(location_id)`: Get location by ID
- `get_location_by_name(name)`: Get location by name
- `list_locations(active_only=True)`: List all locations
- `update_location(location_id, **updates)`: Update location

#### Data Storage
- `store_reading(location_id, pm1_0_atm, pm2_5_atm, pm10_atm, ...)`: Store sensor reading
- `store_aqi_calculation(reading_id, aqi_value, aqi_level, ...)`: Store AQI calculation

#### Querying
- `get_recent_readings(location_id=None, limit=10)`: Get recent readings
- `get_readings_by_date_range(start_date, end_date, location_id=None)`: Query by date range
- `get_aqi_statistics(location_id=None, days=7)`: Get AQI statistics
- `get_location_summary(location_id)`: Get location summary

## Example Output

```
=== AQI Monitoring App Example ===

1. Initializing AQI monitoring application...
   Database initialized successfully

2. Adding monitoring locations...
   Added location: Home Office (ID: 1)
   Added location: Backyard (ID: 2)

3. Taking sensor readings...
   Taking reading at Home Office...
   ✓ Reading stored successfully
     PM2.5: 58 μg/m³
     AQI: 152 (Unhealthy)

4. Querying recent readings...
   Recent readings for Home Office (3 found):
     1. 2025-11-18 07:25:56 - PM2.5: 58.0 μg/m³, AQI: 152 (Unhealthy)
     2. 2025-11-18 07:25:31 - PM2.5: 55.0 μg/m³, AQI: 149 (Unhealthy for Sensitive Groups)

5. Dashboard summary...
   Total monitoring locations: 2

   Location: Home Office
     Total readings: 3
     Average PM2.5: 55.7 μg/m³
     Latest AQI: 152 (Unhealthy)
```

## Requirements

- Python 3.7+
- SQLite3 (built-in with Python)
- PM25 sensor connected via I2C
- PM25 sensor Python library

## Data Export

The app supports exporting data in multiple formats:

```python
# Export specific location data as JSON
json_data = app.export_data("Home Office", format_type="json")

# Export all locations as CSV
csv_data = app.export_data(format_type="csv")
```

## AQI Calculation

Uses AQI v2 (atmospheric values) which matches professional air quality monitoring services like AirNow, PurpleAir, and IQAir. The calculation considers both PM2.5 and PM10 values, using the higher AQI value when both are available.