# Agent Guidelines for PM25 Sensor Codebase

## Project Overview

This is a comprehensive air quality monitoring system with:
- **PM25 Sensor Library** (`sensors/`): Low-level I2C sensor communication, AQI calculations, location detection
- **AQI Application** (`app/`, `aqi/`): Database storage, location management, automated scheduling
- **REST API** (`app/rest_api/`): Flask-based API with 25+ endpoints for sensor data access
- **Frontend UI** (`ui/`): React/TypeScript web interface
- **Examples & Tools**: Demo scripts, validation tools, test utilities

## Project Structure

```
pm25/
├── sensors/              # Core PM25 sensor library
│   ├── pm25_sensor.py    # Main sensor class
│   ├── aqi_v2.py         # AQI v2 calculations (atmospheric values)
│   ├── location.py       # Location detection
│   ├── i2c_interface.py  # I2C communication
│   ├── examples/         # Usage examples
│   └── tests/            # Comprehensive test suite
├── app/                  # Application layer
│   ├── aqi_app.py        # AQI database and location management
│   ├── rest_api/         # Flask REST API
│   │   ├── app.py        # Main API (25+ endpoints)
│   │   └── run.py        # API server runner
│   └── run_scheduler.py  # Automated monitoring scheduler
├── aqi/                  # AQI-specific modules
│   ├── aqi_app.py        # Database wrapper
│   └── scheduler.py      # Time-based scheduler
├── ui/                   # Frontend React/TypeScript application
├── scripts/              # Utility scripts
└── tools/                # Development tools
```

## Build/Lint/Test Commands

### Testing
- **All tests**: `python -m pytest sensors/tests/ -v`
- **Single file**: `python -m pytest sensors/tests/test_aqi_v2.py -v`
- **With markers**: `python -m pytest sensors/tests/ -m hardware -v` (markers: hardware, comparison, performance, integration)
- **Single test**: `python -m pytest sensors/tests/test_aqi_v2.py::test_calculate_aqi_v2_basic -v`

### Build/Run

#### REST API Server
- **Start**: `make start` (starts server on localhost:5000)
- **Stop**: `make stop`
- **Status**: `make status`
- **Logs**: `make logs`
- **Direct run**: `python app/rest_api/app.py` or `cd app/rest_api && python run.py`

#### AQI Application
- **Run example**: `python app/aqi_app_example.py`
- **Run scheduler**: `python app/run_scheduler.py "LocationName" "30m"`

#### Sensor Examples
- **Basic reading**: `python sensors/examples/basic_readings.py`
- **AQI v2 demo**: `python sensors/examples/aqi_v2_demo.py`
- **Location demo**: `python sensors/examples/location_demo.py`
- **Continuous monitoring**: `python sensors/examples/continuous_monitoring.py`

#### Frontend UI
- **Navigate to UI**: `cd ui/`
- **Install dependencies**: `npm install` (if needed)
- **Run dev server**: Check `ui/package.json` for scripts

### Linting/Formatting
No linting or formatting tools configured. Follow manual style guidelines.

## Code Style Guidelines

### Imports & Naming
- Imports: stdlib → third-party → local (absolute imports, grouped with blank lines)
- Functions/methods/variables: `snake_case`
- Classes: `PascalCase`, Constants: `UPPER_CASE`, Private: `_leading_underscore`

### Type Hints & Error Handling
- Full type annotations using `typing` module (`Dict`, `List`, `Optional`, `Union`, etc.)
- Use `-> ReturnType` syntax
- Custom exceptions from `sensors/exceptions.py`, catch specific exceptions
- Use `@handle_sensor_exception` decorator for sensor operations (if available)

### Documentation & Structure
- Comprehensive docstrings with params, returns, exceptions
- Constants at module level in `UPPER_CASE`
- Private helpers prefixed with `_`, context managers for resources
- One class per file, f-strings for formatting

## Key Components

### Sensors Module (`sensors/`)
- **PM25Sensor**: Main sensor interface with I2C communication
- **AQI v2**: Atmospheric-based AQI calculations (matches AirNow, PurpleAir, IQAir)
- **Location Detection**: GPS-based location tracking
- **Power Management**: Sleep/wake functionality
- **Error Handling**: Comprehensive exception hierarchy

### AQI Application (`app/`, `aqi/`)
- **AQIDatabase**: SQLite database with normalized schema (locations, readings, aqi_calculations)
- **AQIApp**: High-level application interface
- **AQIScheduler**: Automated monitoring with flexible time intervals (e.g., "30m", "1h15m30s")

### REST API (`app/rest_api/`)
- **Core Endpoints** (`/api/*`): Health, locations, readings, history, stats, scheduler control
- **Sensor Endpoints** (`/sensor/aqi/sensor/*`): Direct sensor operations, diagnostics, power management
- **AQI Endpoints** (`/sensor/aqi/aqi/*`): AQI calculations, analysis, breakpoints
- **Combined Endpoints** (`/sensor/aqi/combined/*`): Integrated sensor + AQI + database operations

### Database Schema
- **locations**: Monitoring locations with GPS coordinates
- **readings**: Raw sensor readings (PM concentrations, particle counts, sensor metadata)
- **aqi_calculations**: Calculated AQI values with metadata

## Common Tasks

### Adding a New Location
```python
from aqi.aqi_app import AQIApp
app = AQIApp("database.db")
location_id = app.add_monitoring_location(
    name="Living Room",
    latitude=40.7128,
    longitude=-74.0060,
    city="New York"
)
```

### Taking a Reading
```python
result = app.take_reading("Living Room")
# Stores reading + AQI calculation in database
```

### Running Automated Monitoring
```bash
python app/run_scheduler.py "Living Room" "30m"
# Takes readings every 30 minutes until stopped (Ctrl+C)
```

### Using REST API
```bash
# Health check
curl http://localhost:5000/api/health

# Get latest reading
curl http://localhost:5000/api/latest/LivingRoom

# Start scheduler via API
curl -X POST -H "Content-Type: application/json" \
  -d '{"location": "LivingRoom", "interval": "30m"}' \
  http://localhost:5000/api/scheduler/start
```

## Important Notes

1. **AQI v2**: Uses atmospheric values only (not standard), matching professional monitoring services
2. **Database**: SQLite database path can be set via `AQI_DB_PATH` environment variable
3. **Sensor Address**: Default I2C address is 0x19 (25 decimal), bus 1
4. **API Port**: Default REST API port is 5000 (configurable)
5. **Scheduler Intervals**: Supports flexible formats: "30m", "1h", "1h15m30s", etc.
6. **Error Handling**: All sensor operations use custom exceptions from `sensors/exceptions.py`
7. **Testing**: Tests require actual hardware for hardware-marked tests