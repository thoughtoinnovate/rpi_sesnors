"""
PM25 Sensor API

A comprehensive, independent Python library for PM25 air quality sensor communication
via I2C interface. This library provides robust sensor access with advanced
error handling, configuration management, and data analysis capabilities.

Features:
- PM concentration reading (PM1.0, PM2.5, PM10 in standard and atmospheric units)
- Particle counting (0.3μm to 10μm sizes)
- Power management (sleep/wake functionality)
- Air quality index calculation
- Data validation and calibration
- Comprehensive error handling
- Performance optimization with caching
- Configuration management
- Data logging and export

Basic Usage:
    from apis import PM25Sensor
    
    # Simple usage with default configuration
    sensor = PM25Sensor()
    pm25 = sensor.get_pm2_5_standard()
    print(f"PM2.5: {pm25} μg/m³")
    
    # Get complete reading with analysis
    reading = sensor.get_complete_reading()
    print(f"AQI: {reading['air_quality_index']['aqi_level']}")
    
    # Use as context manager
    with PM25Sensor() as sensor:
        data = sensor.get_air_quality_summary()
        print(data)

Advanced Usage:
    from apis import PM25Sensor, PM25Config
    
    # Custom configuration
    config = PM25Config({
        "i2c": {"address": 0x19, "bus": 1},
        "sensor": {"warmup_time": 10},
        "logging": {"level": "DEBUG"}
    })
    
    sensor = PM25Sensor(config=config)
    sensor.initialize()
    
    # Continuous monitoring
    while True:
        reading = sensor.get_complete_reading()
        # Process reading...
        sensor.enter_sleep_mode()
        time.sleep(60)  # Sleep for 1 minute
        sensor.wake_from_sleep()

Configuration:
    The library supports configuration via:
    - Dictionary passed to PM25Config
    - JSON configuration file
    - Environment variables (PM25_CONFIG_FILE)
    - Default configuration files in standard locations

Error Handling:
    All sensor operations raise specific exceptions:
    - CommunicationError: I2C communication failures
    - CalibrationError: Invalid sensor readings
    - PowerManagementError: Power control failures
    - ConfigurationError: Invalid configuration
    - SensorNotInitializedError: Sensor not ready

Performance:
    - Built-in caching for repeated readings
    - Retry logic for communication reliability
    - Performance statistics tracking
    - Configurable timeouts and intervals

For detailed documentation and examples, see the examples/ directory.
"""

__version__ = "1.0.0"
__author__ = "PM25 API Development Team"
__license__ = "MIT"
__description__ = "Independent PM25 sensor API with advanced features"

# Core classes and functions
from .pm25_sensor import PM25Sensor, create_sensor
from .config import PM25Config, load_config, setup_logging
from .exceptions import (
    PM25SensorError, CommunicationError, SensorNotRespondingError,
    InvalidRegisterError, InvalidDataError, SensorNotInitializedError,
    ConfigurationError, PowerManagementError, SensorBusyError,
    CalibrationError, TimeoutError
)

# Functional modules for advanced usage
from .concentration import ConcentrationReader
from .particle_count import ParticleCounter
from .power_management import PowerManager
from .i2c_interface import I2CInterface

# Constants and utilities
from .constants import *
from .utils import (
    calculate_air_quality_index, analyze_particle_distribution,
    format_sensor_data, save_readings_to_file
)
from .aqi_v2 import (
    calculate_aqi_v2, PM25_BREAKPOINTS, PM10_BREAKPOINTS,
    get_aqi_breakpoint_info, test_aqi_v2_calculations
)
from .location import (
    LocationDetector, LocationDetectionError, detect_location, set_location, get_location_with_air_quality
)

# Public API
__all__ = [
    # Version and metadata
    "__version__", "__author__", "__license__", "__description__",
    
    # Main API
    "PM25Sensor", "create_sensor",
    
    # Configuration
    "PM25Config", "load_config", "setup_logging",
    
    # Exceptions
    "PM25SensorError", "CommunicationError", "SensorNotRespondingError",
    "InvalidRegisterError", "InvalidDataError", "SensorNotInitializedError",
    "ConfigurationError", "PowerManagementError", "SensorBusyError",
    "CalibrationError", "TimeoutError",
    
    # Advanced components
    "ConcentrationReader", "ParticleCounter", "PowerManager", "I2CInterface",
    
    # Utilities
    "calculate_air_quality_index", "analyze_particle_distribution",
    "format_sensor_data", "save_readings_to_file",
    
    # AQI v2 (Atmospheric Values Only)
    "calculate_aqi_v2", "PM25_BREAKPOINTS", "PM10_BREAKPOINTS",
    "get_aqi_breakpoint_info", "test_aqi_v2_calculations",
    
    # Location Detection
    "LocationDetector", "LocationDetectionError", "detect_location", "set_location", "get_location_with_air_quality",
    
    # Constants (all from constants module)
    "PARTICLE_PM1_0_STANDARD", "PARTICLE_PM2_5_STANDARD", "PARTICLE_PM10_STANDARD",
    "PARTICLE_PM1_0_ATMOSPHERE", "PARTICLE_PM2_5_ATMOSPHERE", "PARTICLE_PM10_ATMOSPHERE",
    "PARTICLENUM_0_3_UM_EVERY0_1L_AIR", "PARTICLENUM_0_5_UM_EVERY0_1L_AIR",
    "PARTICLENUM_1_0_UM_EVERY0_1L_AIR", "PARTICLENUM_2_5_UM_EVERY0_1L_AIR",
    "PARTICLENUM_5_0_UM_EVERY0_1L_AIR", "PARTICLENUM_10_UM_EVERY0_1L_AIR",
    "PARTICLENUM_GAIN_VERSION", "DEFAULT_I2C_BUS", "DEFAULT_I2C_ADDRESS"
]

# Convenience imports for quick access
def quick_sensor(address: int = 0x19, bus: int = 1) -> PM25Sensor:
    """
    Quick sensor creation with minimal parameters.
    
    Args:
        address: I2C address of sensor
        bus: I2C bus number
        
    Returns:
        Initialized PM25Sensor instance
    """
    config = PM25Config({
        "i2c": {"address": address, "bus": bus}
    })
    return PM25Sensor(config=config, auto_connect=True, auto_warmup=True)


def get_version() -> str:
    """Get library version."""
    return __version__


def get_info() -> dict:
    """Get library information."""
    return {
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "description": __description__
    }
