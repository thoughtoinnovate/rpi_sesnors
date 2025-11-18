"""
PM25 Sensor Exception Classes

This module defines custom exception classes for the PM25 sensor API,
providing better error handling and debugging capabilities.
"""

from typing import Optional, Any


class PM25SensorError(Exception):
    """Base exception class for all PM25 sensor errors."""
    
    def __init__(self, message: str, error_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class CommunicationError(PM25SensorError):
    """Raised when I2C communication with the sensor fails."""
    
    def __init__(self, message: str, register: Optional[int] = None, 
                 address: Optional[int] = None, retry_count: Optional[int] = None):
        super().__init__(message)
        self.register = register
        self.address = address
        self.retry_count = retry_count
    
    def __str__(self) -> str:
        details = []
        if self.address:
            details.append(f"address=0x{self.address:02X}")
        if self.register:
            details.append(f"register=0x{self.register:02X}")
        if self.retry_count is not None:
            details.append(f"retries={self.retry_count}")
        
        base_msg = super().__str__()
        if details:
            return f"{base_msg} ({', '.join(details)})"
        return base_msg


class SensorNotRespondingError(CommunicationError):
    """Raised when the sensor doesn't respond to I2C communication."""
    
    def __init__(self, address: int, timeout: float = 1.0):
        message = f"Sensor not responding at address 0x{address:02X} after {timeout}s timeout"
        super().__init__(message, address=address)
        self.timeout = timeout


class InvalidRegisterError(PM25SensorError):
    """Raised when attempting to access an invalid sensor register."""
    
    def __init__(self, register: int, valid_registers: list):
        message = f"Invalid register 0x{register:02X}. Valid registers: {[hex(r) for r in valid_registers]}"
        super().__init__(message, error_code=register)
        self.register = register
        self.valid_registers = valid_registers


class InvalidDataError(PM25SensorError):
    """Raised when sensor returns invalid or corrupted data."""
    
    def __init__(self, message: str, raw_data: Optional[bytes] = None, expected_length: Optional[int] = None):
        super().__init__(message)
        self.raw_data = raw_data
        self.expected_length = expected_length


class SensorNotInitializedError(PM25SensorError):
    """Raised when attempting to use sensor before initialization."""
    
    def __init__(self):
        message = "Sensor not initialized. Call initialize() method first."
        super().__init__(message, error_code=1001)


class ConfigurationError(PM25SensorError):
    """Raised when there's an error in sensor configuration."""
    
    def __init__(self, parameter: str, value: Any, valid_range: Optional[str] = None):
        message = f"Invalid configuration for {parameter}: {value}"
        if valid_range:
            message += f". Valid range: {valid_range}"
        super().__init__(message, error_code=1002)
        self.parameter = parameter
        self.value = value
        self.valid_range = valid_range


class PowerManagementError(PM25SensorError):
    """Raised when power management operations fail."""
    
    def __init__(self, operation: str, message: str):
        full_message = f"Power management error during {operation}: {message}"
        super().__init__(full_message, error_code=1003)
        self.operation = operation


class SensorBusyError(PM25SensorError):
    """Raised when sensor is busy and cannot accept new commands."""
    
    def __init__(self, operation: str):
        message = f"Sensor busy, cannot perform {operation}"
        super().__init__(message, error_code=1004)
        self.operation = operation


class CalibrationError(PM25SensorError):
    """Raised when sensor calibration fails or readings are out of expected range."""
    
    def __init__(self, parameter: str, value: float, expected_range: tuple):
        message = f"Calibration error: {parameter} value {value} outside expected range {expected_range}"
        super().__init__(message, error_code=1005)
        self.parameter = parameter
        self.value = value
        self.expected_range = expected_range


class TimeoutError(PM25SensorError):
    """Raised when operations timeout."""
    
    def __init__(self, operation: str, timeout: float):
        message = f"Operation {operation} timed out after {timeout}s"
        super().__init__(message, error_code=1006)
        self.operation = operation
        self.timeout = timeout


# Exception hierarchy for easier catching
PM25_EXCEPTIONS = (
    PM25SensorError,
    CommunicationError,
    SensorNotRespondingError,
    InvalidRegisterError,
    InvalidDataError,
    SensorNotInitializedError,
    ConfigurationError,
    PowerManagementError,
    SensorBusyError,
    CalibrationError,
    TimeoutError
)


def handle_sensor_exception(func):
    """Decorator to automatically handle and log sensor exceptions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PM25SensorError:
            # Re-raise PM25 exceptions as-is
            raise
        except Exception as e:
            # Convert other exceptions to PM25SensorError
            raise PM25SensorError(f"Unexpected error in {func.__name__}: {str(e)}") from e
    
    return wrapper
