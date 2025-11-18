"""
PM25 Sensor PM Concentration Functions

This module provides functions for reading PM concentration values
from the PM25 sensor in both standard and atmospheric units.
"""

import logging
import time
from typing import Optional, Dict, Any

from .constants import (
    PARTICLE_PM1_0_STANDARD, PARTICLE_PM2_5_STANDARD, PARTICLE_PM10_STANDARD,
    PARTICLE_PM1_0_ATMOSPHERE, PARTICLE_PM2_5_ATMOSPHERE, PARTICLE_PM10_ATMOSPHERE,
    DATA_LENGTH_2_BYTES, BYTE_SHIFT, MAX_PM_CONCENTRATION, PM_TYPES
)
from .exceptions import (
    InvalidDataError, CalibrationError, SensorNotInitializedError,
    handle_sensor_exception
)
from .i2c_interface import I2CInterface
from .config import PM25Config


class ConcentrationReader:
    """Class for reading PM concentration values from the sensor."""
    
    def __init__(self, i2c_interface: I2CInterface, config: PM25Config):
        """Initialize concentration reader with I2C interface and configuration."""
        self.i2c = i2c_interface
        self.config = config
        self.logger = logging.getLogger("pm25_sensor.concentration")
        
        # Caching for performance
        self._cache: Dict[int, Dict[str, Any]] = {}
        self._cache_timeout = config.get("performance.cache_timeout", 0.5)
        
        # Validation settings
        self._enable_validation = config.get("sensor.enable_validation", True)
        self._max_concentration = config.get("sensor.max_pm_concentration", MAX_PM_CONCENTRATION)
    
    @handle_sensor_exception
    def get_pm1_0_standard(self, use_cache: bool = False) -> int:
        """
        Get PM1.0 concentration in standard units (μg/m³).
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            PM1.0 concentration in μg/m³
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_concentration(PARTICLE_PM1_0_STANDARD, use_cache)
    
    @handle_sensor_exception
    def get_pm2_5_standard(self, use_cache: bool = False) -> int:
        """
        Get PM2.5 concentration in standard units (μg/m³).
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            PM2.5 concentration in μg/m³
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_concentration(PARTICLE_PM2_5_STANDARD, use_cache)
    
    @handle_sensor_exception
    def get_pm10_standard(self, use_cache: bool = False) -> int:
        """
        Get PM10 concentration in standard units (μg/m³).
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            PM10 concentration in μg/m³
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_concentration(PARTICLE_PM10_STANDARD, use_cache)
    
    @handle_sensor_exception
    def get_pm1_0_atmospheric(self, use_cache: bool = False) -> int:
        """
        Get PM1.0 concentration in atmospheric units (μg/m³).
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            PM1.0 atmospheric concentration in μg/m³
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_concentration(PARTICLE_PM1_0_ATMOSPHERE, use_cache)
    
    @handle_sensor_exception
    def get_pm2_5_atmospheric(self, use_cache: bool = False) -> int:
        """
        Get PM2.5 concentration in atmospheric units (μg/m³).
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            PM2.5 atmospheric concentration in μg/m³
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_concentration(PARTICLE_PM2_5_ATMOSPHERE, use_cache)
    
    @handle_sensor_exception
    def get_pm10_atmospheric(self, use_cache: bool = False) -> int:
        """
        Get PM10 concentration in atmospheric units (μg/m³).
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            PM10 atmospheric concentration in μg/m³
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_concentration(PARTICLE_PM10_ATMOSPHERE, use_cache)
    
    def get_all_standard(self, use_cache: bool = False) -> Dict[str, int]:
        """
        Get all standard PM concentrations in a single call.
        
        Args:
            use_cache: Whether to use cached values if available
            
        Returns:
            Dictionary with PM1.0, PM2.5, and PM10 standard concentrations
        """
        return {
            "PM1.0": self.get_pm1_0_standard(use_cache),
            "PM2.5": self.get_pm2_5_standard(use_cache),
            "PM10": self.get_pm10_standard(use_cache)
        }
    
    def get_all_atmospheric(self, use_cache: bool = False) -> Dict[str, int]:
        """
        Get all atmospheric PM concentrations in a single call.
        
        Args:
            use_cache: Whether to use cached values if available
            
        Returns:
            Dictionary with PM1.0, PM2.5, and PM10 atmospheric concentrations
        """
        return {
            "PM1.0": self.get_pm1_0_atmospheric(use_cache),
            "PM2.5": self.get_pm2_5_atmospheric(use_cache),
            "PM10": self.get_pm10_atmospheric(use_cache)
        }
    
    def get_all_concentrations(self, use_cache: bool = False) -> Dict[str, Dict[str, int]]:
        """
        Get all PM concentrations (both standard and atmospheric) in a single call.
        
        Args:
            use_cache: Whether to use cached values if available
            
        Returns:
            Dictionary with nested standard and atmospheric concentrations
        """
        return {
            "standard": self.get_all_standard(use_cache),
            "atmospheric": self.get_all_atmospheric(use_cache)
        }
    
    def _read_concentration(self, register: int, use_cache: bool = False) -> int:
        """
        Read concentration value from sensor register.
        
        Args:
            register: Register address to read from
            use_cache: Whether to use cached value if available
            
        Returns:
            Concentration value in μg/m³
            
        Raises:
            InvalidDataError: If data is invalid
            CalibrationError: If reading is out of valid range
        """
        # Check cache first
        if use_cache and self._is_cache_valid(register):
            cached_data = self._cache[register]
            self.logger.debug(f"Using cached value for register 0x{register:02X}")
            return cached_data["value"]
        
        # Read from sensor
        data = self.i2c.read_register(register, DATA_LENGTH_2_BYTES)
        
        if len(data) != DATA_LENGTH_2_BYTES:
            raise InvalidDataError(
                f"Expected {DATA_LENGTH_2_BYTES} bytes, got {len(data)}",
                raw_data=data,
                expected_length=DATA_LENGTH_2_BYTES
            )
        
        # Convert bytes to concentration value (MSB first)
        concentration = (data[0] << BYTE_SHIFT) + data[1]
        
        # Validate reading
        if self._enable_validation:
            self._validate_concentration(concentration, register)
        
        # Update cache
        self._update_cache(register, concentration)
        
        # Log reading if debug mode is enabled
        if self.config.get("debug.log_timing", False):
            self.logger.debug(f"Read concentration from 0x{register:02X}: {concentration} μg/m³")
        
        return concentration
    
    def _validate_concentration(self, concentration: int, register: int):
        """
        Validate concentration reading is within expected range.
        
        Args:
            concentration: Concentration value to validate
            register: Register address the value was read from
            
        Raises:
            CalibrationError: If concentration is out of valid range
        """
        if concentration < 0:
            raise CalibrationError(
                PM_TYPES.get(register, f"register 0x{register:02X}"),
                concentration,
                (0, self._max_concentration)
            )
        
        if concentration > self._max_concentration:
            # Log warning but don't raise exception for slightly high values
            # (sensor might be in very polluted environment)
            self.logger.warning(
                f"High concentration reading: {concentration} μg/m³ "
                f"(max expected: {self._max_concentration} μg/m³)"
            )
    
    def _is_cache_valid(self, register: int) -> bool:
        """Check if cached value is still valid."""
        if register not in self._cache:
            return False
        
        cached_time = self._cache[register]["timestamp"]
        return (time.time() - cached_time) < self._cache_timeout
    
    def _update_cache(self, register: int, value: int):
        """Update cached value with current timestamp."""
        self._cache[register] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def clear_cache(self):
        """Clear all cached concentration values."""
        self._cache.clear()
        self.logger.debug("Concentration cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached values."""
        current_time = time.time()
        cache_info = {}
        
        for register, data in self._cache.items():
            age = current_time - data["timestamp"]
            cache_info[f"0x{register:02X}"] = {
                "value": data["value"],
                "timestamp": data["timestamp"],
                "age_seconds": age,
                "valid": age < self._cache_timeout
            }
        
        return cache_info
    
    def get_pm_type_description(self, register: int) -> str:
        """Get human-readable description for PM type register."""
        return PM_TYPES.get(register, f"Unknown register 0x{register:02X}")
    
    def is_valid_pm_register(self, register: int) -> bool:
        """Check if register is a valid PM concentration register."""
        return register in [
            PARTICLE_PM1_0_STANDARD, PARTICLE_PM2_5_STANDARD, PARTICLE_PM10_STANDARD,
            PARTICLE_PM1_0_ATMOSPHERE, PARTICLE_PM2_5_ATMOSPHERE, PARTICLE_PM10_ATMOSPHERE
        ]


# Convenience functions for direct access
def get_pm1_0_standard(i2c: I2CInterface, config: PM25Config, use_cache: bool = False) -> int:
    """Convenience function to get PM1.0 standard concentration."""
    reader = ConcentrationReader(i2c, config)
    return reader.get_pm1_0_standard(use_cache)


def get_pm2_5_standard(i2c: I2CInterface, config: PM25Config, use_cache: bool = False) -> int:
    """Convenience function to get PM2.5 standard concentration."""
    reader = ConcentrationReader(i2c, config)
    return reader.get_pm2_5_standard(use_cache)


def get_pm10_standard(i2c: I2CInterface, config: PM25Config, use_cache: bool = False) -> int:
    """Convenience function to get PM10 standard concentration."""
    reader = ConcentrationReader(i2c, config)
    return reader.get_pm10_standard(use_cache)


def get_all_standard(i2c: I2CInterface, config: PM25Config, use_cache: bool = False) -> Dict[str, int]:
    """Convenience function to get all standard concentrations."""
    reader = ConcentrationReader(i2c, config)
    return reader.get_all_standard(use_cache)
