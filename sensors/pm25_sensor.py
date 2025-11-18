"""
PM25 Sensor Main Class

This module provides the main PM25Sensor class that unifies all sensor functionality
into a clean, easy-to-use interface.
"""

import time
import logging
from typing import Optional, Dict, Any, Union, List, Tuple
from pathlib import Path

from .config import PM25Config, load_config, setup_logging
from .i2c_interface import I2CInterface
from .concentration import ConcentrationReader
from .particle_count import ParticleCounter
from .power_management import PowerManager
from .utils import (
    calculate_air_quality_index, analyze_particle_distribution,
    format_sensor_data, save_readings_to_file, create_reading_summary
)
from .exceptions import (
    PM25SensorError, SensorNotInitializedError, SensorNotRespondingError,
    ConfigurationError, handle_sensor_exception
)


class PM25Sensor:
    """
    Main PM25 sensor class providing unified access to all sensor functionality.
    
    This class combines concentration reading, particle counting, power management,
    and data analysis capabilities into a single, easy-to-use interface.
    """
    
    def __init__(self, config: Optional[PM25Config] = None, 
                 auto_connect: bool = True, auto_warmup: bool = True):
        """
        Initialize PM25 sensor with configuration.
        
        Args:
            config: PM25Config instance. If None, loads default configuration.
            auto_connect: Whether to automatically connect to sensor
            auto_warmup: Whether to automatically warm up sensor after connection
        """
        # Load configuration
        self.config = config or load_config()
        
        # Setup logging
        self.logger = setup_logging(self.config)
        self.logger.info("Initializing PM25 Sensor")
        
        # Initialize components
        self.i2c = I2CInterface(self.config)
        self.concentration_reader = ConcentrationReader(self.i2c, self.config)
        self.particle_counter = ParticleCounter(self.i2c, self.config)
        self.power_manager = PowerManager(self.i2c, self.config)
        
        # Connection state
        self._is_initialized = False
        self._is_connected = False
        self._was_initialized = False  # Track if it was ever initialized
        self._initialization_time: Optional[float] = None
        
        # Data collection settings
        self._auto_warmup = auto_warmup
        self._reading_history: List[Dict[str, Any]] = []
        self._max_history_size = self.config.get("sensor.max_history_size", 1000)
        
        # Performance tracking
        self._total_readings = 0
        self._total_errors = 0
        self._last_reading_time: Optional[float] = None
        
        # Auto-connect if requested
        if auto_connect:
            self.initialize()
    
    def initialize(self) -> bool:
        """
        Initialize sensor connection and perform warmup.
        
        Returns:
            True if initialization successful
            
        Raises:
            SensorNotRespondingError: If sensor doesn't respond
            ConfigurationError: If configuration is invalid
        """
        try:
            self.logger.info("Initializing PM25 sensor connection")
            
            # Connect to sensor
            if not self.i2c.connect():
                raise SensorNotRespondingError(self.i2c.device_address, self.i2c.timeout)
            
            self._is_connected = True
            self.logger.info("Successfully connected to PM25 sensor")
            
            # Get firmware version
            try:
                version = self.power_manager.get_firmware_version()
                self.logger.info(f"PM25 Sensor firmware version: {version}")
            except Exception as e:
                self.logger.warning(f"Failed to read firmware version: {e}")
            
            # Auto warmup if enabled
            if self._auto_warmup:
                self.logger.info("Performing sensor warmup")
                time.sleep(self.config.get("sensor.warmup_time", 5))
                self.logger.info("Sensor warmup completed")
            
            self._is_initialized = True
            self._was_initialized = True
            self._initialization_time = time.time()
            
            self.logger.info("PM25 sensor initialization complete")
            return True
            
        except Exception as e:
            self._total_errors += 1
            self.logger.error(f"Sensor initialization failed: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from sensor and clean up resources."""
        try:
            self.logger.info("Disconnecting from PM25 sensor")
            
            # Clear caches
            self.concentration_reader.clear_cache()
            self.particle_counter.clear_cache()
            
            # Disconnect I2C
            self.i2c.disconnect()
            
            # Reset state
            self._is_connected = False
            self._is_initialized = False
            # Keep _was_initialized = True to track that it was previously initialized
            
            self.logger.info("PM25 sensor disconnected")
            
        except Exception as e:
            self.logger.warning(f"Error during disconnect: {e}")
    
    def is_initialized(self) -> bool:
        """Check if sensor is initialized and ready."""
        return self._is_initialized and self.i2c.is_connected()
    
    def is_connected(self) -> bool:
        """Check if sensor is connected."""
        return self._is_connected and self.i2c.is_connected()
    
    def _ensure_initialized(self, attempt_reconnect: bool = True):
        """Ensure sensor is initialized, raise error if not."""
        if not self.is_initialized():
            if attempt_reconnect and self._was_initialized:
                # Try to reconnect if we were previously initialized
                try:
                    self.logger.info("Attempting automatic reconnection")
                    if self.initialize():
                        return
                except Exception as e:
                    self.logger.warning(f"Auto-reconnection failed: {e}")
                    # If reconnection fails, raise CommunicationError instead
                    from .exceptions import CommunicationError
                    raise CommunicationError("Sensor disconnected and reconnection failed")
            
            # If we were never initialized or reconnection is not attempted
            if self._was_initialized:
                # We were initialized but now disconnected
                from .exceptions import CommunicationError
                raise CommunicationError("Sensor disconnected")
            else:
                # We were never initialized
                raise SensorNotInitializedError
    
    # PM Concentration Methods
    @handle_sensor_exception
    def get_pm1_0_standard(self, use_cache: bool = False) -> int:
        """Get PM1.0 concentration in standard units (μg/m³)."""
        return self._track_reading("pm1_0_standard", 
                                self.concentration_reader.get_pm1_0_standard(use_cache))
    
    @handle_sensor_exception
    def get_pm2_5_standard(self, use_cache: bool = False) -> int:
        """Get PM2.5 concentration in standard units (μg/m³)."""
        self._ensure_initialized()
        return self._track_reading("pm2_5_standard",
                                self.concentration_reader.get_pm2_5_standard(use_cache))
    
    @handle_sensor_exception
    def get_pm10_standard(self, use_cache: bool = False) -> int:
        """Get PM10 concentration in standard units (μg/m³)."""
        return self._track_reading("pm10_standard",
                                self.concentration_reader.get_pm10_standard(use_cache))
    
    @handle_sensor_exception
    def get_pm1_0_atmospheric(self, use_cache: bool = False) -> int:
        """Get PM1.0 concentration in atmospheric units (μg/m³)."""
        return self._track_reading("pm1_0_atmospheric",
                                self.concentration_reader.get_pm1_0_atmospheric(use_cache))
    
    @handle_sensor_exception
    def get_pm2_5_atmospheric(self, use_cache: bool = False) -> int:
        """Get PM2.5 concentration in atmospheric units (μg/m³)."""
        return self._track_reading("pm2_5_atmospheric",
                                self.concentration_reader.get_pm2_5_atmospheric(use_cache))
    
    @handle_sensor_exception
    def get_pm10_atmospheric(self, use_cache: bool = False) -> int:
        """Get PM10 concentration in atmospheric units (μg/m³)."""
        return self._track_reading("pm10_atmospheric",
                                self.concentration_reader.get_pm10_atmospheric(use_cache))
    
    def get_all_concentrations(self, use_cache: bool = False) -> Dict[str, Dict[str, int]]:
        """Get all PM concentrations (standard and atmospheric)."""
        return self.concentration_reader.get_all_concentrations(use_cache)
    
    # Particle Count Methods
    @handle_sensor_exception
    def get_particles_0_3um(self, use_cache: bool = False) -> int:
        """Get 0.3μm particle count per 0.1L."""
        return self._track_reading("particles_0_3um",
                                self.particle_counter.get_particles_0_3um(use_cache))
    
    @handle_sensor_exception
    def get_particles_0_5um(self, use_cache: bool = False) -> int:
        """Get 0.5μm particle count per 0.1L."""
        return self._track_reading("particles_0_5um",
                                self.particle_counter.get_particles_0_5um(use_cache))
    
    @handle_sensor_exception
    def get_particles_1_0um(self, use_cache: bool = False) -> int:
        """Get 1.0μm particle count per 0.1L."""
        return self._track_reading("particles_1_0um",
                                self.particle_counter.get_particles_1_0um(use_cache))
    
    @handle_sensor_exception
    def get_particles_2_5um(self, use_cache: bool = False) -> int:
        """Get 2.5μm particle count per 0.1L."""
        return self._track_reading("particles_2_5um",
                                self.particle_counter.get_particles_2_5um(use_cache))
    
    @handle_sensor_exception
    def get_particles_5_0um(self, use_cache: bool = False) -> int:
        """Get 5.0μm particle count per 0.1L."""
        return self._track_reading("particles_5_0um",
                                self.particle_counter.get_particles_5_0um(use_cache))
    
    @handle_sensor_exception
    def get_particles_10um(self, use_cache: bool = False) -> int:
        """Get 10μm particle count per 0.1L."""
        return self._track_reading("particles_10um",
                                self.particle_counter.get_particles_10um(use_cache))
    
    def get_all_particle_counts(self, use_cache: bool = False) -> Dict[str, int]:
        """Get all particle counts."""
        return self.particle_counter.get_all_particle_counts(use_cache)
    
    # Power Management Methods
    @handle_sensor_exception
    def enter_sleep_mode(self) -> bool:
        """Put sensor into low-power sleep mode."""
        result = self.power_manager.enter_sleep_mode()
        if result:
            self.logger.info("Sensor entered sleep mode")
        return result
    
    @handle_sensor_exception
    def wake_from_sleep(self) -> bool:
        """Wake sensor from sleep mode."""
        result = self.power_manager.wake_from_sleep()
        if result:
            self.logger.info("Sensor woke from sleep mode")
        return result
    
    def is_sleeping(self) -> bool:
        """Check if sensor is in sleep mode."""
        return self.power_manager.is_sleeping()
    
    def is_warmed_up(self) -> bool:
        """Check if sensor has completed warmup."""
        return self.power_manager.is_warmed_up()
    
    @handle_sensor_exception
    def get_firmware_version(self) -> int:
        """Get sensor firmware version."""
        return self.power_manager.get_firmware_version()
    
    def perform_power_cycle(self, sleep_duration: float = 1.0) -> bool:
        """Perform complete power cycle."""
        self.logger.info(f"Performing power cycle (sleep: {sleep_duration}s)")
        return self.power_manager.perform_power_cycle(sleep_duration)
    
    # Comprehensive Reading Methods
    def get_complete_reading(self, use_cache: bool = False) -> Dict[str, Any]:
        """
        Get complete sensor reading including all data types.
        
        Args:
            use_cache: Whether to use cached values
            
        Returns:
            Dictionary with complete sensor data
        """
        if not self.is_initialized():
            raise SensorNotInitializedError()
        
        try:
            reading_time = time.time()
            
            # Get all concentrations
            concentrations = self.get_all_concentrations(use_cache)
            
            # Get all particle counts
            particle_counts = self.get_all_particle_counts(use_cache)
            
            # Get sensor status
            sensor_info = self.power_manager.get_sensor_info()
            
            # Calculate derived metrics
            pm25_standard = concentrations["standard"].get("PM2.5", 0)
            aqi_info = calculate_air_quality_index(float(pm25_standard))
            particle_analysis = analyze_particle_distribution(particle_counts)
            
            # Combine all data
            complete_reading = {
                "timestamp": reading_time,
                "concentrations": concentrations,
                "particle_counts": particle_counts,
                "air_quality_index": aqi_info,
                "particle_analysis": particle_analysis,
                "sensor_info": sensor_info,
                "reading_id": len(self._reading_history) + 1
            }
            
            # Add to history
            self._add_to_history(complete_reading)
            
            return complete_reading
            
        except Exception as e:
            self._total_errors += 1
            self.logger.error(f"Failed to get complete reading: {e}")
            raise
    
    def get_air_quality_summary(self, use_cache: bool = False) -> Dict[str, Any]:
        """
        Get air quality summary with key metrics.
        
        Args:
            use_cache: Whether to use cached values
            
        Returns:
            Dictionary with air quality summary
        """
        complete_reading = self.get_complete_reading(use_cache)
        
        return {
            "timestamp": complete_reading["timestamp"],
            "pm25_standard": complete_reading["concentrations"]["standard"]["PM2.5"],
            "pm10_standard": complete_reading["concentrations"]["standard"]["PM10"],
            "aqi_level": complete_reading["air_quality_index"]["aqi_level"],
            "aqi_value": complete_reading["air_quality_index"]["aqi_value"],
            "health_message": complete_reading["air_quality_index"]["health_message"],
            "dominant_particle_size": complete_reading["particle_analysis"]["dominant_size"],
            "total_particles": complete_reading["particle_analysis"]["total_particles"],
            "sensor_status": "awake" if not self.is_sleeping() else "sleeping",
            "is_warmed_up": self.is_warmed_up()
        }
    
    # AQI v2 Methods (Atmospheric Values Only)
    @handle_sensor_exception
    def get_aqi_v2(self, use_cache: bool = False, include_pm10_comparison: bool = False) -> Dict[str, Any]:
        """
        Get AQI v2 calculated from atmospheric (ATM) values only.
        
        This method implements the exact algorithm using atmospheric values:
        1. Uses PM2.5 Atmospheric (pm.pm25_atm) as primary value
        2. Applies exact table-based breakpoints from specification
        3. Optional PM10 comparison if it gives higher AQI
        4. Ignores PM1.0 completely (not used in official AQI calculations)
        
        Args:
            use_cache: Whether to use cached atmospheric values
            include_pm10_comparison: Whether to include PM10 comparison (optional)
            
        Returns:
            Dictionary with AQI v2 information following the exact algorithm
        """
        from .aqi_v2 import calculate_aqi_v2
        
        pm25_atm = self.get_pm2_5_atmospheric(use_cache)
        pm10_atm = self.get_pm10_atmospheric(use_cache) if include_pm10_comparison else None
        
        return calculate_aqi_v2(float(pm25_atm), float(pm10_atm) if pm10_atm else None)
    
    @handle_sensor_exception
    def get_air_quality_summary_v2(self, use_cache: bool = False, include_pm10_comparison: bool = False) -> Dict[str, Any]:
        """
        Get air quality summary using AQI v2 (atmospheric values only).
        
        Args:
            use_cache: Whether to use cached values
            include_pm10_comparison: Whether to include PM10 comparison
            
        Returns:
            Dictionary with air quality summary using AQI v2
        """
        aqi_info = self.get_aqi_v2(use_cache, include_pm10_comparison)
        
        return {
            "timestamp": aqi_info["timestamp"],
            "pm25_atmospheric": aqi_info["pm25_atmospheric"],
            "pm10_atmospheric": aqi_info["pm10_atmospheric"],
            "aqi_level": aqi_info["aqi_level"],
            "aqi_value": aqi_info["aqi_value"],
            "aqi_color": aqi_info["aqi_color"],
            "aqi_source": aqi_info["aqi_source"],
            "health_message": aqi_info["health_message"],
            "method": "aqi_v2",
            "sensor_status": "awake" if not self.is_sleeping() else "sleeping",
            "is_warmed_up": self.is_warmed_up()
        }
    
    def compare_aqi_methods(self, use_cache: bool = False) -> Dict[str, Any]:
        """
        Compare AQI v1 (standard) vs v2 (atmospheric) methods.
        
        Args:
            use_cache: Whether to use cached values
            
        Returns:
            Dictionary comparing both AQI calculation methods
        """
        # Get v1 (standard) results
        v1_summary = self.get_air_quality_summary(use_cache)
        
        # Get v2 (atmospheric) results
        v2_summary = self.get_air_quality_summary_v2(use_cache, include_pm10_comparison=True)
        
        return {
            "timestamp": v1_summary["timestamp"],
            "v1_standard": {
                "pm25": v1_summary["pm25_standard"],
                "pm10": v1_summary["pm10_standard"],
                "aqi_value": v1_summary["aqi_value"],
                "aqi_level": v1_summary["aqi_level"],
                "method": "EPA standard"
            },
            "v2_atmospheric": {
                "pm25": v2_summary["pm25_atmospheric"],
                "pm10": v2_summary["pm10_atmospheric"],
                "aqi_value": v2_summary["aqi_value"],
                "aqi_level": v2_summary["aqi_level"],
                "aqi_color": v2_summary["aqi_color"],
                "aqi_source": v2_summary["aqi_source"],
                "method": "Atmospheric (matches AirNow/PurpleAir)"
            },
            "differences": {
                "pm25_diff": v2_summary["pm25_atmospheric"] - v1_summary["pm25_standard"],
                "pm10_diff": (v2_summary["pm10_atmospheric"] or 0) - v1_summary["pm10_standard"],
                "aqi_diff": v2_summary["aqi_value"] - v1_summary["aqi_value"],
                "level_changed": v1_summary["aqi_level"] != v2_summary["aqi_level"]
            }
        }
    
    # Data Management Methods
    def get_reading_history(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get reading history.
        
        Args:
            count: Maximum number of readings to return (None for all)
            
        Returns:
            List of historical readings
        """
        if count is None:
            return self._reading_history.copy()
        else:
            return self._reading_history[-count:]
    
    def clear_reading_history(self):
        """Clear reading history."""
        self._reading_history.clear()
    
    # Location Detection Methods
    def get_location(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get current location using IP-based geolocation.
        
        Args:
            force_refresh: Whether to force location detection
            
        Returns:
            Dictionary with location information
        """
        from .location import LocationDetector
        
        if not hasattr(self, '_location_detector'):
            self._location_detector = LocationDetector()
        
        return self._location_detector.get_location(force_refresh)
    
    def set_manual_location(self, latitude: float, longitude: float, 
                         city: Optional[str] = None, country: Optional[str] = None) -> Dict[str, Any]:
        """
        Set location manually.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            city: Optional city name
            country: Optional country name
            
        Returns:
            Dictionary with location information
        """
        from .location import LocationDetector
        
        if not hasattr(self, '_location_detector'):
            self._location_detector = LocationDetector()
        
        return self._location_detector.set_manual_location(latitude, longitude, city, country)
    
    def get_air_quality_with_location(self, include_location: bool = True, 
                                   force_refresh_location: bool = False) -> Dict[str, Any]:
        """
        Get air quality data with location information.
        
        Args:
            include_location: Whether to include location data
            force_refresh_location: Whether to force location detection
            
        Returns:
            Dictionary with air quality and location data
        """
        # Get air quality data
        aqi_v2 = self.get_aqi_v2(include_pm10_comparison=True)
        
        result = {
            "air_quality": {
                "pm25_atmospheric": aqi_v2["pm25_atmospheric"],
                "pm10_atmospheric": aqi_v2["pm10_atmospheric"],
                "aqi_value": aqi_v2["aqi_value"],
                "aqi_level": aqi_v2["aqi_level"],
                "aqi_color": aqi_v2["aqi_color"],
                "aqi_source": aqi_v2["aqi_source"],
                "health_message": aqi_v2["health_message"],
                "timestamp": aqi_v2["timestamp"]
            },
            "sensor_info": {
                "status": "awake" if not self.is_sleeping() else "sleeping",
                "warmed_up": self.is_warmed_up(),
                "firmware_version": self.power_manager.get_firmware_version() if self.is_initialized() else None
            }
        }
        
        if include_location:
            try:
                location = self.get_location(force_refresh_location)
                result["location"] = location
            except Exception as e:
                result["location"] = {"error": str(e)}
        
        return result
    
    def get_coordinates(self) -> Tuple[float, float]:
        """
        Get current latitude and longitude coordinates.
        
        Returns:
            Tuple of (latitude, longitude)
        """
        location = self.get_location()
        return (location["latitude"], location["longitude"])
    
    def get_location_string(self) -> str:
        """
        Get formatted location string.
        
        Returns:
            Formatted location string
        """
        from .location import LocationDetector
        
        if not hasattr(self, '_location_detector'):
            self._location_detector = LocationDetector()
        
        return self._location_detector.get_location_string()
        self.logger.debug("Reading history cleared")
    
    def save_readings_to_file(self, file_path: Union[str, Path], 
                            format_type: str = "csv") -> bool:
        """
        Save reading history to file.
        
        Args:
            file_path: Path to save file
            format_type: File format ("csv", "json", "txt")
            
        Returns:
            True if successful
        """
        return save_readings_to_file(self._reading_history, file_path, format_type)
    
    def get_reading_statistics(self) -> Dict[str, Any]:
        """Get statistics for all readings."""
        return create_reading_summary(self._reading_history)
    
    # Performance and Status Methods
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance and communication statistics."""
        i2c_stats = self.i2c.get_statistics()
        
        return {
            "total_readings": self._total_readings,
            "total_errors": self._total_errors,
            "error_rate": (self._total_errors / max(self._total_readings, 1)) * 100,
            "last_reading_time": self._last_reading_time,
            "uptime_seconds": time.time() - self._initialization_time if self._initialization_time else 0,
            "i2c_statistics": i2c_stats,
            "cache_info": {
                "concentration_cache": self.concentration_reader.get_cache_info(),
                "particle_count_cache": self.particle_counter.get_cache_info()
            },
            "history_size": len(self._reading_history),
            "max_history_size": self._max_history_size
        }
    
    def reset_statistics(self):
        """Reset performance statistics."""
        self._total_readings = 0
        self._total_errors = 0
        self._last_reading_time = None
        self.i2c.reset_statistics()
        self.logger.debug("Performance statistics reset")
    
    def clear_all_caches(self):
        """Clear all sensor data caches."""
        self.concentration_reader.clear_cache()
        self.particle_counter.clear_cache()
        self.logger.debug("All caches cleared")
    
    def get_sensor_status(self) -> Dict[str, Any]:
        """Get comprehensive sensor status."""
        return {
            "is_initialized": self.is_initialized(),
            "is_connected": self.is_connected(),
            "is_sleeping": self.is_sleeping(),
            "is_warmed_up": self.is_warmed_up(),
            "firmware_version": self._safe_get_version(),
            "configuration": self.config.to_dict(),
            "performance": self.get_performance_statistics(),
            "timestamp": time.time()
        }
    
    # Context Manager Support
    def __enter__(self):
        """Context manager entry."""
        if not self.is_initialized():
            self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    # Private Helper Methods
    def _track_reading(self, reading_type: str, value: Any) -> Any:
        """Track reading for performance statistics."""
        self._total_readings += 1
        self._last_reading_time = time.time()
        return value
    
    def _add_to_history(self, reading: Dict[str, Any]):
        """Add reading to history with size management."""
        self._reading_history.append(reading)
        
        # Maintain maximum history size
        if len(self._reading_history) > self._max_history_size:
            self._reading_history.pop(0)
    
    def _safe_get_version(self) -> Optional[int]:
        """Safely get firmware version."""
        try:
            return self.get_firmware_version()
        except Exception:
            return None
    
    def __repr__(self) -> str:
        """String representation of sensor."""
        status = "connected" if self.is_connected() else "disconnected"
        return f"PM25Sensor(address=0x{self.i2c.device_address:02X}, status={status})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        if not self.is_initialized():
            return "PM25 Sensor (not initialized)"
        
        try:
            pm25 = self.get_pm2_5_standard(use_cache=True)
            return f"PM25 Sensor (PM2.5: {pm25} μg/m³)"
        except Exception:
            return f"PM25 Sensor (connected, address=0x{self.i2c.device_address:02X})"


# Convenience function for quick sensor access
def create_sensor(config_path: Optional[Union[str, Path]] = None,
                auto_connect: bool = True, auto_warmup: bool = True) -> PM25Sensor:
    """
    Create and initialize PM25 sensor with optional configuration file.
    
    Args:
        config_path: Path to configuration file
        auto_connect: Whether to automatically connect
        auto_warmup: Whether to automatically warm up
        
    Returns:
        Initialized PM25Sensor instance
    """
    if config_path:
        config = PM25Config.load_from_file(config_path)
    else:
        config = load_config()
    
    return PM25Sensor(config, auto_connect, auto_warmup)
