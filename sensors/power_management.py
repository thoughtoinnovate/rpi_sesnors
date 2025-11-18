"""
PM25 Sensor Power Management Functions

This module provides functions for managing power states of the PM25 sensor,
including sleep/wake functionality and version information.
"""

import logging
import time
from typing import Optional, Dict, Any

from .constants import (
    POWER_MODE_REGISTER, POWER_MODE_SLEEP, POWER_MODE_WAKE,
    PARTICLENUM_GAIN_VERSION, DATA_LENGTH_1_BYTE, WARMUP_TIME_SECONDS
)
from .exceptions import (
    CommunicationError, PowerManagementError, SensorNotInitializedError,
    handle_sensor_exception
)
from .i2c_interface import I2CInterface
from .config import PM25Config


class PowerManager:
    """Class for managing power states and system information of the sensor."""
    
    def __init__(self, i2c_interface: I2CInterface, config: PM25Config):
        """Initialize power manager with I2C interface and configuration."""
        self.i2c = i2c_interface
        self.config = config
        self.logger = logging.getLogger("pm25_sensor.power_management")
        
        # Power state tracking
        self._is_sleeping = False
        self._last_wake_time: Optional[float] = None
        self._warmup_time = config.get("sensor.warmup_time", WARMUP_TIME_SECONDS)
        
        # Auto warmup settings
        self._auto_warmup = config.get("sensor.auto_warmup", True)
    
    @handle_sensor_exception
    def enter_sleep_mode(self) -> bool:
        """
        Put the sensor into low-power sleep mode.
        
        Returns:
            True if sleep mode was successfully entered
            
        Raises:
            CommunicationError: If I2C communication fails
            PowerManagementError: If power mode change fails
        """
        try:
            self.logger.info("Entering sleep mode")
            
            # Send sleep command to sensor
            success = self.i2c.write_register(POWER_MODE_REGISTER, [POWER_MODE_SLEEP])
            
            if success:
                self._is_sleeping = True
                self.logger.debug("Sensor successfully entered sleep mode")
                return True
            else:
                raise PowerManagementError("sleep", "Failed to write sleep command")
                
        except Exception as e:
            raise PowerManagementError("sleep", f"Unexpected error: {str(e)}") from e
    
    @handle_sensor_exception
    def wake_from_sleep(self) -> bool:
        """
        Wake the sensor from sleep mode.
        
        Returns:
            True if sensor was successfully woken
            
        Raises:
            CommunicationError: If I2C communication fails
            PowerManagementError: If power mode change fails
        """
        try:
            self.logger.info("Waking from sleep mode")
            
            # Send wake command to sensor
            success = self.i2c.write_register(POWER_MODE_REGISTER, [POWER_MODE_WAKE])
            
            if success:
                self._is_sleeping = False
                self._last_wake_time = time.time()
                self.logger.debug("Sensor successfully woke from sleep mode")
                
                # Auto warmup if enabled
                if self._auto_warmup:
                    self.logger.debug(f"Starting auto warmup for {self._warmup_time}s")
                    time.sleep(self._warmup_time)
                    self.logger.debug("Auto warmup completed")
                
                return True
            else:
                raise PowerManagementError("wake", "Failed to write wake command")
                
        except Exception as e:
            raise PowerManagementError("wake", f"Unexpected error: {str(e)}") from e
    
    def is_sleeping(self) -> bool:
        """
        Check if sensor is currently in sleep mode.
        
        Returns:
            True if sensor is sleeping, False otherwise
        """
        return self._is_sleeping
    
    def is_warmed_up(self) -> bool:
        """
        Check if sensor has completed warmup period after waking.
        
        Returns:
            True if sensor is warmed up, False otherwise
        """
        if self._last_wake_time is None:
            return True  # Assume warmed up if never woken
        
        warmup_elapsed = time.time() - self._last_wake_time
        return warmup_elapsed >= self._warmup_time
    
    def get_warmup_remaining_time(self) -> float:
        """
        Get remaining warmup time in seconds.
        
        Returns:
            Remaining warmup time in seconds (0 if already warmed up)
        """
        if self._last_wake_time is None:
            return 0.0
        
        warmup_elapsed = time.time() - self._last_wake_time
        remaining = self._warmup_time - warmup_elapsed
        return max(0.0, remaining)
    
    def wait_for_warmup(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for sensor to complete warmup period.
        
        Args:
            timeout: Maximum time to wait for warmup (None for no timeout)
            
        Returns:
            True if warmup completed, False if timeout occurred
        """
        if self.is_warmed_up():
            return True
        
        remaining_time = self.get_warmup_remaining_time()
        if timeout is not None:
            remaining_time = min(remaining_time, timeout)
        
        if remaining_time > 0:
            self.logger.debug(f"Waiting for warmup: {remaining_time:.1f}s")
            time.sleep(remaining_time)
        
        return self.is_warmed_up()
    
    @handle_sensor_exception
    def get_firmware_version(self) -> int:
        """
        Get firmware version from sensor.
        
        Returns:
            Firmware version number
            
        Raises:
            CommunicationError: If I2C communication fails
            InvalidDataError: If version data is invalid
        """
        try:
            self.logger.debug("Reading firmware version")
            
            # Read version register
            data = self.i2c.read_register(PARTICLENUM_GAIN_VERSION, DATA_LENGTH_1_BYTE)
            
            if len(data) != DATA_LENGTH_1_BYTE:
                raise CommunicationError(
                    f"Expected {DATA_LENGTH_1_BYTE} byte for version, got {len(data)}",
                    register=PARTICLENUM_GAIN_VERSION
                )
            
            version = data[0]
            self.logger.debug(f"Firmware version: {version}")
            return version
            
        except Exception as e:
            raise CommunicationError(
                f"Failed to read firmware version: {str(e)}",
                register=PARTICLENUM_GAIN_VERSION
            ) from e
    
    def get_sensor_info(self) -> Dict[str, Any]:
        """
        Get comprehensive sensor information.
        
        Returns:
            Dictionary with sensor status and information
        """
        try:
            version = self.get_firmware_version()
        except Exception as e:
            self.logger.warning(f"Failed to read firmware version: {e}")
            version = None
        
        return {
            "firmware_version": version,
            "is_sleeping": self.is_sleeping(),
            "is_warmed_up": self.is_warmed_up(),
            "warmup_remaining_time": self.get_warmup_remaining_time(),
            "warmup_time_setting": self._warmup_time,
            "auto_warmup_enabled": self._auto_warmup,
            "last_wake_time": self._last_wake_time,
            "i2c_address": hex(self.i2c.device_address),
            "i2c_bus": self.i2c.bus_number,
            "timestamp": time.time()
        }
    
    def reset_power_state(self):
        """Reset power state tracking variables."""
        self._is_sleeping = False
        self._last_wake_time = None
        self.logger.debug("Power state tracking reset")
    
    def set_warmup_time(self, warmup_seconds: float):
        """
        Set the warmup time for the sensor.
        
        Args:
            warmup_seconds: Warmup time in seconds
        """
        if warmup_seconds < 0:
            raise ValueError("Warmup time must be non-negative")
        
        self._warmup_time = warmup_seconds
        self.logger.info(f"Warmup time set to {warmup_seconds}s")
    
    def set_auto_warmup(self, enabled: bool):
        """
        Enable or disable automatic warmup after waking.
        
        Args:
            enabled: True to enable auto warmup, False to disable
        """
        self._auto_warmup = enabled
        status = "enabled" if enabled else "disabled"
        self.logger.info(f"Auto warmup {status}")
    
    def perform_power_cycle(self, sleep_duration: float = 1.0) -> bool:
        """
        Perform a complete power cycle (sleep then wake).
        
        Args:
            sleep_duration: How long to stay in sleep mode
            
        Returns:
            True if power cycle was successful
            
        Raises:
            PowerManagementError: If power cycle fails
        """
        try:
            self.logger.info(f"Starting power cycle (sleep: {sleep_duration}s)")
            
            # Enter sleep mode
            if not self.enter_sleep_mode():
                raise PowerManagementError("power_cycle", "Failed to enter sleep mode")
            
            # Sleep for specified duration
            time.sleep(sleep_duration)
            
            # Wake from sleep
            if not self.wake_from_sleep():
                raise PowerManagementError("power_cycle", "Failed to wake from sleep")
            
            self.logger.info("Power cycle completed successfully")
            return True
            
        except Exception as e:
            raise PowerManagementError("power_cycle", f"Power cycle failed: {str(e)}") from e
    
    def get_power_statistics(self) -> Dict[str, Any]:
        """
        Get power management statistics.
        
        Returns:
            Dictionary with power usage statistics
        """
        current_time = time.time()
        
        stats = {
            "current_state": "sleeping" if self.is_sleeping() else "awake",
            "is_warmed_up": self.is_warmed_up(),
            "warmup_remaining_time": self.get_warmup_remaining_time(),
            "auto_warmup_enabled": self._auto_warmup,
            "configured_warmup_time": self._warmup_time
        }
        
        if self._last_wake_time:
            stats["time_since_last_wake"] = current_time - self._last_wake_time
            stats["last_wake_time"] = self._last_wake_time
        else:
            stats["time_since_last_wake"] = None
            stats["last_wake_time"] = None
        
        return stats


# Convenience functions for direct access
def enter_sleep_mode(i2c: I2CInterface, config: PM25Config) -> bool:
    """Convenience function to put sensor in sleep mode."""
    manager = PowerManager(i2c, config)
    return manager.enter_sleep_mode()


def wake_from_sleep(i2c: I2CInterface, config: PM25Config) -> bool:
    """Convenience function to wake sensor from sleep."""
    manager = PowerManager(i2c, config)
    return manager.wake_from_sleep()


def get_firmware_version(i2c: I2CInterface, config: PM25Config) -> int:
    """Convenience function to get firmware version."""
    manager = PowerManager(i2c, config)
    return manager.get_firmware_version()


def perform_power_cycle(i2c: I2CInterface, config: PM25Config, 
                      sleep_duration: float = 1.0) -> bool:
    """Convenience function to perform power cycle."""
    manager = PowerManager(i2c, config)
    return manager.perform_power_cycle(sleep_duration)
