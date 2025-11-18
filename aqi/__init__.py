"""
AQI Package

This package contains AQI (Air Quality Index) calculations, database management,
and scheduling functionality for air quality monitoring.

Modules:
- aqi_app: Main AQI application with database storage
- scheduler: Automated monitoring scheduler

Features:
- AQI v2 calculations (professional standard)
- SQLite database with normalized schema
- Automated scheduling with flexible intervals
- Multi-location support
- Historical data analysis
"""

from .aqi_app import AQIApp, AQIDatabase, quick_reading, create_aqi_app
from .scheduler import AQIScheduler, TimeParser, create_scheduler

__version__ = "1.1.0"
__author__ = "PM25 Sensor Project"

__all__ = [
    "AQIApp",
    "AQIDatabase",
    "AQIScheduler",
    "TimeParser",
    "quick_reading",
    "create_aqi_app",
    "create_scheduler"
]