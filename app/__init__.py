"""
AQI Monitoring Application Package

This package provides a comprehensive air quality monitoring solution
with SQLite database storage, location tracking, and automated scheduling.

Modules:
- aqi_app: Main AQI monitoring application
- aqi_app_example: Usage examples and demonstrations
- scheduler: Automated monitoring scheduler
- run_scheduler: Command-line scheduler interface

Features:
- Real-time PM2.5/PM10 monitoring
- AQI v2 calculations (professional standard)
- Multi-location support with GPS coordinates
- SQLite database with normalized schema
- Automated scheduling with flexible intervals
- Data export (JSON/CSV)
- Historical data analysis
"""

from .aqi_app import AQIApp, AQIDatabase, quick_reading, create_aqi_app
from .scheduler import AQIScheduler, TimeParser, create_scheduler

__version__ = "1.1.0"
__author__ = "PM25 Sensor Project"
__description__ = "Air Quality Monitoring Application with SQLite Database and Scheduling"

__all__ = [
    "AQIApp",
    "AQIDatabase",
    "AQIScheduler",
    "TimeParser",
    "quick_reading",
    "create_aqi_app",
    "create_scheduler"
]