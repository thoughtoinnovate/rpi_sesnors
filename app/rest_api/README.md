# AQI REST API

Lightweight Flask-based REST API for Raspberry Pi 3 air quality monitoring. Provides efficient access to air quality data stored in SQLite database.

## Features

- **Lightweight**: Optimized for Raspberry Pi 3 resource constraints
- **RESTful**: Standard HTTP endpoints with JSON responses
- **CORS Enabled**: Supports web applications and cross-origin requests
- **Database Integration**: Uses existing AQI database functions
- **Pagination**: Efficient data retrieval with pagination support
- **Error Handling**: Comprehensive error responses and logging
- **Health Checks**: Built-in API health monitoring

## Quick Start

### Installation

```bash
cd app/rest_api/
pip install -r requirements.txt
```

### Running the API

```bash
# From rest_api directory
python run.py

# Or from project root
python app/rest_api/run.py

# Custom configuration
python run.py --host 0.0.0.0 --port 8080
```

The API will be available at `http://localhost:5000`

## API Endpoints

### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-18T13:15:30",
  "database_connected": true,
  "locations_count": 2,
  "version": "1.0.0"
}
```

### Get All Locations
```http
GET /api/locations
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "locations": [
    {
      "id": 1,
      "name": "Home Office",
      "latitude": 40.7128,
      "longitude": -74.006,
      "city": "New York",
      "country": "USA"
    }
  ]
}
```

### Get Latest Reading
```http
GET /api/latest/{location_name}
```

**Example:** `GET /api/latest/Home%20Office`

**Response:**
```json
{
  "success": true,
  "location": {
    "id": 1,
    "name": "Home Office",
    "latitude": 40.7128,
    "longitude": -74.006,
    "city": "New York",
    "country": "USA"
  },
  "latest_reading": {
    "id": 8,
    "timestamp": "2025-11-18T13:15:30",
    "pm1_0_atmospheric": 32.0,
    "pm2_5_atmospheric": 50.0,
    "pm10_atmospheric": 62.0,
    "pm1_0_standard": 45.0,
    "pm2_5_standard": 76.0,
    "pm10_standard": 84.0,
    "sensor_firmware_version": 32,
    "sensor_status": "awake",
    "is_warmed_up": 1,
    "aqi": {
      "value": 136,
      "level": "Unhealthy for Sensitive Groups",
      "color": "Orange",
      "source": "PM2.5",
      "health_message": "Sensitive groups may experience health effects"
    }
  }
}
```

### Get Historical Data
```http
GET /api/history/{location_name}?hours=24&limit=100
```

**Parameters:**
- `hours` (optional): Hours of historical data (default: 24, max: 168)
- `limit` (optional): Maximum readings to return (default: 100, max: 1000)

**Example:** `GET /api/history/Home%20Office?hours=48&limit=50`

**Response:**
```json
{
  "success": true,
  "location": { ... },
  "time_range": {
    "start": "2025-11-16T13:15:30",
    "end": "2025-11-18T13:15:30",
    "hours": 48
  },
  "count": 50,
  "readings": [
    {
      "id": 8,
      "timestamp": "2025-11-18T13:15:30",
      "pm1_0_atmospheric": 32.0,
      "pm2_5_atmospheric": 50.0,
      "pm10_atmospheric": 62.0,
      "aqi": {
        "value": 136,
        "level": "Unhealthy for Sensitive Groups",
        "color": "Orange",
        "source": "PM2.5"
      }
    }
  ]
}
```

### Get All Data (with Pagination)
```http
GET /api/all?page=1&per_page=50&location=Home%20Office
```

**Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 50, max: 200)
- `location` (optional): Filter by location name

**Response:**
```json
{
  "success": true,
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 150,
    "pages": 3
  },
  "count": 50,
  "readings": [ ... ]
}
```

### Get Location Statistics
```http
GET /api/stats/{location_name}?days=7
```

**Parameters:**
- `days` (optional): Days for statistics (default: 7, max: 30)

**Response:**
```json
{
  "success": true,
  "location": { ... },
  "time_period_days": 7,
  "statistics": {
    "total_readings": 168,
    "avg_aqi": 145.2,
    "min_aqi": 120,
    "max_aqi": 180
  },
  "summary": {
    "total_readings": 168,
    "avg_pm25": 52.3,
    "last_reading": "2025-11-18T13:15:30"
  }
}
```

## Configuration

### Environment Variables

- `AQI_DB_PATH`: Path to SQLite database file
  - Default: `../aqi_demo.db` (relative to rest_api directory)

### Command Line Options

```bash
python run.py --help
```

```
AQI REST API Server for Raspberry Pi 3

options:
  --host HOST       Host to bind server to (default: 127.0.0.1)
  --port PORT       Port to bind server to (default: 5000)
  --debug           Enable debug mode (not recommended for production)
  --workers WORKERS Number of worker threads (default: 1 for RPi)
```

## Testing with Real Sensor Data

Since this API works with real PM25 sensor data, testing should be done with an actual sensor connected. Here's how to test the API:

### Start the API Server
```bash
cd app/rest_api/
python run.py --host 0.0.0.0 --port 5000
```

### Test Endpoints with Real Data
```bash
# Check API health
curl http://localhost:5000/api/health

# Get monitoring locations
curl http://localhost:5000/api/locations

# Get latest real sensor reading
curl "http://localhost:5000/api/latest/Home%20Office"

# Get real historical data (last 2 hours)
curl "http://localhost:5000/api/history/Home%20Office?hours=2"

# Get real statistics
curl "http://localhost:5000/api/stats/Home%20Office?days=1"
```

### Expected Real Data Response
```json
{
  "success": true,
  "latest_reading": {
    "pm2_5_atmospheric": 52.0,
    "aqi": {
      "value": 141,
      "level": "Unhealthy for Sensitive Groups",
      "color": "Orange"
    }
  }
}
```

**Note:** All testing uses real sensor data from connected PM25 sensors. No mock or dummy data is used.

## Usage Examples

### Python Client

```python
import requests

# Get latest reading
response = requests.get('http://localhost:5000/api/latest/Home%20Office')
data = response.json()

if data['success']:
    pm25 = data['latest_reading']['pm2_5_atmospheric']
    aqi = data['latest_reading']['aqi']['value']
    print(f"PM2.5: {pm25} μg/m³, AQI: {aqi}")

# Get historical data
response = requests.get('http://localhost:5000/api/history/Home%20Office?hours=24')
data = response.json()

for reading in data['readings']:
    print(f"{reading['timestamp']}: AQI {reading['aqi']['value']}")
```

### JavaScript (Browser)

```javascript
// Get latest data
fetch('/api/latest/Home Office')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      const pm25 = data.latest_reading.pm2_5_atmospheric;
      const aqi = data.latest_reading.aqi.value;
      console.log(`PM2.5: ${pm25} μg/m³, AQI: ${aqi}`);
    }
  });

// Get historical data
fetch('/api/history/Home Office?hours=24')
  .then(response => response.json())
  .then(data => {
    data.readings.forEach(reading => {
      console.log(`${reading.timestamp}: AQI ${reading.aqi.value}`);
    });
  });
```

### cURL Examples

```bash
# Health check
curl http://localhost:5000/api/health

# Get locations
curl http://localhost:5000/api/locations

# Get latest reading
curl "http://localhost:5000/api/latest/Home%20Office"

# Get 48 hours of historical data
curl "http://localhost:5000/api/history/Home%20Office?hours=48"

# Get paginated data
curl "http://localhost:5000/api/all?page=1&per_page=20"

# Get statistics
curl "http://localhost:5000/api/stats/Home%20Office?days=7"
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error description"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: Not found (location or endpoint)
- `500`: Internal server error

## Performance Optimization

### For Raspberry Pi 3

- **Threading**: Enabled for concurrent requests
- **Connection Pooling**: Efficient database connections
- **Pagination**: Prevents large data transfers
- **Compression**: Flask handles response compression
- **Minimal Dependencies**: Only essential packages

### Database Optimization

- **Indexes**: Leverages existing database indexes
- **Query Limits**: Prevents excessive data retrieval
- **Connection Reuse**: Efficient database connection handling
- **Read-Only Operations**: Optimized for data retrieval

## Deployment

### Systemd Service (Recommended for RPi)

Create `/etc/systemd/system/aqi-api.service`:

```ini
[Unit]
Description=AQI REST API Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pm25/app/rest_api
ExecStart=/usr/bin/python3 run.py --host 0.0.0.0 --port 5000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Commands:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable aqi-api
sudo systemctl start aqi-api
sudo systemctl status aqi-api
```

### Nginx Reverse Proxy (Optional)

For production deployment with SSL:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring

### Health Checks

The API includes built-in health monitoring:

```bash
# Check API health
curl http://localhost:5000/api/health

# Monitor with cron
*/5 * * * * curl -f http://localhost:5000/api/health || echo "API down"
```

### Logs

Logs are written to stdout/stderr. For systemd service:

```bash
sudo journalctl -u aqi-api -f
```

## Troubleshooting

### Common Issues

**Database not found:**
```bash
# Set correct database path
export AQI_DB_PATH=/path/to/your/database.db
python run.py
```

**Port already in use:**
```bash
# Use different port
python run.py --port 8080
```

**Permission denied:**
```bash
# Run with proper user or adjust permissions
sudo -u www-data python run.py
```

**High memory usage:**
- Reduce `per_page` limit in requests
- Use pagination for large datasets
- Monitor with `htop` or `free -h`

### Performance Tuning

**For high-traffic scenarios:**
- Increase `--workers` (but monitor RPi resources)
- Use database connection pooling
- Implement caching for frequent queries
- Consider uWSGI instead of Flask development server

## API Versioning

Current version: `1.0.0`

Future versions will maintain backward compatibility. Breaking changes will be indicated by major version increments.

## Contributing

The API is designed to be extensible. New endpoints can be added by:

1. Adding route functions to `app.py`
2. Using the existing `get_database()` helper
3. Following the established response format
4. Adding appropriate error handling

## License

This API is part of the PM25 air quality monitoring project.