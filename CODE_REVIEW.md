# Code Review - PM25 Sensor Codebase

**Date:** 2025-01-XX  
**Reviewer:** AI Code Review  
**Scope:** Security, Performance, Code Quality, Best Practices

---

## 🔴 Critical Issues

### 1. SQL Injection Vulnerability (HIGH PRIORITY)

**Location:** `aqi/aqi_app.py:234`

```python
# CURRENT CODE (VULNERABLE):
query = f"UPDATE locations SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
```

**Issue:** While using parameterized queries for values, the field names are constructed via string formatting, which could be exploited if `allowed_fields` validation is bypassed.

**Recommendation:**
```python
# SAFE APPROACH:
allowed_fields = ['name', 'latitude', 'longitude', 'city', 'country', 'description', 'is_active']
update_fields = []
placeholders = []
values = []

for field in allowed_fields:
    if field in updates:
        # Validate field name is in allowed list
        if field not in allowed_fields:
            raise ValueError(f"Invalid field: {field}")
        update_fields.append(f"{field} = ?")
        values.append(updates[field])

if not update_fields:
    return False

values.append(location_id)
query = f"UPDATE locations SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
cursor.execute(query, values)
```

**Alternative:** Use an ORM (SQLAlchemy) or a query builder library.

---

### 2. Weak Admin Authentication (HIGH PRIORITY)

**Location:** `app/rest_api/app.py:567-608`

**Issue:** The admin endpoint `/api/admin/clear_data` only requires a confirmation string, no actual authentication.

**Current:**
```python
confirm = data.get('confirm')
if confirm != 'CLEAR_ALL_DATA':
    return jsonify({'success': False, 'error': 'Confirmation required...'}), 400
```

**Recommendation:**
```python
import os
from functools import wraps
from flask import request

ADMIN_TOKEN = os.getenv('ADMIN_API_TOKEN')

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-Admin-Token') or request.json.get('admin_token')
        if not token or token != ADMIN_TOKEN:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/admin/clear_data', methods=['POST'])
@require_admin
def clear_all_data():
    # ... existing code
```

**Additional:** Consider implementing proper authentication (JWT, API keys, etc.) for production.

---

### 3. CORS Configuration Without Restrictions (MEDIUM PRIORITY)

**Location:** `app/rest_api/app.py:55-56`

**Issue:** CORS is enabled for all origins without restrictions.

**Current:**
```python
if CORS:
    CORS(app)  # Enable CORS for web applications
```

**Recommendation:**
```python
if CORS:
    # Restrict to specific origins in production
    allowed_origins = os.getenv('CORS_ALLOWED_ORIGINS', '*').split(',')
    CORS(app, origins=allowed_origins, methods=['GET', 'POST'], max_age=3600)
```

---

## ⚠️ Security Concerns

### 4. Input Validation for Location Names

**Location:** Multiple endpoints accepting `location_name` parameter

**Issue:** Location names are used directly in database queries without sanitization.

**Recommendation:**
```python
import re

def validate_location_name(name: str) -> str:
    """Validate and sanitize location name."""
    if not name or not isinstance(name, str):
        raise ValueError("Location name must be a non-empty string")
    
    # Remove potentially dangerous characters
    name = re.sub(r'[<>"\';\\]', '', name).strip()
    
    if len(name) < 1 or len(name) > 100:
        raise ValueError("Location name must be 1-100 characters")
    
    return name

# Use in endpoints:
@app.route('/api/latest/<location_name>', methods=['GET'])
def get_latest_reading(location_name):
    try:
        location_name = validate_location_name(location_name)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    # ... rest of code
```

---

### 5. Error Message Information Disclosure

**Location:** Multiple locations

**Issue:** Some error messages expose internal details (stack traces, file paths, etc.).

**Example:**
```python
# CURRENT:
except Exception as e:
    logger.error(f"Failed to get locations: {e}")
    return jsonify({
        'success': False,
        'error': str(e)  # May expose internal details
    }), 500
```

**Recommendation:**
```python
# PRODUCTION-SAFE:
except Exception as e:
    logger.error(f"Failed to get locations: {e}", exc_info=True)
    # Don't expose internal error details to clients
    return jsonify({
        'success': False,
        'error': 'An internal error occurred. Please try again later.'
    }), 500
```

---

## 🐛 Code Quality Issues

### 6. Excessive Use of Bare Exception Handlers

**Location:** Found 196 instances across 34 files

**Issue:** Too many `except Exception:` or `except:` blocks make debugging difficult and can hide bugs.

**Examples:**
- `app/rest_api/app.py:87` - Catching all exceptions in health check
- `sensors/pm25_sensor.py:120` - Generic exception handling

**Recommendation:**
```python
# BAD:
try:
    # code
except Exception as e:
    logger.error(f"Error: {e}")

# GOOD:
try:
    # code
except SensorNotRespondingError as e:
    logger.error(f"Sensor not responding: {e}")
    raise
except CommunicationError as e:
    logger.error(f"Communication error: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise  # Re-raise or handle appropriately
```

**Action Items:**
- Replace generic exception handlers with specific exception types
- Only catch exceptions you can handle meaningfully
- Always log with `exc_info=True` for unexpected exceptions

---

### 7. Inefficient Pagination Implementation

**Location:** `app/rest_api/app.py:127-134`, `aqi/aqi_app.py:343+`

**Issue:** Loading all data into memory then slicing for pagination.

**Current:**
```python
locations = db.list_locations()  # Loads ALL locations
total = len(locations)
offset = (page - 1) * per_page
paginated_locations = locations[offset:offset + per_page]  # Then slices
```

**Recommendation:**
```python
# Implement pagination at database level:
def list_locations(self, active_only: bool = True, limit: int = None, offset: int = None) -> Tuple[List[Dict[str, Any]], int]:
    """List locations with pagination."""
    with self._get_connection() as conn:
        cursor = conn.cursor()
        
        # Get total count
        count_query = 'SELECT COUNT(*) FROM locations WHERE is_active = 1' if active_only else 'SELECT COUNT(*) FROM locations'
        cursor.execute(count_query)
        total = cursor.fetchone()[0]
        
        # Get paginated results
        query = 'SELECT * FROM locations'
        if active_only:
            query += ' WHERE is_active = 1'
        query += ' ORDER BY name'
        
        if limit is not None:
            query += f' LIMIT {limit}'
        if offset is not None:
            query += f' OFFSET {offset}'
        
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()], total
```

---

### 8. Database Connection Management

**Location:** `aqi/aqi_app.py:140-145`

**Issue:** Connection is stored as instance variable but not properly managed as context manager in all cases.

**Current:**
```python
def _get_connection(self) -> sqlite3.Connection:
    if self._connection is None:
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
    return self._connection
```

**Issues:**
- Connection may not be closed properly
- No connection pooling
- Potential connection leaks in long-running processes

**Recommendation:**
```python
from contextlib import contextmanager
import threading

class AQIDatabase:
    def __init__(self, db_path: Union[str, Path] = "aqi_monitoring.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self._local = threading.local()  # Thread-local storage
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = getattr(self._local, 'connection', None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._local.connection = conn
        
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            # Don't close here - keep connection for thread lifetime
            pass
    
    def close(self):
        """Close thread-local connection."""
        conn = getattr(self._local, 'connection', None)
        if conn:
            conn.close()
            self._local.connection = None
```

**Better:** Use connection pooling library or SQLAlchemy.

---

### 9. Global State Management

**Location:** `app/rest_api/app.py:62-63`

**Issue:** Global variables for scheduler state are not thread-safe.

**Current:**
```python
# Global scheduler management
scheduler = None
scheduler_thread = None
```

**Recommendation:**
```python
import threading

class SchedulerManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._scheduler = None
        self._thread = None
    
    def start(self, location: str, interval_seconds: int, db_path: str):
        with self._lock:
            if self._scheduler and self._scheduler.running:
                raise ValueError("Scheduler already running")
            
            self._scheduler = AQIScheduler(location, interval_seconds, db_path)
            self._thread = threading.Thread(target=self._scheduler.run, daemon=True)
            self._thread.start()
    
    def stop(self):
        with self._lock:
            if self._scheduler and self._scheduler.running:
                self._scheduler.running = False
                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=10)
    
    def get_status(self):
        with self._lock:
            if self._scheduler:
                return self._scheduler.get_status()
            return {'running': False, ...}

# Replace global variables:
scheduler_manager = SchedulerManager()
```

---

## ⚡ Performance Issues

### 10. Missing Caching for Frequently Accessed Data

**Location:** Multiple endpoints

**Issue:** No caching for location data, statistics, or sensor readings.

**Recommendation:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache location lookups (5 minute TTL)
@lru_cache(maxsize=100)
def get_cached_location(name: str, cache_time: float):
    # cache_time used to invalidate cache
    return db.get_location_by_name(name)

# Or use Flask-Caching:
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/locations', methods=['GET'])
@cache.cached(timeout=300)  # 5 minutes
def get_locations():
    # ... existing code
```

---

### 11. N+1 Query Problem

**Location:** `aqi/aqi_app.py:343+` (get_recent_readings)

**Issue:** When fetching readings with AQI data, may result in multiple queries.

**Recommendation:** Use JOINs to fetch all data in single query:
```python
query = '''
    SELECT
        r.*,
        a.aqi_value, a.aqi_level, a.aqi_color, a.aqi_source, a.health_message,
        l.name as location_name
    FROM readings r
    LEFT JOIN aqi_calculations a ON r.id = a.reading_id
    LEFT JOIN locations l ON r.location_id = l.id
    WHERE r.location_id = ? OR ? IS NULL
    ORDER BY r.timestamp DESC
    LIMIT ?
'''
```

---

## 📝 Code Style & Best Practices

### 12. Missing Type Hints

**Location:** Various files

**Issue:** Some functions lack complete type hints.

**Recommendation:** Add comprehensive type hints:
```python
# BEFORE:
def get_location_by_name(self, name: str):
    # ...

# AFTER:
def get_location_by_name(self, name: str) -> Optional[Dict[str, Any]]:
    # ...
```

---

### 13. Inconsistent Error Handling Patterns

**Location:** Throughout codebase

**Issue:** Mix of exception handling approaches.

**Recommendation:** Standardize error handling:
```python
# Create a decorator for API endpoints:
from functools import wraps

def handle_api_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except NotFoundError as e:
            return jsonify({'success': False, 'error': str(e)}), 404
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}", exc_info=True)
            return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return decorated_function

@app.route('/api/locations', methods=['GET'])
@handle_api_errors
def get_locations():
    # ... code without try/except
```

---

### 14. Missing Input Validation

**Location:** Multiple API endpoints

**Issue:** Some endpoints don't validate input ranges or types thoroughly.

**Recommendation:** Use a validation library:
```python
from marshmallow import Schema, fields, validate, ValidationError

class LocationQuerySchema(Schema):
    page = fields.Int(validate=validate.Range(min=1), missing=1)
    per_page = fields.Int(validate=validate.Range(min=1, max=200), missing=50)

@app.route('/api/locations', methods=['GET'])
def get_locations():
    try:
        params = LocationQuerySchema().load(request.args)
    except ValidationError as err:
        return jsonify({'success': False, 'error': err.messages}), 400
    
    page = params['page']
    per_page = params['per_page']
    # ... rest of code
```

---

### 15. Hardcoded Configuration Values

**Location:** Multiple files

**Issue:** Magic numbers and hardcoded values throughout code.

**Examples:**
- `app/rest_api/app.py:121` - `per_page > 200`
- `app/rest_api/app.py:226` - `hours > 168`

**Recommendation:**
```python
# Create constants file:
# app/rest_api/constants.py
MAX_PAGE_SIZE = 200
MAX_HISTORY_HOURS = 168
DEFAULT_PAGE_SIZE = 50
DEFAULT_HISTORY_HOURS = 24

# Use in code:
if per_page > MAX_PAGE_SIZE:
    return jsonify({'error': f'per_page must be <= {MAX_PAGE_SIZE}'}), 400
```

---

## 🔧 Architecture Suggestions

### 16. Separate Business Logic from API Layer

**Issue:** Business logic mixed with API endpoint handlers.

**Recommendation:** Create service layer:
```python
# app/rest_api/services/location_service.py
class LocationService:
    def __init__(self, db: AQIDatabase):
        self.db = db
    
    def get_locations(self, page: int, per_page: int) -> Dict[str, Any]:
        # Business logic here
        locations, total = self.db.list_locations(limit=per_page, offset=(page-1)*per_page)
        return {
            'locations': locations,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }

# In app.py:
@app.route('/api/locations', methods=['GET'])
def get_locations():
    service = LocationService(get_database())
    return jsonify(service.get_locations(page, per_page))
```

---

### 17. Add Rate Limiting

**Recommendation:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/sensor/reading', methods=['GET'])
@limiter.limit("10 per minute")
def get_sensor_reading():
    # ... existing code
```

---

### 18. Add Request/Response Logging Middleware

**Recommendation:**
```python
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status_code} for {request.path}")
    return response
```

---

## 📊 Summary

### Priority Breakdown:

**🔴 Critical (Fix Immediately):**
1. SQL Injection vulnerability (#1)
2. Weak admin authentication (#2)
3. CORS without restrictions (#3)

**⚠️ High Priority:**
4. Input validation (#4)
5. Error message disclosure (#5)
6. Excessive exception handlers (#6)

**📝 Medium Priority:**
7. Inefficient pagination (#7)
8. Database connection management (#8)
9. Global state management (#9)
10. Missing caching (#10)

**🔧 Low Priority (Improvements):**
11. N+1 queries (#11)
12. Type hints (#12)
13. Error handling patterns (#13)
14. Input validation library (#14)
15. Configuration constants (#15)
16. Service layer (#16)
17. Rate limiting (#17)
18. Request logging (#18)

### Estimated Effort:
- **Critical fixes:** 4-6 hours
- **High priority:** 8-12 hours
- **Medium priority:** 12-16 hours
- **Low priority:** 16-24 hours

**Total estimated effort:** 40-58 hours

---

## ✅ Positive Aspects

1. **Good use of parameterized queries** (most places)
2. **Comprehensive error handling structure** (custom exceptions)
3. **Type hints in most places**
4. **Good documentation** (docstrings)
5. **Modular architecture**
6. **Comprehensive test suite**

---

## 📚 Recommended Reading

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [SQLite Best Practices](https://www.sqlite.org/security.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
