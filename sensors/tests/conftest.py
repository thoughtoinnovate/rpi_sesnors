"""
Pytest Configuration and Shared Fixtures for PM25 Sensor Tests

This module provides shared test fixtures and configuration for all PM25 sensor tests.
All tests use real hardware - no mocks allowed.
"""

import pytest
import sys
import time
import logging
from pathlib import Path
from typing import Generator, Optional, Dict, Any

# Add our independent API
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))
from apis import PM25Sensor, PM25Config, load_config

# Test configuration
DEFAULT_I2C_BUS = 1
DEFAULT_I2C_ADDRESS = 0x19
SENSOR_WARMUP_TIME = 5  # seconds
TEST_TIMEOUT = 30  # seconds per test


@pytest.fixture(scope="session")
def test_config() -> PM25Config:
    """
    Fixture providing test configuration for PM25 sensor.
    
    Returns:
        PM25Config instance configured for testing
    """
    config_dict = {
        "i2c": {
            "bus": DEFAULT_I2C_BUS,
            "address": DEFAULT_I2C_ADDRESS,
            "timeout": 5.0,
            "max_retries": 3,
            "retry_delay": 0.5
        },
        "sensor": {
            "warmup_time": SENSOR_WARMUP_TIME,
            "enable_validation": True,
            "max_pm_concentration": 999,
            "max_particle_count": 65535,
            "max_history_size": 100
        },
        "performance": {
            "cache_timeout": 0.1  # Short cache for testing
        },
        "debug": {
            "log_raw_data": False,
            "log_timing": True
        },
        "logging": {
            "level": "DEBUG"
        }
    }
    
    return PM25Config(config_dict)


@pytest.fixture(scope="session")
def sensor(test_config: PM25Config) -> Generator[PM25Sensor, None, None]:
    """
    Fixture providing real PM25 sensor instance for all tests.
    
    Args:
        test_config: Test configuration fixture
        
    Yields:
        Initialized PM25Sensor instance
        
    Raises:
        pytest.skip: If sensor is not available
    """
    sensor_instance = None
    try:
        # Create sensor instance
        sensor_instance = PM25Sensor(config=test_config, auto_connect=False)
        
        # Try to connect to real sensor
        if not sensor_instance.initialize():
            pytest.skip("PM25 sensor not connected or not responding")
        
        # Wait for sensor warmup
        time.sleep(SENSOR_WARMUP_TIME)
        
        yield sensor_instance
        
    except Exception as e:
        pytest.skip(f"Failed to initialize PM25 sensor: {e}")
    finally:
        if sensor_instance:
            try:
                sensor_instance.disconnect()
            except Exception:
                pass  # Ignore cleanup errors


# DFRobot comparison fixtures removed - API is now independent


@pytest.fixture
def reading_data() -> Dict[str, Any]:
    """
    Fixture providing test data for reading validation.
    
    Returns:
        Dictionary with expected data ranges and validation parameters
    """
    return {
        "pm_concentration": {
            "min": 0,
            "max": 999,
            "typical_range": (0, 500)
        },
        "particle_count": {
            "min": 0,
            "max": 65535,
            "typical_range": (0, 10000)
        },
        "tolerance": {
            "concentration": 0,  # Must be identical
            "particle_count": 0   # Must be identical
        },
        "timing": {
            "max_read_time": 1.0,  # seconds
            "stabilization_time": 2.0  # seconds
        }
    }


@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for all tests."""
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise during tests
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@pytest.fixture
def performance_tracker():
    """
    Fixture for tracking performance during tests.
    
    Returns:
        Dictionary to store performance metrics
    """
    return {
        "read_times": [],
        "error_counts": {},
        "total_reads": 0,
        "start_time": None,
        "end_time": None
    }


def pytest_configure(config):
    """Pytest configuration hook."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "hardware: marks tests as requiring real hardware"
    )
    config.addinivalue_line(
        "markers", "comparison: marks tests as comparison tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance benchmarks"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add hardware marker to all tests in this module
        item.add_marker(pytest.mark.hardware)
        
        # Add comparison marker to tests that use comparison fixtures
        if "sensor_comparison" in item.fixturenames:
            item.add_marker(pytest.mark.comparison)
        
        # Add performance marker to performance tests
        if "performance" in item.name or "benchmark" in item.name:
            item.add_marker(pytest.mark.performance)
        
        # Add integration marker to integration tests
        if "integration" in item.name or "end_to_end" in item.name:
            item.add_marker(pytest.mark.integration)


# Utility functions for tests
def validate_reading_range(value: int, min_val: int, max_val: int, param_name: str) -> bool:
    """
    Validate that a reading is within expected range.
    
    Args:
        value: Reading value to validate
        min_val: Minimum expected value
        max_val: Maximum expected value
        param_name: Name of parameter for error messages
        
    Returns:
        True if valid
        
    Raises:
        AssertionError: If value is out of range
    """
    assert min_val <= value <= max_val, f"{param_name} value {value} outside range [{min_val}, {max_val}]"
    return True


def compare_readings(api1_value: int, api2_value: int, tolerance: int = 0, param_name: str = "reading") -> bool:
    """
    Compare two readings within tolerance.
    
    Args:
        api1_value: Value from first API
        api2_value: Value from second API
        tolerance: Allowed difference between values
        param_name: Name of parameter for error messages
        
    Returns:
        True if values match within tolerance
        
    Raises:
        AssertionError: If values differ by more than tolerance
    """
    diff = abs(api1_value - api2_value)
    assert diff <= tolerance, f"{param_name} mismatch: API1={api1_value}, API2={api2_value}, diff={diff}, tolerance={tolerance}"
    return True


def log_sensor_data(timestamp: float, api_reading: Dict[str, Any]):
    """
    Log sensor data for analysis.

    Args:
        timestamp: Reading timestamp
        api_reading: Reading from our API
    """
    log_entry = {
        "timestamp": timestamp,
        "our_api": api_reading
    }

    # In a real implementation, this could log to file or database
    # For now, just print debug info
    print(f"SENSOR_DATA: {log_entry}")


def wait_for_sensor_stabilization(sensor: PM25Sensor, wait_time: float = 2.0):
    """
    Wait for sensor readings to stabilize.
    
    Args:
        sensor: PM25 sensor instance
        wait_time: Time to wait for stabilization
    """
    time.sleep(wait_time)


def measure_read_time(func, *args, **kwargs) -> tuple:
    """
    Measure execution time of a function.
    
    Args:
        func: Function to measure
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Tuple of (result, execution_time_seconds)
    """
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    except Exception as e:
        end_time = time.time()
        raise e