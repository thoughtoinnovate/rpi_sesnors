"""
PM25 Sensor I2C Interface

This module provides robust I2C communication with the PM25 sensor,
including retry logic, error handling, and connection management.
"""

import time
import logging
try:
    import smbus
except ImportError:
    import smbus2 as smbus
from typing import List, Optional, Union

from .constants import VALID_REGISTERS, ERROR_CODE, DATA_LENGTH_2_BYTES, DATA_LENGTH_1_BYTE
from .exceptions import (
    CommunicationError, SensorNotRespondingError, InvalidRegisterError,
    InvalidDataError, TimeoutError, handle_sensor_exception
)
from .config import PM25Config


class I2CInterface:
    """Robust I2C interface for PM25 sensor communication."""
    
    def __init__(self, config: PM25Config):
        """Initialize I2C interface with configuration."""
        self.config = config
        self.logger = logging.getLogger("pm25_sensor.i2c")
        
        # I2C configuration
        self.bus_number = config.get("i2c.bus")
        self.device_address = config.get("i2c.address")
        self.timeout = config.get("i2c.timeout")
        self.max_retries = config.get("i2c.max_retries")
        self.retry_delay = config.get("i2c.retry_delay")
        
        # Connection state
        self._bus: Optional[smbus.SMBus] = None
        self._is_connected = False
        self._last_error: Optional[Exception] = None
        
        # Performance tracking
        self._read_count = 0
        self._error_count = 0
        self._last_read_time: Optional[float] = None
    
    def connect(self) -> bool:
        """
        Establish I2C connection to sensor.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self._bus is not None:
                self.disconnect()
            
            self.logger.debug(f"Connecting to I2C bus {self.bus_number}, address 0x{self.device_address:02X}")
            self._bus = smbus.SMBus(self.bus_number)
            
            # Test connection by reading version register
            version_data = self._raw_read(0x1D, DATA_LENGTH_1_BYTE, retry=False)
            if version_data != ERROR_CODE:
                self._is_connected = True
                self.logger.info(f"Connected to PM25 sensor at 0x{self.device_address:02X}")
                return True
            else:
                self.logger.error("Failed to read version register during connection test")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to sensor: {e}")
            self._last_error = e
            self._is_connected = False
            return False
    
    def disconnect(self):
        """Close I2C connection."""
        if self._bus is not None:
            try:
                self._bus.close()
                self.logger.debug("I2C connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing I2C connection: {e}")
            finally:
                self._bus = None
                self._is_connected = False
    
    def is_connected(self) -> bool:
        """Check if I2C connection is active."""
        return self._is_connected and self._bus is not None
    
    @handle_sensor_exception
    def read_register(self, register: int, length: int = DATA_LENGTH_2_BYTES) -> List[int]:
        """
        Read data from sensor register with retry logic.
        
        Args:
            register: Register address to read from
            length: Number of bytes to read
            
        Returns:
            List of bytes read from register
            
        Raises:
            InvalidRegisterError: If register is not valid
            CommunicationError: If communication fails
            InvalidDataError: If data is invalid
        """
        if not self.is_connected():
            if not self.connect():
                raise CommunicationError("Not connected to sensor", address=self.device_address)
        
        # Validate register
        if register not in VALID_REGISTERS:
            raise InvalidRegisterError(register, VALID_REGISTERS)
        
        # Validate length
        if length not in [DATA_LENGTH_1_BYTE, DATA_LENGTH_2_BYTES]:
            raise InvalidDataError(f"Invalid data length: {length}", expected_length="1 or 2")
        
        # Perform read with retry logic
        data = self._raw_read(register, length)
        
        if data == ERROR_CODE:
            self._error_count += 1
            raise CommunicationError(
                f"Failed to read register 0x{register:02X}",
                register=register,
                address=self.device_address,
                retry_count=self.max_retries
            )
        
        self._read_count += 1
        self._last_read_time = time.time()
        
        # Log raw data if debug mode is enabled
        if self.config.get("debug.log_raw_data", False):
            self.logger.debug(f"Read register 0x{register:02X}: {data}")
        
        return data
    
    @handle_sensor_exception
    def write_register(self, register: int, data: List[int]) -> bool:
        """
        Write data to sensor register with retry logic.
        
        Args:
            register: Register address to write to
            data: List of bytes to write
            
        Returns:
            True if write successful, False otherwise
            
        Raises:
            CommunicationError: If communication fails
        """
        if not self.is_connected():
            if not self.connect():
                raise CommunicationError("Not connected to sensor", address=self.device_address)
        
        # Validate register
        if register not in VALID_REGISTERS:
            raise InvalidRegisterError(register, VALID_REGISTERS)
        
        # Validate data
        if not data or len(data) == 0:
            raise InvalidDataError("No data to write")
        
        # Perform write with retry logic
        success = self._raw_write(register, data)
        
        if not success:
            self._error_count += 1
            raise CommunicationError(
                f"Failed to write register 0x{register:02X}",
                register=register,
                address=self.device_address,
                retry_count=self.max_retries
            )
        
        # Log raw data if debug mode is enabled
        if self.config.get("debug.log_raw_data", False):
            self.logger.debug(f"Wrote register 0x{register:02X}: {data}")
        
        return True
    
    def _raw_read(self, register: int, length: int, retry: bool = True) -> List[int]:
        """
        Perform raw I2C read with optional retry logic.
        
        Args:
            register: Register address to read
            length: Number of bytes to read
            retry: Whether to use retry logic
            
        Returns:
            List of bytes read, or ERROR_CODE if failed
        """
        if not retry:
            return self._attempt_read(register, length)
        
        for attempt in range(self.max_retries + 1):
            try:
                result = self._attempt_read(register, length)
                if result != ERROR_CODE:
                    return result
                
                if attempt < self.max_retries:
                    self.logger.warning(f"Read attempt {attempt + 1} failed, retrying...")
                    time.sleep(self.retry_delay)
                
            except Exception as e:
                if attempt == self.max_retries:
                    self.logger.error(f"All {self.max_retries + 1} read attempts failed: {e}")
                    raise CommunicationError(
                        f"Read failed after {self.max_retries + 1} attempts: {e}",
                        register=register,
                        address=self.device_address,
                        retry_count=attempt + 1
                    ) from e
                
                self.logger.warning(f"Read attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(self.retry_delay)
        
        return ERROR_CODE
    
    def _attempt_read(self, register: int, length: int) -> List[int]:
        """
        Attempt a single I2C read operation.
        
        Args:
            register: Register address to read
            length: Number of bytes to read
            
        Returns:
            List of bytes read, or ERROR_CODE if failed
        """
        try:
            if self._bus is None:
                return ERROR_CODE
            
            # Set timeout for read operation
            start_time = time.time()
            result = self._bus.read_i2c_block_data(self.device_address, register, length)
            
            # Check if operation timed out
            if time.time() - start_time > self.timeout:
                raise TimeoutError("read_i2c_block_data", self.timeout)
            
            # Validate result
            if not result or len(result) != length:
                raise InvalidDataError(
                    f"Invalid read result: {result}",
                    raw_data=result,
                    expected_length=length
                )
            
            return result
            
        except (IOError, OSError) as e:
            self.logger.debug(f"I2C read error: {e}")
            return ERROR_CODE
        except Exception as e:
            self.logger.debug(f"Unexpected read error: {e}")
            return ERROR_CODE
    
    def _raw_write(self, register: int, data: List[int], retry: bool = True) -> bool:
        """
        Perform raw I2C write with optional retry logic.
        
        Args:
            register: Register address to write
            data: List of bytes to write
            retry: Whether to use retry logic
            
        Returns:
            True if successful, False otherwise
        """
        if not retry:
            return self._attempt_write(register, data)
        
        for attempt in range(self.max_retries + 1):
            try:
                result = self._attempt_write(register, data)
                if result:
                    return True
                
                if attempt < self.max_retries:
                    self.logger.warning(f"Write attempt {attempt + 1} failed, retrying...")
                    time.sleep(self.retry_delay)
                
            except Exception as e:
                if attempt == self.max_retries:
                    self.logger.error(f"All {self.max_retries + 1} write attempts failed: {e}")
                    raise CommunicationError(
                        f"Write failed after {self.max_retries + 1} attempts: {e}",
                        register=register,
                        address=self.device_address,
                        retry_count=attempt + 1
                    ) from e
                
                self.logger.warning(f"Write attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(self.retry_delay)
        
        return False
    
    def _attempt_write(self, register: int, data: List[int]) -> bool:
        """
        Attempt a single I2C write operation.
        
        Args:
            register: Register address to write
            data: List of bytes to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self._bus is None:
                return False
            
            # Set timeout for write operation
            start_time = time.time()
            self._bus.write_i2c_block_data(self.device_address, register, data)
            
            # Check if operation timed out
            if time.time() - start_time > self.timeout:
                raise TimeoutError("write_i2c_block_data", self.timeout)
            
            return True
            
        except (IOError, OSError) as e:
            self.logger.debug(f"I2C write error: {e}")
            return False
        except Exception as e:
            self.logger.debug(f"Unexpected write error: {e}")
            return False
    
    def get_statistics(self) -> dict:
        """Get communication statistics."""
        return {
            "read_count": self._read_count,
            "error_count": self._error_count,
            "success_rate": (self._read_count - self._error_count) / max(self._read_count, 1),
            "last_read_time": self._last_read_time,
            "is_connected": self.is_connected(),
            "last_error": str(self._last_error) if self._last_error else None
        }
    
    def reset_statistics(self):
        """Reset communication statistics."""
        self._read_count = 0
        self._error_count = 0
        self._last_read_time = None
        self._last_error = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
