# Agent Guidelines for PM25 Sensor Codebase

## Build/Lint/Test Commands

### Testing
- **All tests**: `python -m pytest sensors/tests/ -v`
- **Single file**: `python -m pytest sensors/tests/test_aqi_v2.py -v`
- **With markers**: `python -m pytest sensors/tests/ -m hardware -v` (markers: hardware, comparison, performance, integration)
- **Single test**: `python -m pytest sensors/tests/test_aqi_v2.py::test_calculate_aqi_v2_basic -v`

### Build/Run
- **REST API**: `make start` (starts server on localhost:5000)
- **Stop API**: `make stop`, **Status**: `make status`, **Logs**: `make logs`

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
- Custom exceptions from `exceptions.py`, catch specific exceptions
- Use `@handle_sensor_exception` decorator for sensor operations

### Documentation & Structure
- Comprehensive docstrings with params, returns, exceptions
- Constants at module level in `UPPER_CASE`
- Private helpers prefixed with `_`, context managers for resources
- One class per file, f-strings for formatting</content>
<parameter name="filePath">/home/kdhpi/Documents/code_sensor/pm25/AGENTS.md