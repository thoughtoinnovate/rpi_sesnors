# Agent Guidelines for PM25 Sensor Codebase

## Build/Lint/Test Commands

### Testing
- **All tests**: `python -m pytest sensors/tests/ -v`
- **Single file**: `python -m pytest sensors/tests/test_aqi_v2.py -v`
- **Single test**: `python -m pytest sensors/tests/test_aqi_v2.py::test_calculate_aqi_v2_basic -v`
- **With markers**: `python -m pytest sensors/tests/ -m hardware -v` (markers: hardware, comparison, performance, integration)

### Build/Run
- **API server**: `make start` (localhost:5000) or `make unified` for UI+API
- **Install deps**: `make install` (Python + Node.js)
- **UI dev**: `cd ui && npm run dev`
- **Direct API**: `python app/rest_api/app.py`

### Linting/Formatting
No automated tools configured. Follow manual style guidelines below.

## Code Style Guidelines

### Imports & Naming
- Imports: stdlib → third-party → local (absolute imports, grouped with blank lines)
- Functions/methods/variables: `snake_case`
- Classes: `PascalCase`, Constants: `UPPER_CASE`, Private: `_leading_underscore`

### Type Hints & Error Handling
- Full type annotations using `typing` module (`Dict`, `List`, `Optional`, `Union`, etc.)
- Use `-> ReturnType` syntax
- Custom exceptions from `sensors/exceptions.py`, catch specific exceptions
- Use `@handle_sensor_exception` decorator for sensor operations

### Documentation & Structure
- Comprehensive docstrings with params, returns, exceptions
- Constants at module level in `UPPER_CASE`
- Private helpers prefixed with `_`, context managers for resources
- One class per file, f-strings for formatting

## Key Notes
- **AQI v2**: Uses atmospheric values only (matches AirNow, PurpleAir, IQAir)
- **Database**: SQLite path via `AQI_DB_PATH` env var
- **Sensor**: I2C address 0x19, bus 1
- **API**: Default port 5000
- **Scheduler**: Flexible intervals: "30m", "1h15m30s", etc.
- **Hardware tests**: Require actual sensor hardware