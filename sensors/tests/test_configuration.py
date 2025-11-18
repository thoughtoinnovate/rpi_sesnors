"""
Configuration Validation Tests for PM25 Sensor

This module tests configuration management, validation, and loading.
All tests use real hardware - no mocks allowed.

Test Areas:
- Configuration validation
- Default configuration
- Configuration loading from files
- Dynamic configuration changes
- Invalid configuration handling
"""

import pytest
import json
import tempfile
import time
from pathlib import Path

from apis.config import PM25Config, load_config
from apis.exceptions import ConfigurationError


class TestDefaultConfiguration:
    """Test default configuration values."""
    
    def test_default_config_creation(self):
        """Test creating default configuration."""
        config = PM25Config({})
        
        # Test default I2C settings
        assert config.get("i2c.bus") == 1
        assert config.get("i2c.address") == 0x19
        assert config.get("i2c.timeout") >= 1.0
        assert config.get("i2c.max_retries") >= 1
        
        # Test default sensor settings
        assert config.get("sensor.warmup_time") >= 1
        assert config.get("sensor.enable_validation") is True
        assert config.get("sensor.max_pm_concentration") > 0
        assert config.get("sensor.max_particle_count") > 0
        
        # Test default performance settings
        assert config.get("performance.cache_timeout") >= 0.1
        
        # Test default logging settings
        assert config.get("logging.level") in ["DEBUG", "INFO", "WARNING", "ERROR"]
    
    def test_config_get_set(self):
        """Test configuration get/set operations."""
        config = PM25Config({})
        
        # Test getting non-existent key
        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("nonexistent.key") is None
        
        # Test setting and getting
        config.set("test.key", "test_value")
        assert config.get("test.key") == "test_value"
        
        # Test nested keys
        config.set("nested.deep.key", 42)
        assert config.get("nested.deep.key") == 42
    
    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        config_dict = {
            "i2c": {"bus": 2, "address": 0x20},
            "sensor": {"warmup_time": 10}
        }
        config = PM25Config(config_dict)
        
        result = config.to_dict()
        assert isinstance(result, dict)
        assert result["i2c"]["bus"] == 2
        assert result["i2c"]["address"] == 0x20
        assert result["sensor"]["warmup_time"] == 10


class TestConfigurationValidation:
    """Test configuration validation."""
    
    def test_valid_i2c_config(self):
        """Test valid I2C configuration."""
        valid_config = {
            "i2c": {
                "bus": 1,
                "address": 0x19,
                "timeout": 5.0,
                "max_retries": 3,
                "retry_delay": 0.5
            }
        }
        
        # Should not raise exception
        config = PM25Config(valid_config)
        assert config.get("i2c.bus") == 1
        assert config.get("i2c.address") == 0x19
        assert config.get("i2c.timeout") == 5.0
        assert config.get("i2c.max_retries") == 3
        assert config.get("i2c.retry_delay") == 0.5
    
    def test_invalid_i2c_bus(self):
        """Test invalid I2C bus configuration."""
        invalid_configs = [
            {"i2c": {"bus": -1}},  # Negative bus
            {"i2c": {"bus": "not_a_number"}},  # String instead of number
            {"i2c": {"bus": 1000}},  # Too large bus number
        ]
        
        for invalid_config in invalid_configs:
            with pytest.raises((ConfigurationError, ValueError, TypeError)):
                PM25Config(invalid_config)
    
    def test_invalid_i2c_address(self):
        """Test invalid I2C address configuration."""
        invalid_configs = [
            {"i2c": {"address": -1}},  # Negative address
            {"i2c": {"address": 0x100}},  # Too large address
            {"i2c": {"address": "not_a_number"}},  # String instead of number
        ]
        
        for invalid_config in invalid_configs:
            with pytest.raises((ConfigurationError, ValueError, TypeError)):
                PM25Config(invalid_config)
    
    def test_invalid_timeout_values(self):
        """Test invalid timeout configuration."""
        invalid_configs = [
            {"i2c": {"timeout": -1}},  # Negative timeout
            {"i2c": {"timeout": 0}},  # Zero timeout
            {"i2c": {"timeout": "not_a_number"}},  # String instead of number
        ]
        
        for invalid_config in invalid_configs:
            with pytest.raises((ConfigurationError, ValueError, TypeError)):
                PM25Config(invalid_config)
    
    def test_invalid_sensor_config(self):
        """Test invalid sensor configuration."""
        invalid_configs = [
            {"sensor": {"warmup_time": -1}},  # Negative warmup
            {"sensor": {"max_pm_concentration": -100}},  # Negative max
            {"sensor": {"enable_validation": "not_boolean"}},  # Invalid boolean
        ]
        
        for invalid_config in invalid_configs:
            with pytest.raises((ConfigurationError, ValueError, TypeError)):
                PM25Config(invalid_config)
    
    def test_valid_sensor_config(self):
        """Test valid sensor configuration."""
        valid_config = {
            "sensor": {
                "warmup_time": 5,
                "enable_validation": True,
                "max_pm_concentration": 999,
                "max_particle_count": 65535,
                "max_history_size": 1000
            }
        }
        
        # Should not raise exception
        config = PM25Config(valid_config)
        assert config.get("sensor.warmup_time") == 5
        assert config.get("sensor.enable_validation") is True
        assert config.get("sensor.max_pm_concentration") == 999
        assert config.get("sensor.max_particle_count") == 65535
        assert config.get("sensor.max_history_size") == 1000


class TestConfigurationFileLoading:
    """Test loading configuration from files."""
    
    def test_load_from_json_file(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "i2c": {
                "bus": 1,
                "address": 25,
                "timeout": 3.0
            },
            "sensor": {
                "warmup_time": 10,
                "enable_validation": False
            }
        }
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_file = Path(f.name)
            json.dump(config_data, f)
        
        try:
            # Load configuration from file
            config = PM25Config.load_from_file(json_file)
            
            # Verify loaded values
            assert config.get("i2c.bus") == 1
            assert config.get("i2c.address") == 25
            assert config.get("i2c.timeout") == 3.0
            assert config.get("sensor.warmup_time") == 10
            assert config.get("sensor.enable_validation") is False
            
        finally:
            # Cleanup
            if json_file.exists():
                json_file.unlink()
    
    def test_load_nonexistent_file(self):
        """Test loading from non-existent file."""
        nonexistent_file = Path("/nonexistent/config.json")
        
        with pytest.raises(FileNotFoundError):
            PM25Config.load_from_file(nonexistent_file)
    
    def test_load_invalid_json(self):
        """Test loading from invalid JSON file."""
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            invalid_json_file = Path(f.name)
            f.write("{ invalid json content")
        
        try:
            with pytest.raises(json.JSONDecodeError):
                PM25Config.load_from_file(invalid_json_file)
        finally:
            if invalid_json_file.exists():
                invalid_json_file.unlink()
    
    def test_load_config_with_defaults(self):
        """Test loading configuration that uses defaults."""
        partial_config = {
            "i2c": {
                "address": 0x19
                # Missing bus, timeout, etc.
            }
        }
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_file = Path(f.name)
            json.dump(partial_config, f)
        
        try:
            config = PM25Config.load_from_file(json_file)
            
            # Should have loaded the specified value
            assert config.get("i2c.address") == 0x19
            
            # Should have defaults for missing values
            assert config.get("i2c.bus") is not None  # Should have default
            assert config.get("i2c.timeout") is not None  # Should have default
            
        finally:
            if json_file.exists():
                json_file.unlink()


class TestConfigurationIntegration:
    """Test configuration integration with sensor."""
    
    def test_config_with_sensor(self, test_config):
        """Test configuration with real sensor."""
        from apis import PM25Sensor
        
        # Create sensor with custom configuration
        custom_config = test_config.copy()
        custom_config.set("i2c.timeout", 2.0)
        custom_config.set("sensor.enable_validation", True)
        
        sensor = PM25Sensor(config=custom_config, auto_connect=True, auto_warmup=True)
        
        try:
            # Sensor should use custom configuration
            assert sensor.is_connected(), "Sensor should connect with custom config"
            
            # Test that configuration values are used
            # (This is indirect - we verify sensor works with the config)
            reading = sensor.get_pm2_5_standard()
            assert reading >= 0, "Sensor should return valid reading"
            
        finally:
            sensor.disconnect()
    
    def test_dynamic_config_changes(self, sensor):
        """Test dynamic configuration changes."""
        # Get initial cache timeout
        initial_timeout = sensor.config.get("performance.cache_timeout")
        
        # Change cache timeout
        new_timeout = 2.0
        sensor.config.set("performance.cache_timeout", new_timeout)
        
        # Verify change took effect
        assert sensor.config.get("performance.cache_timeout") == new_timeout
        
        # Test that new timeout is used
        reading1 = sensor.get_pm2_5_standard(use_cache=True)
        time.sleep(0.1)  # Less than new timeout
        reading2 = sensor.get_pm2_5_standard(use_cache=True)
        
        # Should be cached (same reading)
        assert reading1 == reading2, "Should use cached reading with new timeout"
        
        # Restore original timeout
        sensor.config.set("performance.cache_timeout", initial_timeout)


class TestConfigurationEdgeCases:
    """Test configuration edge cases."""
    
    def test_empty_configuration(self):
        """Test empty configuration."""
        config = PM25Config({})
        
        # Should have all default values
        assert config.get("i2c.bus") is not None
        assert config.get("i2c.address") is not None
        assert config.get("sensor.warmup_time") is not None
        assert config.get("performance.cache_timeout") is not None
    
    def test_nested_configuration_merge(self):
        """Test merging nested configurations."""
        base_config = {
            "i2c": {
                "bus": 1,
                "address": 0x19,
                "timeout": 5.0
            },
            "sensor": {
                "warmup_time": 5
            }
        }
        
        override_config = {
            "i2c": {
                "timeout": 10.0  # Override only timeout
            },
            "sensor": {
                "enable_validation": True  # Add new setting
            }
        }
        
        # Create config with base, then apply overrides
        config = PM25Config(base_config)
        config.set("i2c.timeout", override_config["i2c"]["timeout"])
        config.set("sensor.enable_validation", override_config["sensor"]["enable_validation"])
        
        # Should have merged values
        assert config.get("i2c.bus") == 1  # From base
        assert config.get("i2c.address") == 0x19  # From base
        assert config.get("i2c.timeout") == 10.0  # From override
        assert config.get("sensor.warmup_time") == 5  # From base
        assert config.get("sensor.enable_validation") is True  # From override
    
    def test_configuration_copy(self):
        """Test configuration copying."""
        original_config = PM25Config({
            "i2c": {"bus": 2, "address": 0x20},
            "sensor": {"warmup_time": 15}
        })
        
        # Copy configuration
        copied_config = PM25Config(original_config.to_dict())
        
        # Verify copy has same values
        assert copied_config.get("i2c.bus") == 2
        assert copied_config.get("i2c.address") == 0x20
        assert copied_config.get("sensor.warmup_time") == 15
        
        # Modify original
        original_config.set("i2c.bus", 3)
        
        # Copy should not be affected
        assert copied_config.get("i2c.bus") == 2
        assert original_config.get("i2c.bus") == 3


class TestLoadConfigFunction:
    """Test the load_config convenience function."""
    
    def test_load_config_default(self):
        """Test load_config with default behavior."""
        config = load_config()
        
        # Should return valid configuration
        assert isinstance(config, PM25Config)
        assert config.get("i2c.bus") is not None
        assert config.get("i2c.address") is not None
    
    def test_load_config_with_file(self):
        """Test load_config with specific file."""
        config_data = {
            "i2c": {"bus": 2, "address": 0x25},
            "sensor": {"warmup_time": 8}
        }
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = Path(f.name)
            json.dump(config_data, f)
        
        try:
            # Load specific config file
            config = load_config(str(config_file))
            
            assert config.get("i2c.bus") == 2
            assert config.get("i2c.address") == 0x25
            assert config.get("sensor.warmup_time") == 8
            
        finally:
            if config_file.exists():
                config_file.unlink()


class TestConfigurationPerformance:
    """Test configuration performance."""
    
    def test_config_access_performance(self, test_config):
        """Test that configuration access is performant."""
        import time
        
        # Test many accesses
        num_accesses = 1000
        start_time = time.time()
        
        for i in range(num_accesses):
            value = test_config.get("i2c.timeout")
            assert value is not None
        
        end_time = time.time()
        access_time = end_time - start_time
        
        # Should be fast (less than 0.1 seconds for 1000 accesses)
        assert access_time < 0.1, f"Config access too slow: {access_time:.3f}s for {num_accesses} accesses"
        
        avg_access_time = access_time / num_accesses
        assert avg_access_time < 0.0001, f"Average access time too slow: {avg_access_time:.6f}s"
    
    def test_config_update_performance(self, test_config):
        """Test that configuration updates are performant."""
        
        # Test many updates
        num_updates = 100
        start_time = time.time()
        
        for i in range(num_updates):
            test_config.set("test.value", i)
        
        end_time = time.time()
        update_time = end_time - start_time
        
        # Should be fast (less than 0.05 seconds for 100 updates)
        assert update_time < 0.05, f"Config update too slow: {update_time:.3f}s for {num_updates} updates"