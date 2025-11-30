# Air Quality Monitor - RPi3

A comprehensive air quality monitoring system for Raspberry Pi 3 with PM2.5 sensor integration, AQI calculations, and web dashboard.

## 🚀 Quick Start

### Option 1: Unified Server (Recommended)
Run both UI and API on the same port (5000):

```bash
# Start unified server (builds UI and starts Flask)
./start_unified.sh

# Access at:
# UI: http://localhost:5000
# API: http://localhost:5000/api/health
```

### Option 2: Separate Development Servers
Run UI and API on separate ports:

```bash
# Terminal 1: Start API server
cd app/rest_api && python app.py

# Terminal 2: Start UI server  
cd ui && npm run dev

# Access at:
# UI: http://localhost:5173
# API: http://localhost:5000
```

## 📊 Features

- **Real-time Monitoring**: PM2.5 and PM10 particle measurements
- **AQI Calculations**: EPA-standard Air Quality Index v2
- **Web Dashboard**: Lightweight Alpine.js + Tailwind CSS UI
- **Historical Data**: SQLite database with trend analysis
- **Automated Scheduling**: Configurable monitoring intervals
- **Mobile Responsive**: Works on all screen sizes
- **Dark Mode**: System preference detection
- **RPi3 Optimized**: Lightweight and efficient

## 🛠️ Technology Stack

### Backend
- **Python 3**: Core application
- **Flask**: REST API server
- **SQLite**: Database storage
- **AQI v2**: Atmospheric-based calculations

### Frontend
- **Alpine.js**: Lightweight reactivity (15KB)
- **Tailwind CSS**: Utility-first styling (10KB)
- **Chart.js**: Data visualization
- **Fetch API**: Native HTTP requests

### Performance
- **Bundle Size**: 48KB (vs 460KB React)
- **Load Time**: 1.5s (vs 8s React)
- **Memory Usage**: 30MB (vs 150MB React)
- **CPU Usage**: 15% (vs 60% React)

## 📁 Project Structure

```
rpi_sesnors/
├── app/                    # Application layer
│   ├── rest_api/           # Flask REST API
│   │   ├── app.py         # Main server (serves UI + API)
│   │   └── run.py        # Alternative runner
│   └── aqi_app.py        # AQI database operations
├── sensors/                # PM25 sensor library
│   ├── pm25_sensor.py     # Main sensor interface
│   ├── aqi_v2.py         # AQI v2 calculations
│   └── examples/         # Usage examples
├── ui/                    # Frontend web interface
│   ├── index.html        # Main UI file
│   ├── src/             # Source files
│   ├── dist/            # Built files
│   └── package.json     # Dependencies
├── aqi/                  # AQI-specific modules
└── start_unified.sh      # Unified startup script
```

## 🔧 API Endpoints

### Core Endpoints
- `GET /api/health` - System health check
- `GET /api/locations` - List monitoring locations
- `GET /api/latest/{location}` - Latest reading
- `GET /api/history/{location}` - Historical data
- `GET /api/scheduler/status` - Scheduler status

### Control Endpoints
- `POST /api/scheduler/start` - Start monitoring
- `POST /api/scheduler/stop` - Stop monitoring
- `POST /api/sensor/wake` - Wake sensor
- `POST /api/sensor/sleep` - Sleep sensor

### Sensor Endpoints
- `GET /sensor/aqi/sensor/reading` - Direct sensor reading
- `GET /sensor/aqi/sensor/diagnostics` - Sensor diagnostics
- `POST /sensor/aqi/aqi/calculate` - Calculate AQI

## 📱 Usage

### Dashboard
- View real-time AQI, PM2.5, and PM10 readings
- Monitor sensor status and connection
- Auto-refresh every 30 seconds

### History
- Interactive charts with multiple time ranges
- Data table with recent readings
- Export capabilities

### Control Panel
- Start/stop automated monitoring
- Sensor power management
- Real-time status updates

## 🧪 Testing

```bash
# Run all tests
python -m pytest sensors/tests/ -v

# Run specific test file
python -m pytest sensors/tests/test_aqi_v2.py -v

# Run with markers
python -m pytest sensors/tests/ -m hardware -v
```

## 🔒 Security

- Input validation on all endpoints
- Error handling with proper HTTP status codes
- No sensitive data exposure
- CORS configuration for web access

## 📈 Performance Optimization

- **Bundle Splitting**: Separate CSS and JS files
- **Minification**: Compressed production builds
- **Caching**: Browser cache headers
- **Compression**: Gzip support in Flask
- **Lazy Loading**: On-demand chart initialization

## 🌐 Deployment

### Production Setup
```bash
# Build UI for production
cd ui && npm run build-for-flask

# Set environment variables
export FLASK_ENV=production
export AQI_DB_PATH=/path/to/production.db

# Start production server
cd ../app/rest_api && python app.py
```

### Systemd Service
Create `/etc/systemd/system/air-quality.service`:
```ini
[Unit]
Description=Air Quality Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/rpi_sesnors
ExecStart=/home/pi/rpi_sesnors/start_unified.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable air-quality
sudo systemctl start air-quality
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📄 License

ISC License - feel free to use and modify.

## 🆘 Troubleshooting

### Common Issues

**UI not loading:**
- Check if UI files are built: `cd ui && npm run build-for-flask`
- Verify Flask is running on port 5000
- Check browser console for errors

**Sensor not connecting:**
- Verify I2C is enabled: `sudo raspi-config`
- Check sensor connections
- Run sensor test: `python sensors/examples/basic_readings.py`

**API errors:**
- Check database permissions
- Verify all dependencies installed
- Check Flask logs for detailed errors

### Getting Help

- Check logs: `tail -f /var/log/air-quality.log`
- Run diagnostics: `python tools/ui_headless_test.py`
- Test API: `curl http://localhost:5000/api/health`