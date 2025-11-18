"""
AQI App Module

A comprehensive air quality monitoring application that stores PM sensor readings
and AQI calculations in SQLite database with location tracking.

Features:
- SQLite database storage with normalized schema
- Location management for multiple monitoring sites
- Raw sensor data storage (atmospheric PM values)
- AQI v2 calculations with complete metadata
- Historical data querying and analytics
- Integration with PM25Sensor class

Database Schema:
- locations: Monitoring location information
- readings: Raw sensor readings with timestamps
- aqi_calculations: Calculated AQI values and metadata
"""

import sqlite3
import time
import logging
from typing import Optional, Dict, List, Any, Tuple, Union
from pathlib import Path
import json


class AQIDatabase:
    """
    SQLite database manager for AQI monitoring application.

    Handles all database operations including schema creation, data insertion,
    and querying for air quality monitoring data.
    """

    def __init__(self, db_path: Union[str, Path] = "aqi_monitoring.db"):
        """
        Initialize AQI database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self._connection: Optional[sqlite3.Connection] = None

        # Create database and tables if they don't exist
        self._initialize_database()

    def _initialize_database(self):
        """Create database and tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create locations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    latitude REAL,
                    longitude REAL,
                    city TEXT,
                    country TEXT,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create readings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    -- Atmospheric PM concentrations (raw sensor values)
                    pm1_0_atmospheric REAL NOT NULL,
                    pm2_5_atmospheric REAL NOT NULL,
                    pm10_atmospheric REAL NOT NULL,

                    -- Optional standard values for comparison
                    pm1_0_standard REAL,
                    pm2_5_standard REAL,
                    pm10_standard REAL,

                    -- Particle counts
                    particles_0_3um INTEGER,
                    particles_0_5um INTEGER,
                    particles_1_0um INTEGER,
                    particles_2_5um INTEGER,
                    particles_5_0um INTEGER,
                    particles_10um INTEGER,

                    -- Sensor metadata
                    sensor_firmware_version INTEGER,
                    sensor_status TEXT,
                    is_warmed_up BOOLEAN,

                    FOREIGN KEY (location_id) REFERENCES locations(id)
                )
            ''')

            # Create AQI calculations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS aqi_calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reading_id INTEGER NOT NULL UNIQUE,

                    -- AQI v2 (atmospheric) results
                    aqi_value INTEGER NOT NULL,
                    aqi_level TEXT NOT NULL,
                    aqi_color TEXT NOT NULL,
                    aqi_source TEXT NOT NULL,
                    health_message TEXT,

                    -- Individual AQI components
                    pm25_aqi INTEGER,
                    pm10_aqi INTEGER,

                    -- Calculation metadata
                    calculation_method TEXT DEFAULT 'aqi_v2',
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (reading_id) REFERENCES readings(id)
                )
            ''')

            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_readings_location_timestamp ON readings(location_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_aqi_calculations_reading ON aqi_calculations(reading_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_locations_active ON locations(is_active)')

            conn.commit()
            self.logger.info(f"AQI database initialized at {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    # Location Management Methods
    def add_location(self, name: str, latitude: Optional[float] = None,
                    longitude: Optional[float] = None, city: Optional[str] = None,
                    country: Optional[str] = None, description: Optional[str] = None) -> int:
        """
        Add a new monitoring location.

        Args:
            name: Location name (must be unique)
            latitude: GPS latitude
            longitude: GPS longitude
            city: City name
            country: Country name
            description: Optional description

        Returns:
            Location ID of newly created location

        Raises:
            sqlite3.IntegrityError: If location name already exists
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO locations (name, latitude, longitude, city, country, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, latitude, longitude, city, country, description))

            location_id = cursor.lastrowid
            conn.commit()
            self.logger.info(f"Added location: {name} (ID: {location_id})")
            return location_id

    def get_location(self, location_id: int) -> Optional[Dict[str, Any]]:
        """Get location information by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM locations WHERE id = ?', (location_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def get_location_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get location information by name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM locations WHERE name = ?', (name,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def list_locations(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all locations."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute('SELECT * FROM locations WHERE is_active = 1 ORDER BY name')
            else:
                cursor.execute('SELECT * FROM locations ORDER BY name')

            return [dict(row) for row in cursor.fetchall()]

    def update_location(self, location_id: int, **updates) -> bool:
        """Update location information."""
        allowed_fields = ['name', 'latitude', 'longitude', 'city', 'country', 'description', 'is_active']

        update_fields = []
        values = []
        for field in allowed_fields:
            if field in updates:
                update_fields.append(f"{field} = ?")
                values.append(updates[field])

        if not update_fields:
            return False

        values.append(location_id)
        query = f"UPDATE locations SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()

            if cursor.rowcount > 0:
                self.logger.info(f"Updated location ID: {location_id}")
                return True
            return False

    # Reading Storage Methods
    def store_reading(self, location_id: int, pm1_0_atm: float, pm2_5_atm: float, pm10_atm: float,
                     pm1_0_std: Optional[float] = None, pm2_5_std: Optional[float] = None,
                     pm10_std: Optional[float] = None, particle_counts: Optional[Dict[str, int]] = None,
                     sensor_info: Optional[Dict[str, Any]] = None) -> int:
        """
        Store a sensor reading in the database.

        Args:
            location_id: Location ID where reading was taken
            pm1_0_atm: PM1.0 atmospheric concentration (μg/m³)
            pm2_5_atm: PM2.5 atmospheric concentration (μg/m³)
            pm10_atm: PM10 atmospheric concentration (μg/m³)
            pm1_0_std: PM1.0 standard concentration (optional)
            pm2_5_std: PM2.5 standard concentration (optional)
            pm10_std: PM10 standard concentration (optional)
            particle_counts: Dictionary of particle counts by size
            sensor_info: Dictionary with sensor metadata

        Returns:
            Reading ID of stored reading
        """
        # Extract particle counts
        particles_0_3um = particle_counts.get('particles_0_3um') if particle_counts else None
        particles_0_5um = particle_counts.get('particles_0_5um') if particle_counts else None
        particles_1_0um = particle_counts.get('particles_1_0um') if particle_counts else None
        particles_2_5um = particle_counts.get('particles_2_5um') if particle_counts else None
        particles_5_0um = particle_counts.get('particles_5_0um') if particle_counts else None
        particles_10um = particle_counts.get('particles_10um') if particle_counts else None

        # Extract sensor info
        firmware_version = sensor_info.get('firmware_version') if sensor_info else None
        sensor_status = sensor_info.get('status') if sensor_info else None
        is_warmed_up = sensor_info.get('is_warmed_up') if sensor_info else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO readings (
                    location_id, pm1_0_atmospheric, pm2_5_atmospheric, pm10_atmospheric,
                    pm1_0_standard, pm2_5_standard, pm10_standard,
                    particles_0_3um, particles_0_5um, particles_1_0um, particles_2_5um,
                    particles_5_0um, particles_10um, sensor_firmware_version,
                    sensor_status, is_warmed_up
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                location_id, pm1_0_atm, pm2_5_atm, pm10_atm,
                pm1_0_std, pm2_5_std, pm10_std,
                particles_0_3um, particles_0_5um, particles_1_0um, particles_2_5um,
                particles_5_0um, particles_10um, firmware_version,
                sensor_status, is_warmed_up
            ))

            reading_id = cursor.lastrowid
            conn.commit()
            self.logger.info(f"Stored reading ID: {reading_id} for location {location_id}")
            return reading_id

    def store_aqi_calculation(self, reading_id: int, aqi_value: int, aqi_level: str,
                             aqi_color: str, aqi_source: str, health_message: Optional[str] = None,
                             pm25_aqi: Optional[int] = None, pm10_aqi: Optional[int] = None,
                             method: str = 'aqi_v2') -> int:
        """
        Store AQI calculation results.

        Args:
            reading_id: Reading ID this calculation is based on
            aqi_value: Final AQI value (0-500)
            aqi_level: AQI level description
            aqi_color: AQI color code
            aqi_source: Primary pollutant ('PM2.5' or 'PM10')
            health_message: Health advisory message
            pm25_aqi: AQI calculated from PM2.5 alone
            pm10_aqi: AQI calculated from PM10 alone
            method: Calculation method ('aqi_v1', 'aqi_v2')

        Returns:
            AQI calculation ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO aqi_calculations (
                    reading_id, aqi_value, aqi_level, aqi_color, aqi_source,
                    health_message, pm25_aqi, pm10_aqi, calculation_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                reading_id, aqi_value, aqi_level, aqi_color, aqi_source,
                health_message, pm25_aqi, pm10_aqi, method
            ))

            calc_id = cursor.lastrowid
            conn.commit()
            self.logger.info(f"Stored AQI calculation ID: {calc_id} for reading {reading_id}")
            return calc_id

    # Query Methods
    def get_recent_readings(self, location_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent readings with AQI data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT
                    r.*,
                    l.name as location_name,
                    l.city,
                    l.country,
                    a.aqi_value,
                    a.aqi_level,
                    a.aqi_color,
                    a.aqi_source,
                    a.health_message,
                    a.pm25_aqi,
                    a.pm10_aqi,
                    a.calculation_method
                FROM readings r
                JOIN locations l ON r.location_id = l.id
                LEFT JOIN aqi_calculations a ON r.id = a.reading_id
            '''

            params = []
            if location_id is not None:
                query += ' WHERE r.location_id = ?'
                params.append(location_id)

            query += ' ORDER BY r.timestamp DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_readings_by_date_range(self, start_date: str, end_date: str,
                                  location_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get readings within date range."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT
                    r.*,
                    l.name as location_name,
                    a.aqi_value,
                    a.aqi_level,
                    a.aqi_color
                FROM readings r
                JOIN locations l ON r.location_id = l.id
                LEFT JOIN aqi_calculations a ON r.id = a.reading_id
                WHERE r.timestamp BETWEEN ? AND ?
            '''

            params = [start_date, end_date]
            if location_id is not None:
                query += ' AND r.location_id = ?'
                params.append(location_id)

            query += ' ORDER BY r.timestamp'

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_aqi_statistics(self, location_id: Optional[int] = None, days: int = 7) -> Dict[str, Any]:
        """Get AQI statistics for recent period."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Calculate date threshold
            import datetime
            threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()

            query = '''
                SELECT
                    COUNT(*) as total_readings,
                    AVG(a.aqi_value) as avg_aqi,
                    MIN(a.aqi_value) as min_aqi,
                    MAX(a.aqi_value) as max_aqi,
                    AVG(r.pm2_5_atmospheric) as avg_pm25,
                    AVG(r.pm10_atmospheric) as avg_pm10
                FROM readings r
                LEFT JOIN aqi_calculations a ON r.id = a.reading_id
                WHERE r.timestamp >= ?
            '''

            params = [threshold_date]
            if location_id is not None:
                query += ' AND r.location_id = ?'
                params.append(location_id)

            cursor.execute(query, params)
            row = cursor.fetchone()

            if row:
                return dict(row)
            return {}

    def get_location_summary(self, location_id: int) -> Dict[str, Any]:
        """Get summary statistics for a location."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get location info
            cursor.execute('SELECT * FROM locations WHERE id = ?', (location_id,))
            location = dict(cursor.fetchone()) if cursor.fetchone() else None

            if not location:
                return {}

            # Get reading statistics
            cursor.execute('''
                SELECT
                    COUNT(*) as total_readings,
                    COUNT(CASE WHEN a.aqi_value IS NOT NULL THEN 1 END) as readings_with_aqi,
                    AVG(r.pm2_5_atmospheric) as avg_pm25,
                    MAX(r.timestamp) as last_reading
                FROM readings r
                LEFT JOIN aqi_calculations a ON r.id = a.reading_id
                WHERE r.location_id = ?
            ''', (location_id,))

            stats = dict(cursor.fetchone()) if cursor.fetchone() else {}

            return {
                'location': location,
                'statistics': stats
            }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class AQIApp:
    """
    Main AQI monitoring application class.

    Integrates PM25Sensor with AQIDatabase for complete air quality monitoring
    with location tracking and historical data storage.
    """

    def __init__(self, db_path: Union[str, Path] = "aqi_monitoring.db"):
        """
        Initialize AQI application.

        Args:
            db_path: Path to SQLite database file
        """
        self.db = AQIDatabase(db_path)
        self.logger = logging.getLogger(__name__)

    def add_monitoring_location(self, name: str, **location_data) -> int:
        """
        Add a new monitoring location.

        Args:
            name: Location name
            **location_data: Additional location data (latitude, longitude, etc.)

        Returns:
            Location ID
        """
        return self.db.add_location(name, **location_data)

    def take_reading(self, location_name: str) -> Optional[Dict[str, Any]]:
        """
        Take a complete reading at specified location.

        Args:
            location_name: Name of monitoring location

        Returns:
            Dictionary with reading results or None if failed
        """
        try:
            # Import sensor here to avoid circular imports
            from sensors.pm25_sensor import PM25Sensor

            # Get location
            location = self.db.get_location_by_name(location_name)
            if not location:
                self.logger.error(f"Location '{location_name}' not found")
                return None

            # Initialize sensor and take reading
            sensor = PM25Sensor()
            try:
                # Get complete reading
                complete_reading = sensor.get_complete_reading()

                # Extract data for storage
                concentrations = complete_reading.get('concentrations', {})
                particle_counts = complete_reading.get('particle_counts', {})
                sensor_info = complete_reading.get('sensor_info', {})

                # Store reading
                reading_id = self.db.store_reading(
                    location_id=location['id'],
                    pm1_0_atm=concentrations.get('atmospheric', {}).get('PM1.0', 0),
                    pm2_5_atm=concentrations.get('atmospheric', {}).get('PM2.5', 0),
                    pm10_atm=concentrations.get('atmospheric', {}).get('PM10', 0),
                    pm1_0_std=concentrations.get('standard', {}).get('PM1.0'),
                    pm2_5_std=concentrations.get('standard', {}).get('PM2.5'),
                    pm10_std=concentrations.get('standard', {}).get('PM10'),
                    particle_counts=particle_counts,
                    sensor_info=sensor_info
                )

                # Calculate and store AQI
                aqi_result = sensor.get_aqi_v2(include_pm10_comparison=True)
                self.db.store_aqi_calculation(
                    reading_id=reading_id,
                    aqi_value=aqi_result['aqi_value'],
                    aqi_level=aqi_result['aqi_level'],
                    aqi_color=aqi_result['aqi_color'],
                    aqi_source=aqi_result['aqi_source'],
                    health_message=aqi_result['health_message'],
                    pm25_aqi=aqi_result['pm25_aqi'],
                    pm10_aqi=aqi_result['pm10_aqi']
                )

                self.logger.info(f"Successfully stored reading at {location_name}")
                return {
                    'reading_id': reading_id,
                    'location': location,
                    'reading': complete_reading,
                    'aqi': aqi_result
                }

            finally:
                sensor.disconnect()

        except Exception as e:
            self.logger.error(f"Failed to take reading at {location_name}: {e}")
            return None

    def get_location_readings(self, location_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent readings for a location."""
        location = self.db.get_location_by_name(location_name)
        if not location:
            return []

        return self.db.get_recent_readings(location_id=location['id'], limit=limit)

    def get_all_locations(self) -> List[Dict[str, Any]]:
        """Get all monitoring locations."""
        return self.db.list_locations()

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard summary data."""
        locations = self.db.list_locations()

        dashboard = {
            'total_locations': len(locations),
            'locations': []
        }

        for location in locations:
            summary = self.db.get_location_summary(location['id'])
            recent_readings = self.db.get_recent_readings(location_id=location['id'], limit=1)

            location_data = {
                'location': location,
                'summary': summary.get('statistics', {}) if summary else {},
                'latest_reading': recent_readings[0] if recent_readings else None
            }

            dashboard['locations'].append(location_data)

        return dashboard

    def export_data(self, location_name: Optional[str] = None, format_type: str = 'json') -> str:
        """Export data for specified location or all locations."""
        if location_name:
            location = self.db.get_location_by_name(location_name)
            if not location:
                return ""
            readings = self.db.get_recent_readings(location_id=location['id'], limit=1000)
        else:
            readings = self.db.get_recent_readings(limit=1000)

        if format_type == 'json':
            return json.dumps(readings, indent=2, default=str)
        else:
            # CSV format
            if not readings:
                return ""

            headers = readings[0].keys()
            csv_lines = [','.join(headers)]

            for reading in readings:
                row = [str(reading.get(h, '')) for h in headers]
                csv_lines.append(','.join(row))

            return '\n'.join(csv_lines)

    def close(self):
        """Close database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions
def create_aqi_app(db_path: Union[str, Path] = "aqi_monitoring.db") -> AQIApp:
    """Create and return AQIApp instance."""
    return AQIApp(db_path)


def quick_reading(location_name: str, db_path: Union[str, Path] = "aqi_monitoring.db") -> Optional[Dict[str, Any]]:
    """Take a quick reading at specified location."""
    with AQIApp(db_path) as app:
        return app.take_reading(location_name)