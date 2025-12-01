"""Helpers for computing AQI values from raw PM readings."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Mapping, TypedDict

AQIMethod = Literal["us_epa", "purpleair"]


@dataclass(frozen=True)
class AQIBreakpoint:
    """Represents a single AQI breakpoint segment."""

    c_low: float
    c_high: float
    aqi_low: int
    aqi_high: int


PM25_US_EPA_BREAKPOINTS: tuple[AQIBreakpoint, ...] = (
    AQIBreakpoint(0.0, 12.0, 0, 50),
    AQIBreakpoint(12.1, 35.4, 51, 100),
    AQIBreakpoint(35.5, 55.4, 101, 150),
    AQIBreakpoint(55.5, 150.4, 151, 200),
    AQIBreakpoint(150.5, 250.4, 201, 300),
    AQIBreakpoint(250.5, 350.4, 301, 400),
    AQIBreakpoint(350.5, 500.4, 401, 500),
)

PM10_US_EPA_BREAKPOINTS: tuple[AQIBreakpoint, ...] = (
    AQIBreakpoint(0.0, 54.0, 0, 50),
    AQIBreakpoint(55.0, 154.0, 51, 100),
    AQIBreakpoint(155.0, 254.0, 101, 150),
    AQIBreakpoint(255.0, 354.0, 151, 200),
    AQIBreakpoint(355.0, 424.0, 201, 300),
    AQIBreakpoint(425.0, 504.0, 301, 400),
    AQIBreakpoint(505.0, 604.0, 401, 500),
)


class AQIResult(TypedDict, total=False):
    """Typed dict describing AQI computation output."""

    aqi: int | None
    dominant: Literal["pm2_5", "pm10"] | None
    pm25_aqi: int | None
    pm10_aqi: int | None
    method: AQIMethod


def _interpolate(concentration: float | None, table: Iterable[AQIBreakpoint]) -> int | None:
    """Map a concentration to the AQI scale using the provided breakpoints."""
    if concentration is None:
        return None
    clamped = max(0.0, concentration)
    table_list = tuple(table)
    chosen = None
    for breakpoint in table_list:
        if clamped <= breakpoint.c_high:
            chosen = breakpoint
            break
    if chosen is None:
        chosen = table_list[-1]
    return round(
        (chosen.aqi_high - chosen.aqi_low) / (chosen.c_high - chosen.c_low) * (clamped - chosen.c_low)
        + chosen.aqi_low
    )


def _purpleair_adjustment(pm25: float | None) -> float | None:
    """Apply the US EPA/PurpleAir correction to CF=1 PM2.5 readings.

    The correction equation (0.52 * PM + 5.71) is based on the US EPA
    guidance for PurpleAir PA-II devices using CF=1 data, assuming no
    humidity compensation is available.
    """
    if pm25 is None:
        return None
    return max(0.0, (0.52 * pm25) + 5.71)


def compute_aqi(reading: Mapping[str, float | None], method: AQIMethod = "us_epa") -> AQIResult:
    """Compute AQI using PM2.5/PM10 inputs and the requested method."""
    pm25 = reading.get("pm2_5")
    pm10 = reading.get("pm10")
    if method == "purpleair":
        pm25 = _purpleair_adjustment(pm25)
    pm25_aqi = _interpolate(pm25, PM25_US_EPA_BREAKPOINTS)
    pm10_aqi = _interpolate(pm10, PM10_US_EPA_BREAKPOINTS)
    overall = None
    dominant: Literal["pm2_5", "pm10"] | None = None
    candidates = [val for val in (pm25_aqi, pm10_aqi) if val is not None]
    if candidates:
        overall = max(candidates)
        if pm25_aqi == overall:
            dominant = "pm2_5"
        elif pm10_aqi == overall:
            dominant = "pm10"
    return AQIResult(
        aqi=overall,
        dominant=dominant,
        pm25_aqi=pm25_aqi,
        pm10_aqi=pm10_aqi,
        method=method,
    )


__all__ = ["compute_aqi", "AQIMethod", "AQIResult"]
