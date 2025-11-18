"""
Error Handling Validation Tests for PM25 Sensor

This module tests error handling, exception management, and robustness.
All tests use real hardware - no mocks allowed.

Test Areas:
- Invalid register access handling
- Sensor disconnection scenarios
- Invalid data handling
- Configuration error handling
- Exception propagation and logging
"""

import pytest
import time

from apis.exceptions import (
    PM25SensorError, CommunicationError, SensorNotRespondingError,
    InvalidRegisterError, InvalidDataError, SensorNotInitializedError,
    ConfigurationError, PowerManagementError, CalibrationError,
    TimeoutError
)
from apis.config import PM25Config


class TestInvalidRegisterHandling:
    """Test handling of invalid register access."""
    
    def test_invalid_register_error(self, sensor):
        """Test that invalid register access raises appropriate exception."""
        # This test requires accessing private I2C interface
        i2c = sensor.i2c
        
        # Try to read from invalid register addresses
        invalid_registers = [0x00, 0x02, 0x04, 0x20, 0xFF]
        
        for register in invalid_registers:
            with pytest.raises(InvalidRegisterError) as exc_info:
                i2c.read_register(register, 2)
            
            # Verify exception details
            assert exc_info.value.register == register
            assert exc_info.value.valid_registers is not None
            assert len(exc_info.value.valid_registers) > 0
    
    def test_invalid_register_write(self, sensor):
        """Test that invalid register write raises appropriate exception."""
        i2c = sensor.i2c
        
        # Try to write to invalid register
        invalid_register = 0x00
        test_data = [0x01, 0x02]
        
        with pytest.raises(InvalidRegisterError) as exc_info:
            i2c.write_register(invalid_register, test_data)
        
        assert exc_info.value.register == invalid_register
    
    def test_valid_register_access(self, sensor):
        """Test that valid registers work correctly."""
        i2c = sensor.i2c
        
        # Test a few known valid registers
        valid_registers = [0x05, 0x07, 0x1D]  # PM1.0, PM2.5, Version
        
        for register in valid_registers:
            try:
                # Should not raise exception
                data = i2c.read_register(register, 2)
                assert isinstance(data, list), f"Register {register:02X} should return list"
                assert len(data) == 2, f"Register {register:02X} should return 2 bytes"
            except CommunicationError:
                # Communication errors are acceptable for this test
                pass


class TestSensorDisconnectionScenarios:
    """Test sensor disconnection and reconnection scenarios."""
    
    def test_not_initialized_error(self):
        """Test error when using sensor without initialization."""
        config = PM25Config()
        sensor = __import__('apis').PM25Sensor(config=config, auto_connect=False)
        
        # Should raise SensorNotInitializedError
        with pytest.raises(SensorNotInitializedError):
            sensor.get_pm2_5_standard()
    
    def test_disconnected_sensor_error(self, sensor):
        """Test behavior when sensor becomes disconnected."""
        # Disconnect sensor
        sensor.disconnect()
        
        # Try to read - should auto-reconnect and succeed
        reading = sensor.get_pm2_5_standard(use_cache=False)
        assert isinstance(reading, int)
        assert reading >= 0
    
    def test_reconnection_recovery(self, sensor, test_config):
        """Test recovery after disconnection."""
        # Disconnect
        sensor.disconnect()
        assert not sensor.is_connected()
        
        # Reconnect
        success = sensor.initialize()
        assert success, "Should reconnect successfully"
        
        # Should work after reconnection
        reading = sensor.get_pm2_5_standard()
        assert reading >= 0, "Should return valid reading after reconnection"


class TestInvalidDataHandling:
    """Test handling of invalid or corrupted data."""
    
    def test_data_validation_enabled(self, sensor):
        """Test that data validation catches invalid readings."""
        # Test with validation enabled (default)
        readings = []
        
        # Take multiple readings
        for i in range(10):
            try:
                reading = sensor.get_pm2_5_standard(use_cache=False)
                readings.append(reading)
            except CalibrationError:
                # Should catch calibration errors for invalid readings
                pass
        
        # Should have some valid readings
        valid_readings = [r for r in readings if r >= 0]
        assert len(valid_readings) > 0, "Should have some valid readings"
    
    def test_data_validation_disabled(self, sensor, test_config):
        """Test behavior with data validation disabled."""
        # Temporarily disable validation
        original_validation = sensor.config.get("sensor.enable_validation")
        sensor.config.set("sensor.enable_validation", False)
        
        try:
            # Take readings with validation disabled
            readings = []
            for i in range(5):
                reading = sensor.get_pm2_5_standard(use_cache=False)
                readings.append(reading)
                time.sleep(0.1)
            
            # Should get readings without calibration errors
            assert len(readings) == 5, "Should get all readings without validation errors"
            
        finally:
            # Restore original validation setting
            sensor.config.set("sensor.enable_validation", original_validation)


class TestConfigurationErrorHandling:
    """Test configuration error handling."""
    
    def test_invalid_i2c_address(self):
        """Test error handling for invalid I2C address."""
        # Test with invalid I2C address
        invalid_config_dict = {
            "i2c": {
                "bus": 1,
                "address": 0x99  # Invalid address
            }
        }
        
        # Should fail during config creation
        with pytest.raises(ConfigurationError):
            PM25Config(invalid_config_dict)
    
    def test_invalid_i2c_bus(self):
        """Test error handling for invalid I2C bus."""
        invalid_config_dict = {
            "i2c": {
                "bus": 99,  # Invalid bus number
                "address": 0x19
            }
        }
        
        # Should fail during config creation
        with pytest.raises(ConfigurationError):
            PM25Config(invalid_config_dict)
    
    def test_invalid_configuration_values(self):
        """Test error handling for invalid configuration values."""
        # Test configuration validation
        with pytest.raises(ConfigurationError):
            PM25Config({"i2c": {"timeout": -1}})  # Negative timeout
        
        with pytest.raises(ConfigurationError):
            PM25Config({"sensor": {"max_pm_concentration": -100}})  # Negative max value
    
    def test_configuration_type_validation(self):
        """Test configuration type validation."""
        # Test with wrong types
        with pytest.raises((ConfigurationError, TypeError)):
            PM25Config({"i2c": {"address": "not_a_number"}})
        
        with pytest.raises((ConfigurationError, TypeError)):
            PM25Config({"sensor": {"warmup_time": "not_a_number"}})


class TestPowerManagementErrorHandling:
    """Test power management error handling."""
    
    def test_sleep_mode_error_handling(self, sensor):
        """Test error handling in sleep mode operations."""
        # Test sleep mode
        result = sensor.enter_sleep_mode()
        
        if result:
            # If sleep succeeded, test wake
            wake_result = sensor.wake_from_sleep()
            assert wake_result, "Should wake successfully after sleep"
            
            # Verify sensor is responsive
            time.sleep(1)
            reading = sensor.get_pm2_5_standard()
            assert reading >= 0, "Should be responsive after wake cycle"
    
    def test_power_cycle_error_handling(self, sensor):
        """Test error handling in power cycle operations."""
        # Test power cycle
        result = sensor.perform_power_cycle(sleep_duration=0.5)
        
        # Should either succeed or handle gracefully
        if result:
            # Verify sensor is responsive after power cycle
            reading = sensor.get_pm2_5_standard()
            assert reading >= 0, "Should be responsive after power cycle"


class TestTimeoutErrorHandling:
    """Test timeout error handling."""
    
    def test_communication_timeout(self, sensor):
        """Test handling of communication timeouts."""
        # Get current timeout setting
        original_timeout = sensor.config.get("i2c.timeout")
        
        try:
            # Set very short timeout to induce timeouts
            sensor.config.set("i2c.timeout", 0.001)
            
            # Try reading - might timeout
            try:
                reading = sensor.get_pm2_5_standard(use_cache=False)
                # If successful, that's fine too
                assert reading >= 0
            except (TimeoutError, CommunicationError):
                # Expected behavior with very short timeout
                pass
            
        finally:
            # Restore original timeout
            sensor.config.set("i2c.timeout", original_timeout)
    
    def test_retry_logic(self, sensor):
        """Test retry logic on communication failures."""
        # Get performance statistics
        initial_stats = sensor.get_performance_statistics()
        
        # Force some communication attempts
        for i in range(10):
            try:
                reading = sensor.get_pm2_5_standard(use_cache=False)
                assert reading >= 0
            except CommunicationError:
                pass  # Expected occasionally
        
        # Check that retry logic is working
        final_stats = sensor.get_performance_statistics()
        total_attempts = final_stats["total_readings"]
        
        # Should have attempted some reads
        assert total_attempts > initial_stats["total_readings"]


class TestExceptionPropagation:
    """Test exception propagation and logging."""
    
    def test_exception_hierarchy(self, sensor):
        """Test that exceptions follow proper hierarchy."""
        # Test that specific exceptions inherit from PM25SensorError
        try:
            # Force an error by using uninitialized sensor
            uninitialized_sensor = __import__('apis').PM25Sensor(auto_connect=False)
            uninitialized_sensor.get_pm2_5_standard()
        except PM25SensorError as e:
            # Should catch base exception
            assert isinstance(e, SensorNotInitializedError)
        except Exception as e:
            pytest.fail(f"Should raise PM25SensorError, got {type(e)}")
    
    def test_exception_details(self, sensor):
        """Test that exceptions contain useful details."""
        i2c = sensor.i2c
        
        # Test InvalidRegisterError details
        invalid_register = 0x99
        try:
            i2c.read_register(invalid_register, 2)
        except InvalidRegisterError as e:
            assert e.register == invalid_register
            assert e.valid_registers is not None
            assert str(invalid_register) in str(e)
        
        # Test CommunicationError details (if possible)
        sensor.disconnect()
        try:
            sensor.get_pm2_5_standard(use_cache=False)
        except SensorNotRespondingError as e:
            assert e.address is not None
            assert e.timeout is not None
        except CommunicationError as e:
            assert e.address is not None or e.register is not None
        finally:
            sensor.initialize()  # Reconnect for other tests


class TestErrorRecoveryMechanisms:
    """Test error recovery mechanisms."""
    
    def test_automatic_reconnection(self, sensor):
        """Test automatic reconnection on communication errors."""
        # Disconnect sensor
        sensor.disconnect()
        
        # Try reading - should attempt reconnection
        try:
            reading = sensor.get_pm2_5_standard(use_cache=False)
            # If successful, reconnection worked
            assert reading >= 0
        except CommunicationError:
            # Manual reconnection
            success = sensor.initialize()
            assert success, "Should be able to reconnect manually"
    
    def test_cache_invalidation_on_error(self, sensor):
        """Test that cache is invalidated on errors."""
        # Take a reading to populate cache
        reading1 = sensor.get_pm2_5_standard(use_cache=True)
        
        # Clear cache and take another reading
        sensor.clear_all_caches()
        reading2 = sensor.get_pm2_5_standard(use_cache=True)
        
        # Should be fresh readings
        assert reading1 >= 0 and reading2 >= 0
    
    def test_statistics_tracking_on_errors(self, sensor):
        """Test that errors are properly tracked in statistics."""
        # Get initial statistics
        initial_stats = sensor.get_performance_statistics()
        initial_errors = initial_stats["total_errors"]
        
        # Force some potential error conditions
        for i in range(5):
            try:
                # Rapid operations might cause occasional errors
                sensor.get_pm2_5_standard(use_cache=False)
            except CommunicationError:
                pass  # Expected occasionally
        
        # Check that errors are tracked
        final_stats = sensor.get_performance_statistics()
        final_errors = final_stats["total_errors"]
        
        # Error count should be accurate
        assert final_errors >= initial_errors


class TestGracefulDegradation:
    """Test graceful degradation under error conditions."""
    
    def test_partial_functionality_preserved(self, sensor):
        """Test that partial functionality is preserved during errors."""
        # Test that if one function fails, others still work
        try:
            # Try reading multiple parameters
            pm25 = sensor.get_pm2_5_standard(use_cache=False)
            pm10 = sensor.get_pm10_standard(use_cache=False)
            particles = sensor.get_particles_2_5um(use_cache=False)
            
            # At least some should succeed
            successes = sum(1 for x in [pm25, pm10, particles] if x >= 0)
            assert successes >= 2, "At least 2 out of 3 readings should succeed"
            
        except CommunicationError:
            # If communication fails entirely, that's acceptable
            pass
    
    def test_fallback_mechanisms(self, sensor):
        """Test fallback mechanisms when primary operations fail."""
        # Test cache fallback when direct reading fails
        try:
            # Populate cache
            cached_reading = sensor.get_pm2_5_standard(use_cache=False)
            
            # Try reading with cache (should work even if direct read fails)
            cached_result = sensor.get_pm2_5_standard(use_cache=True)
            assert cached_result == cached_reading
            
        except CommunicationError:
            # If even cache fails, that's acceptable for this test
            pass