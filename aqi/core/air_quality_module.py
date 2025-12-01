"""Self-contained helpers for the DFRobot air quality sensor.

Configuration lives in `config/aqi.toml` (with a legacy fallback next to this
module), so downstream scripts can change buses or I2C addresses without
touching code.  The helper functions embed the low-level I2C driver, so this
module does not depend on the original DFRobot Python package.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for older interpreters
    import tomli as tomllib  # type: ignore[assignment]

import smbus

DEFAULT_BUS = 0x01
DEFAULT_I2C_ADDRESS = 0x19
DEFAULT_RETRIES = 1
DEFAULT_RETRY_DELAY_MS = 1000
CONFIG_ENV_VAR = "AQI_CONFIG_FILE"
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "aqi.toml"
LEGACY_CONFIG_PATH = Path(__file__).with_name("air_quality_config.toml")


class AirQualitySensor:
    """Minimal I2C driver for the SEN0460 PM sensor."""

    # Select PM type
    PARTICLE_PM1_0_STANDARD = 0x05
    PARTICLE_PM2_5_STANDARD = 0x07
    PARTICLE_PM10_STANDARD = 0x09
    PARTICLE_PM1_0_ATMOSPHERE = 0x0B
    PARTICLE_PM2_5_ATMOSPHERE = 0x0D
    PARTICLE_PM10_ATMOSPHERE = 0x0F
    PARTICLENUM_0_3_UM_EVERY0_1L_AIR = 0x11
    PARTICLENUM_0_5_UM_EVERY0_1L_AIR = 0x13
    PARTICLENUM_1_0_UM_EVERY0_1L_AIR = 0x15
    PARTICLENUM_2_5_UM_EVERY0_1L_AIR = 0x17
    PARTICLENUM_5_0_UM_EVERY0_1L_AIR = 0x19
    PARTICLENUM_10_UM_EVERY0_1L_AIR = 0x1B
    PARTICLENUM_GAIN_VERSION = 0x1D

    def __init__(self, bus: int, addr: int, retries: int = DEFAULT_RETRIES, retry_delay_s: float = DEFAULT_RETRY_DELAY_MS / 1000.0) -> None:
        self._addr = addr
        self._bus = smbus.SMBus(bus)
        self._retries = max(1, int(retries))
        self._retry_delay = max(0.0, float(retry_delay_s))

    def gain_particle_concentration_ugm3(self, pm_type: int) -> int:
        """Return particulate mass concentration for the given register."""
        buf = self.read_reg(pm_type, 2)
        return (buf[0] << 8) + buf[1]

    def gain_particlenum_every0_1l(self, pm_type: int) -> int:
        """Return particle counts for a 0.1 L sample window."""
        buf = self.read_reg(pm_type, 2)
        return (buf[0] << 8) + buf[1]

    def gain_version(self) -> int:
        """Return the firmware version byte."""
        version = self.read_reg(self.PARTICLENUM_GAIN_VERSION, 1)
        return version[0]

    def set_lowpower(self) -> None:
        """Put the sensor into low-power mode."""
        self.write_reg(0x01, [0x01])

    def awake(self) -> None:
        """Wake the sensor from low-power mode."""
        self.write_reg(0x01, [0x02])

    def write_reg(self, reg: int, data: list[int]) -> None:
        """Best-effort register write."""
        for attempt in range(self._retries):
            try:
                self._bus.write_i2c_block_data(self._addr, reg, data)
                return
            except OSError:
                print("please check connect!")
                if attempt < self._retries - 1 and self._retry_delay > 0:
                    time.sleep(self._retry_delay)

    def read_reg(self, reg: int, length: int) -> list[int]:
        """Read bytes from the given register."""
        for attempt in range(self._retries):
            try:
                return self._bus.read_i2c_block_data(self._addr, reg, length)
            except OSError:
                print("please check connect!")
                if attempt < self._retries - 1 and self._retry_delay > 0:
                    time.sleep(self._retry_delay)
        return [-1] * length


def _candidate_config_paths() -> list[Path]:
    """Return config paths in search order."""
    candidates: list[Path] = []
    env_value = os.environ.get(CONFIG_ENV_VAR)
    if env_value:
        candidates.append(Path(env_value).expanduser())
    candidates.append(CONFIG_PATH)
    if LEGACY_CONFIG_PATH != CONFIG_PATH:
        candidates.append(LEGACY_CONFIG_PATH)
    return candidates


def _load_sensor_config() -> Dict[str, int]:
    """Load bus and address settings from the TOML file."""
    config = {
        "bus": DEFAULT_BUS,
        "i2c_address": DEFAULT_I2C_ADDRESS,
        "retries": DEFAULT_RETRIES,
        "retry_delay_ms": DEFAULT_RETRY_DELAY_MS,
    }
    for candidate in _candidate_config_paths():
        if candidate.exists():
            with candidate.open("rb") as cfg_file:
                data = tomllib.load(cfg_file)
            sensor_cfg = data.get("sensor", {})
            config["bus"] = int(sensor_cfg.get("bus", config["bus"]))
            config["i2c_address"] = int(sensor_cfg.get("i2c_address", config["i2c_address"]))
            config["retries"] = int(sensor_cfg.get("retries", config["retries"]))
            config["retry_delay_ms"] = int(sensor_cfg.get("retry_delay_ms", config["retry_delay_ms"]))
            break
    return config


_SENSOR_CONFIG = _load_sensor_config()


def load_config() -> Dict[str, Dict[str, int]]:
    """Return a deep copy of the resolved configuration."""
    return {"sensor": dict(_SENSOR_CONFIG)}


def create_sensor(
    bus: int | None = None,
    address: int | None = None,
    retries: int | None = None,
    retry_delay_ms: int | None = None,
) -> AirQualitySensor:
    """Instantiate and return the embedded sensor driver."""
    resolved_bus = _SENSOR_CONFIG["bus"] if bus is None else bus
    resolved_address = _SENSOR_CONFIG["i2c_address"] if address is None else address
    resolved_retries = _SENSOR_CONFIG["retries"] if retries is None else retries
    resolved_retry_delay_ms = _SENSOR_CONFIG["retry_delay_ms"] if retry_delay_ms is None else retry_delay_ms
    return AirQualitySensor(
        resolved_bus,
        resolved_address,
        retries=max(1, int(resolved_retries)),
        retry_delay_s=max(0.0, float(resolved_retry_delay_ms) / 1000.0),
    )


def get_firmware_version(sensor: AirQualitySensor) -> int:
    """Return the single-byte firmware version."""
    return sensor.gain_version()


def sensor_status(sensor: AirQualitySensor) -> Dict[str, Any]:
    """Return a health snapshot for the sensor."""
    status: Dict[str, Any] = {"config": load_config()["sensor"]}
    try:
        status["firmware_version"] = get_firmware_version(sensor)
        status["online"] = True
    except Exception as exc:  # pragma: no cover - defensive path
        status["online"] = False
        status["error"] = str(exc)
    return status


def read_standard_pm(sensor: AirQualitySensor) -> Dict[str, int]:
    """Read the CF=1 (standard) particulate mass concentrations."""
    return {
        "pm1_0": sensor.gain_particle_concentration_ugm3(sensor.PARTICLE_PM1_0_STANDARD),
        "pm2_5": sensor.gain_particle_concentration_ugm3(sensor.PARTICLE_PM2_5_STANDARD),
        "pm10": sensor.gain_particle_concentration_ugm3(sensor.PARTICLE_PM10_STANDARD),
    }


def read_atmospheric_pm(sensor: AirQualitySensor) -> Dict[str, int]:
    """Read the atmospheric particulate mass concentrations."""
    return {
        "pm1_0": sensor.gain_particle_concentration_ugm3(sensor.PARTICLE_PM1_0_ATMOSPHERE),
        "pm2_5": sensor.gain_particle_concentration_ugm3(sensor.PARTICLE_PM2_5_ATMOSPHERE),
        "pm10": sensor.gain_particle_concentration_ugm3(sensor.PARTICLE_PM10_ATMOSPHERE),
    }


def read_particle_counts(sensor: AirQualitySensor) -> Dict[str, int]:
    """Return particle counts for each size bin (0.3–10 µm per 0.1 L of air)."""
    return {
        "particles_0_3um": sensor.gain_particlenum_every0_1l(sensor.PARTICLENUM_0_3_UM_EVERY0_1L_AIR),
        "particles_0_5um": sensor.gain_particlenum_every0_1l(sensor.PARTICLENUM_0_5_UM_EVERY0_1L_AIR),
        "particles_1_0um": sensor.gain_particlenum_every0_1l(sensor.PARTICLENUM_1_0_UM_EVERY0_1L_AIR),
        "particles_2_5um": sensor.gain_particlenum_every0_1l(sensor.PARTICLENUM_2_5_UM_EVERY0_1L_AIR),
        "particles_5_0um": sensor.gain_particlenum_every0_1l(sensor.PARTICLENUM_5_0_UM_EVERY0_1L_AIR),
        "particles_10um": sensor.gain_particlenum_every0_1l(sensor.PARTICLENUM_10_UM_EVERY0_1L_AIR),
    }


def enter_low_power(sensor: AirQualitySensor) -> None:
    """Put the sensor into its documented low-power mode."""
    sensor.set_lowpower()


def wake_up(sensor: AirQualitySensor) -> None:
    """Bring the sensor out of low-power mode."""
    sensor.awake()


def snapshot(sensor: AirQualitySensor) -> Dict[str, Dict[str, int]]:
    """Collect every exposed measurement in a single dictionary payload."""
    return {
        "firmware": {"version": get_firmware_version(sensor)},
        "pm_standard": read_standard_pm(sensor),
        "pm_atmosphere": read_atmospheric_pm(sensor),
        "particle_counts": read_particle_counts(sensor),
    }


__all__ = [
    "DEFAULT_BUS",
    "DEFAULT_I2C_ADDRESS",
    "CONFIG_PATH",
    "AirQualitySensor",
    "create_sensor",
    "get_firmware_version",
    "sensor_status",
    "read_standard_pm",
    "read_atmospheric_pm",
    "read_particle_counts",
    "enter_low_power",
    "wake_up",
    "snapshot",
    "load_config",
]
