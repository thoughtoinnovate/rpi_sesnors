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

All endpoints return JSON responses optimized for low-bandwidth connections.
"""

import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request, abort
try:
    from flask_cors import CORS
except ImportError:
    # Fallback if CORS is not available
    CORS = None
import sqlite3
from datetime import datetime, timedelta
import logging

# Add parent directories to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))

from aqi.aqi_app import AQIDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
if CORS:
    CORS(app)  # Enable CORS for web applications

# Database configuration
DEFAULT_DB_PATH = os.getenv('AQI_DB_PATH', str(current_dir.parent / 'aqi_demo.db'))

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