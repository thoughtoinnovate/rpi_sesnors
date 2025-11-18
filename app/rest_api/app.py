"""
AQI REST API - Lightweight Flask Application for Raspberry Pi 3

This module provides REST API endpoints for accessing air quality monitoring data
stored in the SQLite database. Designed to be lightweight and efficient for RPi3.

Endpoints:
- GET /api/locations - Get all monitoring locations
- GET /api/latest/<location_name> - Get latest reading for a location
- GET /api/history/<location_name> - Get historical data for a location
- GET /api/history/<location_name>?hours=24 - Get data for last N hours
- GET /api/all - Get all data with pagination
- GET /api/stats/<location_name> - Get statistics for a location
- GET /api/health - API health check
- POST /api/scheduler/start - Start AQI scheduler
- POST /api/scheduler/stop - Stop AQI scheduler
- GET /api/scheduler/status - Get scheduler status
- POST /api/admin/clear_data - Clear all database data (admin only)
- GET /api/sensor/reading - Get raw sensor reading data
- POST /api/sensor/calculate_aqi - Calculate AQI from raw PM data

All endpoints return JSON responses optimized for low-bandwidth connections.
"""

import os
import sys
from pathlib import Path

# Add parent directories to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))

from flask import Flask, jsonify, request, abort
try:
    from flask_cors import CORS
except ImportError:
    # Fallback if CORS is not available
    CORS = None
import sqlite3
from datetime import datetime, timedelta
import logging
import threading
import time

from aqi.aqi_app import AQIDatabase
from aqi.scheduler import AQIScheduler, TimeParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
if CORS:
    CORS(app)  # Enable CORS for web applications

# Database configuration
DEFAULT_DB_PATH = os.getenv('AQI_DB_PATH', str(current_dir.parent / 'aqi_demo.db'))

# Global scheduler management
scheduler = None
scheduler_thread = None

def get_database():
    """Get database connection with error handling."""
    try:
        return AQIDatabase(DEFAULT_DB_PATH)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        abort(500, description="Database connection failed")

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint."""
    try:
        with get_database() as db:
            # Quick database check
            locations = db.list_locations()

            # Check sensor availability
            sensor_available = False
            try:
                from sensors.pm25_sensor import PM25Sensor
                sensor = PM25Sensor(auto_connect=False)
                sensor_available = True
            except Exception as e:
                logger.debug(f"Sensor not available: {e}")

            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database_connected': True,
                'locations_count': len(locations),
                'sensor_available': sensor_available,
                'version': '1.0.0'
            })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get all monitoring locations."""
    try:
        # Parse query parameters
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=50, type=int)

        # Validate parameters
        if page < 1:
            return jsonify({
                'success': False,
                'error': 'Page must be >= 1'
            }), 400

        if per_page < 1 or per_page > 200:
            return jsonify({
                'success': False,
                'error': 'per_page must be between 1 and 200'
            }), 400

        with get_database() as db:
            locations = db.list_locations()
            total = len(locations)
            pages = (total + per_page - 1) // per_page

            # Apply pagination
            offset = (page - 1) * per_page
            paginated_locations = locations[offset:offset + per_page]

            return jsonify({
                'success': True,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': pages
                },
                'count': len(paginated_locations),
                'locations': paginated_locations
            })
    except Exception as e:
        logger.error(f"Failed to get locations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/latest/<location_name>', methods=['GET'])
def get_latest_reading(location_name):
    """Get the latest reading for a specific location."""
    try:
        with get_database() as db:
            # Get location info first
            location = db.get_location_by_name(location_name)
            if not location:
                return jsonify({
                    'success': False,
                    'error': f'Location "{location_name}" not found'
                }), 404

            # Get latest reading with AQI data
            readings = db.get_recent_readings(location_id=location['id'], limit=1)

            if not readings:
                return jsonify({
                    'success': False,
                    'error': f'No readings found for location "{location_name}"'
                }), 404

            reading = readings[0]

            # Format response
            response = {
                'success': True,
                'location': location,
                'latest_reading': {
                    'id': reading['id'],
                    'timestamp': reading['timestamp'],
                    'pm1_0_atmospheric': reading['pm1_0_atmospheric'],
                    'pm2_5_atmospheric': reading['pm2_5_atmospheric'],
                    'pm10_atmospheric': reading['pm10_atmospheric'],
                    'pm1_0_standard': reading['pm1_0_standard'],
                    'pm2_5_standard': reading['pm2_5_standard'],
                    'pm10_standard': reading['pm10_standard'],
                    'sensor_firmware_version': reading['sensor_firmware_version'],
                    'sensor_status': reading['sensor_status'],
                    'is_warmed_up': reading['is_warmed_up']
                }
            }

            # Add AQI data if available
            if reading.get('aqi_value'):
                response['latest_reading']['aqi'] = {
                    'value': reading['aqi_value'],
                    'level': reading['aqi_level'],
                    'color': reading['aqi_color'],
                    'source': reading['aqi_source'],
                    'health_message': reading.get('health_message')
                }

            return jsonify(response)

    except Exception as e:
        logger.error(f"Failed to get latest reading for {location_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/history/<location_name>', methods=['GET'])
def get_historical_data(location_name):
    """Get historical data for a specific location."""
    try:
        # Parse query parameters
        hours = request.args.get('hours', default=24, type=int)
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=100, type=int)

        # Validate parameters
        if hours < 1 or hours > 168:  # Max 1 week
            return jsonify({
                'success': False,
                'error': 'Hours must be between 1 and 168 (1 week)'
            }), 400

        if page < 1:
            return jsonify({
                'success': False,
                'error': 'Page must be >= 1'
            }), 400

        if per_page < 1 or per_page > 1000:
            return jsonify({
                'success': False,
                'error': 'per_page must be between 1 and 1000'
            }), 400

        with get_database() as db:
            # Get location info
            location = db.get_location_by_name(location_name)
            if not location:
                return jsonify({
                    'success': False,
                    'error': f'Location "{location_name}" not found'
                }), 404

            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)

            # Get historical readings
            readings = db.get_readings_by_date_range(
                start_time.isoformat(),
                end_time.isoformat(),
                location_id=location['id']
            )

            # Apply pagination
            total = len(readings)
            pages = (total + per_page - 1) // per_page
            offset = (page - 1) * per_page
            readings = readings[offset:offset + per_page]

            # Format response
            formatted_readings = []
            for reading in readings:
                formatted_reading = {
                    'id': reading['id'],
                    'timestamp': reading['timestamp'],
                    'pm1_0_atmospheric': reading['pm1_0_atmospheric'],
                    'pm2_5_atmospheric': reading['pm2_5_atmospheric'],
                    'pm10_atmospheric': reading['pm10_atmospheric'],
                    'pm1_0_standard': reading['pm1_0_standard'],
                    'pm2_5_standard': reading['pm2_5_standard'],
                    'pm10_standard': reading['pm10_standard']
                }

                # Add AQI data if available
                if reading.get('aqi_value'):
                    formatted_reading['aqi'] = {
                        'value': reading['aqi_value'],
                        'level': reading['aqi_level'],
                        'color': reading['aqi_color'],
                        'source': reading['aqi_source']
                    }

                formatted_readings.append(formatted_reading)

            return jsonify({
                'success': True,
                'location': location,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'hours': hours
                },
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': pages
                },
                'count': len(formatted_readings),
                'readings': formatted_readings
            })

    except Exception as e:
        logger.error(f"Failed to get historical data for {location_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/all', methods=['GET'])
def get_all_data():
    """Get all data with pagination."""
    try:
        # Parse query parameters
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=50, type=int)
        location_name = request.args.get('location')

        # Validate parameters
        if page < 1:
            return jsonify({
                'success': False,
                'error': 'Page must be >= 1'
            }), 400

        if per_page < 1 or per_page > 200:
            return jsonify({
                'success': False,
                'error': 'per_page must be between 1 and 200'
            }), 400

        with get_database() as db:
            # Get location filter if specified
            location_filter = None
            if location_name:
                location = db.get_location_by_name(location_name)
                if not location:
                    return jsonify({
                        'success': False,
                        'error': f'Location "{location_name}" not found'
                    }), 404
                location_filter = location['id']

            # Calculate offset
            offset = (page - 1) * per_page

            # Get readings with pagination
            readings = db.get_recent_readings(
                location_id=location_filter,
                limit=per_page * page  # Get enough for pagination
            )

            # Apply pagination
            total_readings = len(readings)
            paginated_readings = readings[offset:offset + per_page]

            # Format response
            formatted_readings = []
            for reading in paginated_readings:
                formatted_reading = {
                    'id': reading['id'],
                    'timestamp': reading['timestamp'],
                    'location_name': reading['location_name'],
                    'pm1_0_atmospheric': reading['pm1_0_atmospheric'],
                    'pm2_5_atmospheric': reading['pm2_5_atmospheric'],
                    'pm10_atmospheric': reading['pm10_atmospheric']
                }

                # Add AQI data if available
                if reading.get('aqi_value'):
                    formatted_reading['aqi'] = {
                        'value': reading['aqi_value'],
                        'level': reading['aqi_level'],
                        'color': reading['aqi_color']
                    }

                formatted_readings.append(formatted_reading)

            return jsonify({
                'success': True,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_readings,
                    'pages': (total_readings + per_page - 1) // per_page
                },
                'count': len(formatted_readings),
                'readings': formatted_readings
            })

    except Exception as e:
        logger.error(f"Failed to get all data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats/<location_name>', methods=['GET'])
def get_location_stats(location_name):
    """Get statistics for a specific location."""
    try:
        # Parse query parameters
        days = request.args.get('days', default=7, type=int)

        # Validate parameters
        if days < 1 or days > 30:
            return jsonify({
                'success': False,
                'error': 'Days must be between 1 and 30'
            }), 400

        with get_database() as db:
            # Get location info
            location = db.get_location_by_name(location_name)
            if not location:
                return jsonify({
                    'success': False,
                    'error': f'Location "{location_name}" not found'
                }), 404

            # Get statistics
            stats = db.get_aqi_statistics(location_id=location['id'], days=days)

            # Get location summary
            summary = db.get_location_summary(location['id'])

            return jsonify({
                'success': True,
                'location': location,
                'time_period_days': days,
                'statistics': stats,
                'summary': summary.get('statistics', {}) if summary else {}
            })

    except Exception as e:
        logger.error(f"Failed to get stats for {location_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Scheduler Management Endpoints
@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the AQI scheduler with specified location and interval."""
    global scheduler, scheduler_thread

    if scheduler and scheduler.running:
        return jsonify({
            'success': False,
            'error': 'Scheduler is already running'
        }), 400

    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': 'JSON body required'
        }), 400

    location = data.get('location')
    interval_str = data.get('interval')

    if not location or not interval_str:
        return jsonify({
            'success': False,
            'error': 'location and interval are required'
        }), 400

    try:
        interval_seconds = TimeParser.parse_time_interval(interval_str)
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid interval format: {e}'
        }), 400

    try:
        scheduler = AQIScheduler(location, interval_seconds, DEFAULT_DB_PATH)
        scheduler_thread = threading.Thread(target=scheduler.run, daemon=True)
        scheduler_thread.start()

        return jsonify({
            'success': True,
            'message': f'Scheduler started for location "{location}" with interval {interval_str}',
            'location': location,
            'interval': interval_str
        })

    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the running AQI scheduler."""
    global scheduler, scheduler_thread

    if not scheduler or not scheduler.running:
        return jsonify({
            'success': False,
            'error': 'Scheduler is not running'
        }), 400

    try:
        scheduler.running = False
        if scheduler_thread and scheduler_thread.is_alive():
            scheduler_thread.join(timeout=10)  # Wait up to 10 seconds

        return jsonify({
            'success': True,
            'message': 'Scheduler stopped successfully'
        })

    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """Get the current status of the AQI scheduler."""
    global scheduler

    if scheduler:
        try:
            status = scheduler.get_status()
            return jsonify({
                'success': True,
                'status': status
            })
        except Exception as e:
            logger.error(f"Failed to get scheduler status: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    else:
        return jsonify({
            'success': True,
            'status': {
                'running': False,
                'location': None,
                'interval_seconds': None,
                'readings_taken': 0,
                'start_time': None,
                'last_reading_time': None
            }
        })

# Admin Endpoints
@app.route('/api/admin/clear_data', methods=['POST'])
def clear_all_data():
    """Clear all data from the database (admin operation)."""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': 'JSON body required'
        }), 400

    confirm = data.get('confirm')
    if confirm != 'CLEAR_ALL_DATA':
        return jsonify({
            'success': False,
            'error': 'Confirmation required. Set confirm to "CLEAR_ALL_DATA"'
        }), 400

    try:
        with get_database() as db:
            conn = db._get_connection()
            cursor = conn.cursor()

            # Delete in order to respect foreign keys
            cursor.execute('DELETE FROM aqi_calculations')
            cursor.execute('DELETE FROM readings')
            cursor.execute('DELETE FROM locations')

            conn.commit()

            logger.warning("All database data cleared via admin API")

        return jsonify({
            'success': True,
            'message': 'All database data has been cleared'
        })

    except Exception as e:
        logger.error(f"Failed to clear database data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sensor/calculate_aqi', methods=['POST'])
def calculate_aqi():
    """Calculate AQI v2 from raw PM atmospheric data."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'JSON body required'
            }), 400

        pm25 = data.get('pm25')
        pm10 = data.get('pm10')

        if pm25 is None:
            return jsonify({
                'success': False,
                'error': 'pm25 value is required'
            }), 400

        # Validate values
        if not isinstance(pm25, (int, float)) or pm25 < 0:
            return jsonify({
                'success': False,
                'error': 'pm25 must be a non-negative number'
            }), 400

        if pm10 is not None and (not isinstance(pm10, (int, float)) or pm10 < 0):
            return jsonify({
                'success': False,
                'error': 'pm10 must be a non-negative number'
            }), 400

        from sensors.aqi_v2 import calculate_aqi_v2

        aqi_result = calculate_aqi_v2(float(pm25), float(pm10) if pm10 is not None else None)

        return jsonify({
            'success': True,
            'input': {
                'pm25_atmospheric': pm25,
                'pm10_atmospheric': pm10
            },
            'aqi': aqi_result
        })

    except Exception as e:
        logger.error(f"Failed to calculate AQI: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# SENSOR/AQI ENDPOINTS (/sensor/aqi/*)
# =============================================================================

# Sensor Endpoints (/sensor/aqi/sensor/*)
@app.route('/sensor/aqi/sensor/reading', methods=['GET'])
def get_sensor_reading():
    """Get direct sensor reading without database storage."""
    try:
        from sensors.pm25_sensor import PM25Sensor

        sensor = PM25Sensor()
        try:
            reading = sensor.get_complete_reading()
            sensor.disconnect()

            return jsonify({
                'success': True,
                'reading': reading,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            sensor.disconnect()
            raise e

    except Exception as e:
        logger.error(f"Failed to get sensor reading: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sensor/aqi/sensor/diagnostics', methods=['GET'])
def get_sensor_diagnostics():
    """Get comprehensive sensor diagnostics and performance data."""
    try:
        from sensors.pm25_sensor import PM25Sensor

        sensor = PM25Sensor()
        try:
            # Get various diagnostic information
            performance_stats = sensor.get_performance_statistics()
            sensor_status = sensor.get_sensor_status()

            diagnostics = {
                'sensor_status': 'healthy' if sensor.is_initialized() else 'unavailable',
                'performance_stats': performance_stats,
                'sensor_info': sensor_status,
                'power_status': {
                    'is_sleeping': sensor.is_sleeping(),
                    'is_warmed_up': sensor.is_warmed_up(),
                    'firmware_version': sensor.get_firmware_version()
                }
            }

            sensor.disconnect()

            return jsonify({
                'success': True,
                'diagnostics': diagnostics,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            sensor.disconnect()
            raise e

    except Exception as e:
        logger.error(f"Failed to get sensor diagnostics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sensor/aqi/sensor/calibration', methods=['GET'])
def get_sensor_calibration():
    """Check sensor calibration and data validity."""
    try:
        from sensors.pm25_sensor import PM25Sensor

        sensor = PM25Sensor()
        try:
            # Basic calibration check - validate recent readings
            reading = sensor.get_complete_reading()

            # Check if readings are within expected ranges
            pm25 = reading['concentrations']['atmospheric']['PM2.5']
            pm10 = reading['concentrations']['atmospheric']['PM10']

            calibration_status = {
                'status': 'valid',
                'last_check': datetime.now().isoformat(),
                'data_ranges': {
                    'pm2_5': {'value': pm25, 'range': '0-500', 'status': 'valid' if 0 <= pm25 <= 500 else 'out_of_range'},
                    'pm10': {'value': pm10, 'range': '0-1000', 'status': 'valid' if 0 <= pm10 <= 1000 else 'out_of_range'}
                },
                'validation_errors': []
            }

            # Check for validation errors
            if pm25 < 0 or pm25 > 500:
                calibration_status['validation_errors'].append(f'PM2.5 value {pm25} out of range')
            if pm10 < 0 or pm10 > 1000:
                calibration_status['validation_errors'].append(f'PM10 value {pm10} out of range')

            if calibration_status['validation_errors']:
                calibration_status['status'] = 'invalid'

            sensor.disconnect()

            return jsonify({
                'success': True,
                'calibration': calibration_status,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            sensor.disconnect()
            raise e

    except Exception as e:
        logger.error(f"Failed to check sensor calibration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sensor/aqi/sensor/power/status', methods=['GET'])
def get_sensor_power_status():
    """Get current sensor power status."""
    try:
        from sensors.pm25_sensor import PM25Sensor

        sensor = PM25Sensor()
        try:
            power_status = {
                'is_sleeping': sensor.is_sleeping(),
                'is_warmed_up': sensor.is_warmed_up(),
                'firmware_version': sensor.get_firmware_version(),
                'sensor_status': 'active' if sensor.is_initialized() else 'inactive'
            }

            sensor.disconnect()

            return jsonify({
                'success': True,
                'power_status': power_status,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            sensor.disconnect()
            raise e

    except Exception as e:
        logger.error(f"Failed to get sensor power status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sensor/aqi/sensor/power/sleep', methods=['POST'])
def sensor_enter_sleep():
    """Put sensor into sleep mode."""
    try:
        from sensors.pm25_sensor import PM25Sensor

        sensor = PM25Sensor()
        try:
            success = sensor.enter_sleep_mode()

            if success:
                return jsonify({
                    'success': True,
                    'message': 'Sensor entered sleep mode successfully',
                    'power_status': {
                        'is_sleeping': True,
                        'sleep_entered_at': datetime.now().isoformat()
                    },
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to enter sleep mode'
                }), 500
        except Exception as e:
            sensor.disconnect()
            raise e

    except Exception as e:
        logger.error(f"Failed to put sensor to sleep: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sensor/aqi/sensor/power/wake', methods=['POST'])
def sensor_wake_up():
    """Wake sensor from sleep mode."""
    try:
        from sensors.pm25_sensor import PM25Sensor

        sensor = PM25Sensor()
        try:
            success = sensor.wake_from_sleep()

            if success:
                return jsonify({
                    'success': True,
                    'message': 'Sensor woke from sleep mode successfully',
                    'power_status': {
                        'is_sleeping': False,
                        'wake_time': datetime.now().isoformat()
                    },
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to wake from sleep mode'
                }), 500
        except Exception as e:
            sensor.disconnect()
            raise e

    except Exception as e:
        logger.error(f"Failed to wake sensor: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sensor/aqi/sensor/power/cycle', methods=['POST'])
def sensor_power_cycle():
    """Perform sensor power cycle."""
    try:
        data = request.get_json() or {}
        sleep_duration = data.get('sleep_duration', 3.0)

        if not isinstance(sleep_duration, (int, float)) or sleep_duration < 1 or sleep_duration > 30:
            return jsonify({
                'success': False,
                'error': 'sleep_duration must be a number between 1 and 30 seconds'
            }), 400

        from sensors.pm25_sensor import PM25Sensor

        sensor = PM25Sensor()
        try:
            start_time = time.time()
            success = sensor.perform_power_cycle(sleep_duration=sleep_duration)
            end_time = time.time()

            if success:
                return jsonify({
                    'success': True,
                    'message': 'Power cycle completed successfully',
                    'cycle_info': {
                        'sleep_duration': sleep_duration,
                        'total_duration': round(end_time - start_time, 2),
                        'sensor_reinitialized': True
                    },
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Power cycle failed'
                }), 500
        except Exception as e:
            sensor.disconnect()
            raise e

    except Exception as e:
        logger.error(f"Failed to perform power cycle: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sensor/aqi/sensor/firmware', methods=['GET'])
def get_sensor_firmware():
    """Get sensor firmware information."""
    try:
        from sensors.pm25_sensor import PM25Sensor

        sensor = PM25Sensor()
        try:
            firmware_version = sensor.get_firmware_version()

            firmware_info = {
                'version': firmware_version,
                'model': 'PM25 Air Quality Sensor',
                'capabilities': [
                    'concentration_measurement',
                    'particle_counting',
                    'power_management',
                    'aqi_calculation'
                ],
                'communication': 'I2C'
            }

            sensor.disconnect()

            return jsonify({
                'success': True,
                'firmware': firmware_info,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            sensor.disconnect()
            raise e

    except Exception as e:
        logger.error(f"Failed to get sensor firmware info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# AQI Endpoints (/sensor/aqi/aqi/*)
@app.route('/sensor/aqi/aqi/calculate', methods=['POST'])
def calculate_aqi_endpoint():
    """Calculate AQI from provided PM data."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'JSON body required'
            }), 400

        pm25 = data.get('pm25')
        pm10 = data.get('pm10')
        include_pm10_comparison = data.get('include_pm10_comparison', False)

        if pm25 is None:
            return jsonify({
                'success': False,
                'error': 'pm25 value is required'
            }), 400

        # Validate values
        if not isinstance(pm25, (int, float)) or pm25 < 0:
            return jsonify({
                'success': False,
                'error': 'pm25 must be a non-negative number'
            }), 400

        if pm10 is not None and (not isinstance(pm10, (int, float)) or pm10 < 0):
            return jsonify({
                'success': False,
                'error': 'pm10 must be a non-negative number'
            }), 400

        from sensors.aqi_v2 import calculate_aqi_v2

        aqi_result = calculate_aqi_v2(float(pm25), float(pm10) if pm10 is not None else None)

        # Add calculation metadata
        aqi_result['calculation_method'] = 'aqi_v2'
        aqi_result['calculated_at'] = datetime.now().isoformat()
        aqi_result['input_values'] = {
            'pm25_atmospheric': pm25,
            'pm10_atmospheric': pm10
        }

        return jsonify({
            'success': True,
            'aqi': aqi_result,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to calculate AQI: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sensor/aqi/aqi/analysis/<location_name>', methods=['GET'])
def get_aqi_analysis(location_name):
    """Get AQI trend analysis for a location."""
    try:
        # Parse query parameters
        days = request.args.get('days', default=7, type=int)

        # Validate parameters
        if days < 1 or days > 30:
            return jsonify({
                'success': False,
                'error': 'days must be between 1 and 30'
            }), 400

        with get_database() as db:
            # Get location info
            location = db.get_location_by_name(location_name)
            if not location:
                return jsonify({
                    'success': False,
                    'error': f'Location "{location_name}" not found'
                }), 404

            # Get AQI statistics
            stats = db.get_aqi_statistics(location_id=location['id'], days=days)

            # Get recent readings for trend analysis
            readings = db.get_recent_readings(location_id=location['id'], limit=min(days * 24, 1000))

            # Analyze AQI levels distribution
            level_counts = {}
            aqi_values = []

            for reading in readings:
                if reading.get('aqi_value'):
                    aqi_val = reading['aqi_value']
                    aqi_values.append(aqi_val)

                    # Categorize AQI level
                    if aqi_val <= 50:
                        level = 'Good'
                    elif aqi_val <= 100:
                        level = 'Moderate'
                    elif aqi_val <= 150:
                        level = 'Unhealthy for Sensitive Groups'
                    elif aqi_val <= 200:
                        level = 'Unhealthy'
                    elif aqi_val <= 300:
                        level = 'Very Unhealthy'
                    else:
                        level = 'Hazardous'

                    level_counts[level] = level_counts.get(level, 0) + 1

            # Calculate trend insights
            if aqi_values:
                avg_aqi = sum(aqi_values) / len(aqi_values)
                max_aqi = max(aqi_values)
                min_aqi = min(aqi_values)

                # Determine air quality trend
                if avg_aqi <= 50:
                    trend = "good"
                    recommendations = ["Air quality is satisfactory for all activities"]
                elif avg_aqi <= 100:
                    trend = "moderate"
                    recommendations = ["Air quality is acceptable", "Unusually sensitive people should consider limiting prolonged outdoor exertion"]
                elif avg_aqi <= 150:
                    trend = "unhealthy_sensitive"
                    recommendations = ["Sensitive groups may experience health effects", "Consider reducing prolonged outdoor activities"]
                else:
                    trend = "unhealthy"
                    recommendations = ["Everyone may experience health effects", "Reduce outdoor activities"]
            else:
                trend = "no_data"
                recommendations = ["No AQI data available for analysis"]

            analysis = {
                'location': location,
                'time_period_days': days,
                'total_readings': len(readings),
                'aqi_statistics': stats,
                'level_distribution': level_counts,
                'trend': trend,
                'health_recommendations': recommendations,
                'data_points': len(aqi_values)
            }

            return jsonify({
                'success': True,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            })

    except Exception as e:
        logger.error(f"Failed to get AQI analysis for {location_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sensor/aqi/aqi/breakpoints', methods=['GET'])
def get_aqi_breakpoints():
    """Get AQI breakpoint information."""
    try:
        from sensors.aqi_v2 import PM25_BREAKPOINTS, PM10_BREAKPOINTS

        breakpoints_info = {
            'pm25_breakpoints': [
                {
                    'range': f"{bp[0]}-{bp[1]} μg/m³",
                    'aqi_range': f"{bp[2]}-{bp[3]}",
                    'level': bp[4],
                    'color': bp[5]
                }
                for bp in PM25_BREAKPOINTS
            ],
            'pm10_breakpoints': [
                {
                    'range': f"{bp[0]}-{bp[1]} μg/m³",
                    'aqi_range': f"{bp[2]}-{bp[3]}"
                }
                for bp in PM10_BREAKPOINTS
            ],
            'calculation_method': 'aqi_v2',
            'source': 'EPA AirNow AQI specification',
            'last_updated': 'Based on 2023 EPA guidelines'
        }

        return jsonify({
            'success': True,
            'breakpoints': breakpoints_info,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get AQI breakpoints: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Combined Endpoints (/sensor/aqi/combined/*)
@app.route('/sensor/aqi/combined/reading/<location_name>', methods=['GET'])
def get_combined_reading(location_name):
    """Get combined sensor reading and AQI data for a location."""
    try:
        from sensors.pm25_sensor import PM25Sensor

        # Get sensor reading
        sensor = PM25Sensor()
        try:
            sensor_reading = sensor.get_complete_reading()

            # Calculate AQI
            pm25 = sensor_reading['concentrations']['atmospheric']['PM2.5']
            pm10 = sensor_reading['concentrations']['atmospheric']['PM10']

            from sensors.aqi_v2 import calculate_aqi_v2
            aqi_result = calculate_aqi_v2(pm25, pm10)

            # Store in database if location exists
            with get_database() as db:
                location = db.get_location_by_name(location_name)
                if location:
                    # Store the reading
                    reading_id = db.store_reading(
                        location_id=location['id'],
                        pm1_0_atm=sensor_reading['concentrations']['atmospheric']['PM1.0'],
                        pm2_5_atm=pm25,
                        pm10_atm=pm10,
                        pm1_0_std=sensor_reading['concentrations']['standard']['PM1.0'],
                        pm2_5_std=sensor_reading['concentrations']['standard']['PM2.5'],
                        pm10_std=sensor_reading['concentrations']['standard']['PM10'],
                        particle_counts=sensor_reading['particle_counts'],
                        sensor_info=sensor_reading['sensor_info']
                    )

                    # Store AQI calculation
                    db.store_aqi_calculation(
                        reading_id=reading_id,
                        aqi_value=aqi_result['aqi_value'],
                        aqi_level=aqi_result['aqi_level'],
                        aqi_color=aqi_result['aqi_color'],
                        aqi_source=aqi_result['aqi_source'],
                        health_message=aqi_result['health_message'],
                        pm25_aqi=aqi_result['pm25_aqi'],
                        pm10_aqi=aqi_result['pm10_aqi']
                    )

            sensor.disconnect()

            combined_data = {
                'sensor_reading': sensor_reading,
                'aqi_calculation': aqi_result,
                'location': location_name,
                'stored_in_database': location is not None
            }

            return jsonify({
                'success': True,
                'data': combined_data,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            sensor.disconnect()
            raise e

    except Exception as e:
        logger.error(f"Failed to get combined reading for {location_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/sensor/aqi/combined/calculate', methods=['POST'])
def calculate_aqi_from_sensor():
    """Calculate AQI from current sensor data."""
    try:
        from sensors.pm25_sensor import PM25Sensor

        sensor = PM25Sensor()
        try:
            # Get current sensor reading
            reading = sensor.get_complete_reading()

            # Extract PM values
            pm25 = reading['concentrations']['atmospheric']['PM2.5']
            pm10 = reading['concentrations']['atmospheric']['PM10']

            # Calculate AQI
            from sensors.aqi_v2 import calculate_aqi_v2
            aqi_result = calculate_aqi_v2(pm25, pm10)

            sensor.disconnect()

            return jsonify({
                'success': True,
                'sensor_data': {
                    'pm25_atmospheric': pm25,
                    'pm10_atmospheric': pm10,
                    'timestamp': reading['timestamp']
                },
                'aqi': aqi_result,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            sensor.disconnect()
            raise e

    except Exception as e:
        logger.error(f"Failed to calculate AQI from sensor: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 errors."""
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # Disable debug for production
        threaded=True  # Enable threading for better performance
    )