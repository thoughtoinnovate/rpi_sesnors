"""
PM25 Sensor Particle Count Functions

This module provides functions for reading particle count values
from PM25 sensor for different particle sizes.
"""

import logging
import time
from typing import Optional, Dict, Any

from .constants import (
    PARTICLENUM_0_3_UM_EVERY0_1L_AIR, PARTICLENUM_0_5_UM_EVERY0_1L_AIR,
    PARTICLENUM_1_0_UM_EVERY0_1L_AIR, PARTICLENUM_2_5_UM_EVERY0_1L_AIR,
    PARTICLENUM_5_0_UM_EVERY0_1L_AIR, PARTICLENUM_10_UM_EVERY0_1L_AIR,
    DATA_LENGTH_2_BYTES, BYTE_SHIFT, MAX_PARTICLE_COUNT, PARTICLE_SIZES
)
from .exceptions import (
    InvalidDataError, CalibrationError, SensorNotInitializedError,
    handle_sensor_exception
)
from .i2c_interface import I2CInterface
from .config import PM25Config


class ParticleCounter:
    """Class for reading particle count values from sensor."""
    
    def __init__(self, i2c_interface: I2CInterface, config: PM25Config):
        """Initialize particle counter with I2C interface and configuration."""
        self.i2c = i2c_interface
        self.config = config
        self.logger = logging.getLogger("pm25_sensor.particle_count")
        
        # Caching for performance
        self._cache: Dict[int, Dict[str, Any]] = {}
        self._cache_timeout = config.get("performance.cache_timeout", 0.5)
        
        # Validation settings
        self._enable_validation = config.get("sensor.enable_validation", True)
        self._max_particle_count = config.get("sensor.max_particle_count", MAX_PARTICLE_COUNT)
    
    @handle_sensor_exception
    def get_particles_0_3um(self, use_cache: bool = False) -> int:
        """
        Get particle count for 0.3μm particles per 0.1L of air.
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            Number of 0.3μm particles per 0.1L
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_particle_count(PARTICLENUM_0_3_UM_EVERY0_1L_AIR, use_cache)
    
    @handle_sensor_exception
    def get_particles_0_5um(self, use_cache: bool = False) -> int:
        """
        Get particle count for 0.5μm particles per 0.1L of air.
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            Number of 0.5μm particles per 0.1L
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_particle_count(PARTICLENUM_0_5_UM_EVERY0_1L_AIR, use_cache)
    
    @handle_sensor_exception
    def get_particles_1_0um(self, use_cache: bool = False) -> int:
        """
        Get particle count for 1.0μm particles per 0.1L of air.
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            Number of 1.0μm particles per 0.1L
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_particle_count(PARTICLENUM_1_0_UM_EVERY0_1L_AIR, use_cache)
    
    @handle_sensor_exception
    def get_particles_2_5um(self, use_cache: bool = False) -> int:
        """
        Get particle count for 2.5μm particles per 0.1L of air.
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            Number of 2.5μm particles per 0.1L
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_particle_count(PARTICLENUM_2_5_UM_EVERY0_1L_AIR, use_cache)
    
    @handle_sensor_exception
    def get_particles_5_0um(self, use_cache: bool = False) -> int:
        """
        Get particle count for 5.0μm particles per 0.1L of air.
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            Number of 5.0μm particles per 0.1L
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_particle_count(PARTICLENUM_5_0_UM_EVERY0_1L_AIR, use_cache)
    
    @handle_sensor_exception
    def get_particles_10um(self, use_cache: bool = False) -> int:
        """
        Get particle count for 10μm particles per 0.1L of air.
        
        Args:
            use_cache: Whether to use cached value if available
            
        Returns:
            Number of 10μm particles per 0.1L
            
        Raises:
            CommunicationError: If I2C communication fails
            CalibrationError: If reading is out of valid range
        """
        return self._read_particle_count(PARTICLENUM_10_UM_EVERY0_1L_AIR, use_cache)
    
    def get_all_particle_counts(self, use_cache: bool = False) -> Dict[str, int]:
        """
        Get all particle counts in a single call.
        
        Args:
            use_cache: Whether to use cached values if available
            
        Returns:
            Dictionary with particle counts for all sizes
        """
        return {
            "0.3um": self.get_particles_0_3um(use_cache),
            "0.5um": self.get_particles_0_5um(use_cache),
            "1.0um": self.get_particles_1_0um(use_cache),
            "2.5um": self.get_particles_2_5um(use_cache),
            "5.0um": self.get_particles_5_0um(use_cache),
            "10um": self.get_particles_10um(use_cache)
        }
    
    def get_particle_size_distribution(self, use_cache: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get particle size distribution with additional analysis.
        
        Args:
            use_cache: Whether to use cached values if available
            
        Returns:
            Dictionary with particle counts and distribution analysis
        """
        counts = self.get_all_particle_counts(use_cache)
        
        # Calculate total particles
        total_particles = sum(counts.values())
        
        # Calculate percentage distribution
        distribution = {}
        for size, count in counts.items():
            percentage = (count / total_particles * 100) if total_particles > 0 else 0
            distribution[size] = {
                "count": count,
                "percentage": round(percentage, 2)
            }
        
        # Determine dominant particle size
        dominant_size = max(counts.items(), key=lambda x: x[1])[0] if counts else "N/A"
        
        return {
            "counts": counts,
            "distribution": distribution,
            "total_particles": total_particles,
            "dominant_size": dominant_size,
            "timestamp": time.time()
        }
    
    def get_air_quality_index(self, use_cache: bool = False) -> Dict[str, Any]:
        """
        Calculate simple air quality index based on particle counts.
        
        Args:
            use_cache: Whether to use cached values if available
            
        Returns:
            Dictionary with AQI calculation and classification
        """
        counts = self.get_all_particle_counts(use_cache)
        
        # Simple AQI calculation based on PM2.5 equivalent
        # This is a simplified calculation - real AQI is more complex
        pm2_5_count = counts.get("2.5um", 0)
        pm10_count = counts.get("10um", 0)
        
        # Convert particle counts to approximate mass concentration
        # (very rough approximation for demonstration)
        pm2_5_mass = pm2_5_count * 0.0001  # rough conversion
        pm10_mass = pm10_count * 0.0002    # rough conversion
        
        # Simple AQI categories
        total_mass = pm2_5_mass + pm10_mass
        
        if total_mass < 12:
            aqi_level = "Good"
            aqi_color = "green"
        elif total_mass < 35:
            aqi_level = "Moderate"
            aqi_color = "yellow"
        elif total_mass < 55:
            aqi_level = "Unhealthy for Sensitive"
            aqi_color = "orange"
        elif total_mass < 150:
            aqi_level = "Unhealthy"
            aqi_color = "red"
        else:
            aqi_level = "Hazardous"
            aqi_color = "purple"
        
        return {
            "aqi_level": aqi_level,
            "aqi_color": aqi_color,
            "estimated_mass": total_mass,
            "particle_counts": counts,
            "calculation_method": "simplified_particle_to_mass",
            "timestamp": time.time()
        }
    
    def _read_particle_count(self, register: int, use_cache: bool = False) -> int:
        """
        Read particle count value from sensor register.
        
        Args:
            register: Register address to read from
            use_cache: Whether to use cached value if available
            
        Returns:
            Particle count value
            
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
        
        # Convert bytes to particle count (MSB first)
        particle_count = (data[0] << BYTE_SHIFT) + data[1]
        
        # Validate reading
        if self._enable_validation:
            self._validate_particle_count(particle_count, register)
        
        # Update cache
        self._update_cache(register, particle_count)
        
        # Log reading if debug mode is enabled
        if self.config.get("debug.log_timing", False):
            size_desc = PARTICLE_SIZES.get(register, f"register 0x{register:02X}")
            self.logger.debug(f"Read particle count for {size_desc}: {particle_count}")
        
        return particle_count
    
    def _validate_particle_count(self, particle_count: int, register: int):
        """
        Validate particle count reading is within expected range.
        
        Args:
            particle_count: Particle count value to validate
            register: Register address value was read from
            
        Raises:
            CalibrationError: If particle count is out of valid range
        """
        if particle_count < 0:
            raise CalibrationError(
                PARTICLE_SIZES.get(register, f"register 0x{register:02X}"),
                particle_count,
                (0, self._max_particle_count)
            )
        
        if particle_count > self._max_particle_count:
            # Log warning but don't raise exception for slightly high values
            # (sensor might be in very dusty environment)
            self.logger.warning(
                f"High particle count: {particle_count} "
                f"(max expected: {self._max_particle_count})"
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
        """Clear all cached particle count values."""
        self._cache.clear()
        self.logger.debug("Particle count cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached values."""
        current_time = time.time()
        cache_info = {}
        
        for register, data in self._cache.items():
            age = current_time - data["timestamp"]
            size_desc = PARTICLE_SIZES.get(register, f"0x{register:02X}")
            cache_info[size_desc] = {
                "value": data["value"],
                "timestamp": data["timestamp"],
                "age_seconds": age,
                "valid": age < self._cache_timeout
            }
        
        return cache_info
    
    def get_particle_size_description(self, register: int) -> str:
        """Get human-readable description for particle size register."""
        return PARTICLE_SIZES.get(register, f"Unknown register 0x{register:02X}")
    
    def is_valid_particle_register(self, register: int) -> bool:
        """Check if register is a valid particle count register."""
        return register in [
            PARTICLENUM_0_3_UM_EVERY0_1L_AIR, PARTICLENUM_0_5_UM_EVERY0_1L_AIR,
            PARTICLENUM_1_0_UM_EVERY0_1L_AIR, PARTICLENUM_2_5_UM_EVERY0_1L_AIR,
            PARTICLENUM_5_0_UM_EVERY0_1L_AIR, PARTICLENUM_10_UM_EVERY0_1L_AIR
        ]


# Convenience functions for direct access
def get_particles_0_3um(i2c: I2CInterface, config: PM25Config, use_cache: bool = False) -> int:
    """Convenience function to get 0.3μm particle count."""
    counter = ParticleCounter(i2c, config)
    return counter.get_particles_0_3um(use_cache)


def get_particles_2_5um(i2c: I2CInterface, config: PM25Config, use_cache: bool = False) -> int:
    """Convenience function to get 2.5μm particle count."""
    counter = ParticleCounter(i2c, config)
    return counter.get_particles_2_5um(use_cache)


def get_all_particle_counts(i2c: I2CInterface, config: PM25Config, use_cache: bool = False) -> Dict[str, int]:
    """Convenience function to get all particle counts."""
    counter = ParticleCounter(i2c, config)
    return counter.get_all_particle_counts(use_cache)
