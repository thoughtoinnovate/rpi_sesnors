# Code Review - Quick Action Items

## 🔴 Critical - Fix Immediately

### 1. Fix SQL Injection in `update_location` method
**File:** `aqi/aqi_app.py:234`  
**Fix:** Validate field names explicitly before using in query
```python
# Add explicit validation
for field in allowed_fields:
    if field in updates:
        # Double-check field is in allowed list
        if field not in allowed_fields:
            raise ValueError(f"Invalid field: {field}")
        update_fields.append(f"{field} = ?")
        values.append(updates[field])
```

### 2. Add Authentication to Admin Endpoint
**File:** `app/rest_api/app.py:567`  
**Fix:** Add token-based authentication
```python
ADMIN_TOKEN = os.getenv('ADMIN_API_TOKEN')
if not ADMIN_TOKEN:
    raise ValueError("ADMIN_API_TOKEN environment variable required")

@app.route('/api/admin/clear_data', methods=['POST'])
def clear_all_data():
    token = request.headers.get('X-Admin-Token')
    if token != ADMIN_TOKEN:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    # ... rest of code
```

### 3. Restrict CORS Configuration
**File:** `app/rest_api/app.py:55`  
**Fix:** Limit CORS to specific origins
```python
allowed_origins = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=allowed_origins, methods=['GET', 'POST'], max_age=3600)
```

---

## ⚠️ High Priority - Fix This Week

### 4. Add Input Validation for Location Names
**Files:** All endpoints accepting `location_name`  
**Fix:** Create validation function
```python
def validate_location_name(name: str) -> str:
    if not name or not isinstance(name, str):
        raise ValueError("Location name must be a non-empty string")
    name = re.sub(r'[<>"\';\\]', '', name).strip()
    if len(name) < 1 or len(name) > 100:
        raise ValueError("Location name must be 1-100 characters")
    return name
```

### 5. Sanitize Error Messages
**Files:** All API endpoints  
**Fix:** Don't expose internal error details
```python
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    return jsonify({
        'success': False,
        'error': 'An internal error occurred'  # Generic message
    }), 500
```

### 6. Replace Generic Exception Handlers
**Files:** 34 files with 196 instances  
**Fix:** Use specific exception types
- Replace `except Exception:` with specific exceptions
- Add proper exception hierarchy
- Log with `exc_info=True` for debugging

---

## 📝 Medium Priority - Fix This Month

### 7. Fix Inefficient Pagination
**Files:** `app/rest_api/app.py`, `aqi/aqi_app.py`  
**Fix:** Implement database-level pagination
- Add `limit` and `offset` parameters to database methods
- Use SQL `LIMIT` and `OFFSET` clauses
- Return total count separately

### 8. Improve Database Connection Management
**File:** `aqi/aqi_app.py:140`  
**Fix:** Use proper context managers
- Implement thread-local connections
- Add connection pooling
- Ensure proper cleanup

### 9. Fix Global State Management
**File:** `app/rest_api/app.py:62`  
**Fix:** Use thread-safe scheduler manager
- Create `SchedulerManager` class with locks
- Replace global variables

---

## 🔧 Low Priority - Nice to Have

### 10. Add Caching
- Cache location lookups
- Cache statistics
- Use Flask-Caching or similar

### 11. Fix N+1 Query Problem
- Use JOINs in database queries
- Fetch related data in single query

### 12. Add Rate Limiting
- Use Flask-Limiter
- Set limits per endpoint

### 13. Standardize Error Handling
- Create error handling decorator
- Consistent error response format

### 14. Add Input Validation Library
- Use Marshmallow or similar
- Validate all API inputs

### 15. Extract Configuration Constants
- Create constants file
- Replace magic numbers

---

## 📋 Testing Checklist

After fixes, verify:
- [ ] SQL injection tests pass
- [ ] Admin endpoint requires authentication
- [ ] CORS only allows configured origins
- [ ] Input validation works for all endpoints
- [ ] Error messages don't leak information
- [ ] Pagination works efficiently
- [ ] Database connections are properly managed
- [ ] Scheduler is thread-safe

---

## 🚀 Quick Wins (Can Do Today)

1. **Add environment variable for admin token** (5 min)
2. **Restrict CORS origins** (5 min)
3. **Add input validation for location names** (15 min)
4. **Sanitize error messages** (30 min)
5. **Extract configuration constants** (30 min)

**Total time:** ~1.5 hours for quick wins
