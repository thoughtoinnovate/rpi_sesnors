"""
PM25 Sensor Configuration Management

This module provides configuration management for the PM25 sensor API,
including default settings, validation, and file-based configuration loading.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

from .constants import (
    DEFAULT_I2C_BUS, DEFAULT_I2C_ADDRESS, WARMUP_TIME_SECONDS,
    MIN_READ_INTERVAL, MAX_PM_CONCENTRATION, MAX_PARTICLE_COUNT
)
from .exceptions import ConfigurationError


class PM25Config:
    """Configuration class for PM25 sensor settings."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration with optional dictionary."""
        self._config = self._get_default_config()
        
        if config_dict:
            self._update_config(config_dict)
            self._validate_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "i2c": {
                "bus": DEFAULT_I2C_BUS,
                "address": DEFAULT_I2C_ADDRESS,
                "timeout": 1.0,
                "max_retries": 3,
                "retry_delay": 0.1
            },
            "sensor": {
                "warmup_time": WARMUP_TIME_SECONDS,
                "read_interval": MIN_READ_INTERVAL,
                "auto_warmup": True,
                "max_pm_concentration": MAX_PM_CONCENTRATION,
                "max_particle_count": MAX_PARTICLE_COUNT,
                "enable_validation": True
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": None,
                "console": True
            },
            "performance": {
                "enable_caching": False,
                "cache_timeout": 0.5,
                "async_operations": False
            },
            "debug": {
                "enable_debug_output": False,
                "log_raw_data": False,
                "log_timing": False
            }
        }
    
    def _update_config(self, config_dict: Dict[str, Any]):
        """Update configuration with provided dictionary."""
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self._config, config_dict)
    
    def _validate_config(self):
        """Validate configuration values."""
        # I2C configuration validation
        i2c_config = self._config.get("i2c", {})
        
        bus = i2c_config.get("bus")
        if not isinstance(bus, int) or bus < 0 or bus > 3:
            raise ConfigurationError("i2c.bus", bus, "0, 1, 2, or 3")
        
        address = i2c_config.get("address")
        if not isinstance(address, int) or address < 0x08 or address > 0x77:
            raise ConfigurationError("i2c.address", address, "0x08 to 0x77")
        
        timeout = i2c_config.get("timeout")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ConfigurationError("i2c.timeout", timeout, "positive number")
        
        max_retries = i2c_config.get("max_retries")
        if not isinstance(max_retries, int) or max_retries < 0:
            raise ConfigurationError("i2c.max_retries", max_retries, "non-negative integer")
        
        # Sensor configuration validation
        sensor_config = self._config.get("sensor", {})
        
        warmup_time = sensor_config.get("warmup_time")
        if not isinstance(warmup_time, (int, float)) or warmup_time < 0:
            raise ConfigurationError("sensor.warmup_time", warmup_time, "non-negative number")
        
        read_interval = sensor_config.get("read_interval")
        if not isinstance(read_interval, (int, float)) or read_interval <= 0:
            raise ConfigurationError("sensor.read_interval", read_interval, "positive number")
        
        max_pm_concentration = sensor_config.get("max_pm_concentration")
        if not isinstance(max_pm_concentration, (int, float)) or max_pm_concentration < 0:
            raise ConfigurationError("sensor.max_pm_concentration", max_pm_concentration, "non-negative number")
        
        enable_validation = sensor_config.get("enable_validation")
        if not isinstance(enable_validation, bool):
            raise ConfigurationError("sensor.enable_validation", enable_validation, "boolean value")
        
        # Logging configuration validation
        logging_config = self._config.get("logging", {})
        level = logging_config.get("level", "INFO")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level not in valid_levels:
            raise ConfigurationError("logging.level", level, f"one of {valid_levels}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'i2c.address')."""
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self._validate_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()
    
    def copy(self) -> 'PM25Config':
        """Create a copy of this configuration."""
        return PM25Config(self.to_dict())
    
    def save_to_file(self, file_path: Union[str, Path]):
        """Save configuration to JSON file."""
        file_path = Path(file_path)
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            raise ConfigurationError("file_save", str(e), "valid file path and permissions")
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> 'PM25Config':
        """Load configuration from JSON file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
            return cls(config_dict)
        except json.JSONDecodeError as e:
            raise e  # Re-raise the original JSONDecodeError as expected by tests
        except Exception as e:
            raise ConfigurationError("file_read", str(e), "readable file")


def load_config(config_path: Optional[Union[str, Path]] = None) -> PM25Config:
    """
    Load configuration from file or return default configuration.
    
    Args:
        config_path: Path to configuration file. If None, returns default config.
    
    Returns:
        PM25Config instance
    """
    if config_path:
        return PM25Config.load_from_file(config_path)
    
    # Try to load from environment variable
    env_config = os.getenv("PM25_CONFIG_FILE")
    if env_config and os.path.exists(env_config):
        return PM25Config.load_from_file(env_config)
    
    # Try to load from default locations
    default_locations = [
        Path.cwd() / "pm25_config.json",
        Path.home() / ".pm25" / "config.json",
        Path("/etc/pm25/config.json")
    ]
    
    for location in default_locations:
        if location.exists():
            return PM25Config.load_from_file(location)
    
    # Return default configuration
    return PM25Config()


def setup_logging(config: PM25Config) -> logging.Logger:
    """
    Setup logging based on configuration.
    
    Args:
        config: PM25Config instance
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("pm25_sensor")
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set log level
    level_name = config.get("logging.level", "INFO")
    logger.setLevel(getattr(logging, level_name))
    
    # Create formatter
    format_str = config.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    formatter = logging.Formatter(format_str)
    
    # Console handler
    if config.get("logging.console", True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    log_file = config.get("logging.file")
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Global configuration instance
_global_config: Optional[PM25Config] = None


def get_global_config() -> PM25Config:
    """Get global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config


def set_global_config(config: PM25Config):
    """Set global configuration instance."""
    global _global_config
    _global_config = config
