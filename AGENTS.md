# AGENTS.md - Development Guidelines for AQI Sensor Service

## Build/Lint/Test Commands

### Running the Application
- **Start**: `make start` or `./scripts/manage.sh start`
- **Stop**: `make stop` or `./scripts/manage.sh stop`
- **Restart**: `make restart` or `./scripts/manage.sh restart`
- **Status**: `make status` or `./scripts/manage.sh status`

### Testing
- No test framework currently configured
- No test files present in the codebase

### Linting/Formatting
- No linting tools currently configured (no black, flake8, ruff, mypy, etc.)
- No formatting tools configured

### Running a Single Test
- No tests currently exist to run

## Code Style Guidelines

### Python Version & Imports
- Use Python 3.x
- Include `from __future__ import annotations` at the top of all Python files
- Use absolute imports with relative path handling via `sys.path`
- Group imports: standard library, then third-party, then local modules
- Use `# noqa: E402` comments for import ordering issues when necessary

### Type Hints
- Use type hints for all function parameters and return values
- Use `typing` module imports for complex types (Dict, List, Tuple, etc.)
- Example: `def func(param: str) -> dict[str, Any]:`

### Naming Conventions
- **Variables/Functions**: `snake_case`
- **Constants**: `UPPER_CASE`
- **Classes**: `CamelCase`
- **Modules**: `snake_case`
- **Private methods**: `_leading_underscore`

### Documentation
- Use triple-quoted docstrings for all modules, classes, and functions
- Keep docstrings concise but descriptive
- Example: `"""Brief description of what this function does."""`

### Code Structure
- Use 4 spaces for indentation (standard Python)
- Line length: aim for 88 characters or less (Black default)
- Use blank lines to separate logical sections
- Use `self.` prefix for all instance variables and methods

### Error Handling
- Use specific exception types in `try/except` blocks
- Use `ValueError` for invalid input data
- Use `KeyError` for missing dictionary keys
- Include `# pragma: no cover` for defensive exception handling
- Log errors appropriately when needed

### String Formatting
- Use f-strings for string interpolation: `f"Value: {variable}"`
- Use triple quotes for multi-line strings

### File Paths
- Use `pathlib.Path` for path operations
- Avoid string concatenation for paths

### Database/SQL
- Use parameterized queries to prevent SQL injection
- Use descriptive table and column names
- Follow SQLite naming conventions

### HTTP/Web Standards
- Use appropriate HTTP status codes
- Return JSON responses with consistent structure
- Handle CORS and security headers appropriately

### Configuration
- Use TOML files for configuration (`.toml` extension)
- Separate configuration from code
- Use environment variables for sensitive data

### Logging
- Use Python's `logging` module when logging is needed
- Include timestamps and appropriate log levels
- Log to files in a `logs/` directory

### Web UI (JavaScript/HTML/CSS)
- Use Alpine.js for reactive components
- Use Chart.js for data visualization
- Follow semantic HTML structure
- Use CSS classes for styling
- Keep JavaScript modular and organized

### Scheduler/Service Management
- Use file-based locking for single-instance processes
- Handle process signals appropriately (SIGTERM, SIGINT)
- Use PID files for process management
- Include proper cleanup on shutdown

### Security Best Practices
- Validate all input data
- Use HTTPS in production
- Avoid exposing sensitive information in logs
- Implement proper authentication/authorization if needed
- Sanitize user inputs to prevent injection attacks

### Performance Considerations
- Use efficient data structures
- Minimize database queries
- Consider caching for frequently accessed data
- Use appropriate data types for storage and computation

### Development Workflow
- Test changes locally before deployment
- Use version control (Git) for all changes
- Document significant changes and new features
- Follow the existing code patterns and conventions</content>
<parameter name="filePath">/home/kdhpi/Documents/workk/code/sensors/AGENTS.md