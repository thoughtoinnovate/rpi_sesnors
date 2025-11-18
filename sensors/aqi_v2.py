"""
AQI v2 - Atmospheric Values Only

This module implements the AQI calculation algorithm using only atmospheric (ATM) values
from the PM25 sensor, following the exact specification provided.

Algorithm:
1. Use PM2.5 Atmospheric (pm.pm25_atm) as the primary value
2. Apply exact table-based breakpoints from specification
3. Optional PM10 comparison if it gives higher AQI
4. Ignore PM1.0 completely (not used in official AQI calculations)

This provides the same AQI values as AirNow, PurpleAir, IQAir, etc.
"""

import time
from typing import Dict, Any, Optional, Tuple, List
from .exceptions import InvalidDataError


# PM2.5 AQI Breakpoints (exact specification)
# Each tuple: (low_conc, high_conc, low_aqi, high_aqi, level, color)
PM25_BREAKPOINTS: List[Tuple[float, float, int, int, str, str]] = [
    (0.0, 9.0, 0, 50, "Good", "Green"),
    (9.1, 35.4, 51, 100, "Moderate", "Yellow"),
    (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups", "Orange"),
    (55.5, 125.4, 151, 200, "Unhealthy", "Red"),
    (125.5, 225.4, 201, 300, "Very Unhealthy", "Purple"),
    (225.5, 325.4, 301, 400, "Hazardous", "Maroon"),
    (325.5, float('inf'), 401, 500, "Hazardous", "Maroon")
]

# PM10 AQI Breakpoints (for comparison only)
# Each tuple: (low_conc, high_conc, low_aqi, high_aqi)
PM10_BREAKPOINTS: List[Tuple[float, float, int, int]] = [
    (0, 54, 0, 50),
    (55, 154, 51, 100),
    (155, 254, 101, 150),
    (255, 354, 151, 200),
    (355, 424, 201, 300),
    (425, float('inf'), 301, 500)
]

# Health messages for each AQI level
HEALTH_MESSAGES: Dict[str, str] = {
    "Good": "Air quality is satisfactory",
    "Moderate": "Air quality is acceptable for most people",
    "Unhealthy for Sensitive Groups": "Sensitive groups may experience health effects",
    "Unhealthy": "Everyone may experience health effects",
    "Very Unhealthy": "Health alert: everyone may experience serious health effects",
    "Hazardous": "Emergency conditions: everyone affected"
}


def validate_atmospheric_value(value: float, parameter_name: str = "concentration") -> float:
    """
    Validate atmospheric concentration value.
    
    Args:
        value: Concentration value to validate
        parameter_name: Name of parameter for error messages
        
    Returns:
        Validated concentration value as float
        
    Raises:
        InvalidDataError: If value is invalid
    """
    try:
        concentration = float(value)
    except (ValueError, TypeError):
        raise InvalidDataError(f"Invalid {parameter_name}: {value} (must be numeric)")
    
    if concentration < 0:
        raise InvalidDataError(f"Invalid {parameter_name}: {concentration} (must be non-negative)")
    
    if concentration > 1000:  # Reasonable upper limit for PM sensors
        raise InvalidDataError(f"Invalid {parameter_name}: {concentration} (too high, max 1000 μg/m³)")
    
    return concentration


def _calculate_pm25_aqi_v2(pm25_atm: float) -> Tuple[int, str, str]:
    """
    Calculate PM2.5 AQI using exact table-based breakpoints.
    
    Args:
        pm25_atm: PM2.5 atmospheric concentration (μg/m³)
        
    Returns:
        Tuple of (aqi_value, aqi_level, aqi_color)
        
    Raises:
        InvalidDataError: If value is out of range
    """
    pm25_atm = validate_atmospheric_value(pm25_atm, "PM2.5 atmospheric")
    
    for low, high, aqi_low, aqi_high, level, color in PM25_BREAKPOINTS:
        if low <= pm25_atm <= high:
            if high == float('inf'):  # Last breakpoint (325.5+)
                # Linear interpolation for last range
                aqi = int(((500.0 - 401.0) / (500.0 - 325.5)) * (pm25_atm - 325.5) + 401.0)
            else:
                # Linear interpolation within range
                aqi = int(((aqi_high - aqi_low) / (high - low)) * (pm25_atm - low) + aqi_low)
            
            return min(aqi, 500), level, color
    
    # This should never happen due to the last breakpoint having infinite high value
    raise InvalidDataError(f"PM2.5 value {pm25_atm} out of range")


def _calculate_pm10_aqi_v2(pm10_atm: float) -> int:
    """
    Calculate PM10 AQI for comparison only.
    
    Args:
        pm10_atm: PM10 atmospheric concentration (μg/m³)
        
    Returns:
        AQI value for PM10
        
    Raises:
        InvalidDataError: If value is out of range
    """
    pm10_atm = validate_atmospheric_value(pm10_atm, "PM10 atmospheric")
    
    for low, high, aqi_low, aqi_high in PM10_BREAKPOINTS:
        if low <= pm10_atm <= high:
            if high == float('inf'):  # Last breakpoint (425+)
                aqi = int(((500.0 - 301.0) / (500.0 - 425.0)) * (pm10_atm - 425.0) + 301.0)
            else:
                aqi = int(((aqi_high - aqi_low) / (high - low)) * (pm10_atm - low) + aqi_low)
            
            return min(aqi, 500)
    
    # This should never happen due to the last breakpoint having infinite high value
    raise InvalidDataError(f"PM10 value {pm10_atm} out of range")


def calculate_aqi_v2(pm25_atm: float, pm10_atm: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate AQI v2 using atmospheric (ATM) values only.
    
    This function implements the exact algorithm specified:
    1. Use PM2.5 Atmospheric (pm.pm25_atm) as primary value
    2. Apply exact table-based breakpoints from specification
    3. Optional PM10 comparison if it gives higher AQI
    4. Ignore PM1.0 completely (not used in official AQI calculations)
    
    Args:
        pm25_atm: PM2.5 atmospheric concentration (μg/m³)
        pm10_atm: Optional PM10 atmospheric for comparison (μg/m³)
        
    Returns:
        Dictionary with AQI v2 information containing:
        - aqi_value: Final AQI value (0-500)
        - aqi_level: Air quality level description
        - aqi_color: Color code for visualization
        - aqi_source: "PM2.5" or "PM10" (whichever gave higher AQI)
        - pm25_atmospheric: Input PM2.5 atmospheric value
        - pm10_atmospheric: Input PM10 atmospheric value (if provided)
        - pm25_aqi: AQI calculated from PM2.5
        - pm10_aqi: AQI calculated from PM10 (if PM10 provided)
        - health_message: Health advisory message
        - timestamp: Calculation timestamp
        
    Raises:
        InvalidDataError: If input values are invalid
    """
    # Calculate PM2.5 AQI (primary)
    pm25_aqi, pm25_level, pm25_color = _calculate_pm25_aqi_v2(pm25_atm)
    
    # Initialize with PM2.5 results
    final_aqi = pm25_aqi
    final_level = pm25_level
    final_color = pm25_color
    aqi_source = "PM2.5"
    pm10_aqi = None
    
    # Optional PM10 comparison
    if pm10_atm is not None:
        pm10_aqi = _calculate_pm10_aqi_v2(pm10_atm)
        
        # Use higher AQI if PM10 gives worse result
        if pm10_aqi > pm25_aqi:
            final_aqi = pm10_aqi
            aqi_source = "PM10"
            
            # Update level and color based on PM10 AQI
            if pm10_aqi <= 50:
                final_level = "Good"
                final_color = "Green"
            elif pm10_aqi <= 100:
                final_level = "Moderate"
                final_color = "Yellow"
            elif pm10_aqi <= 150:
                final_level = "Unhealthy for Sensitive Groups"
                final_color = "Orange"
            elif pm10_aqi <= 200:
                final_level = "Unhealthy"
                final_color = "Red"
            elif pm10_aqi <= 300:
                final_level = "Very Unhealthy"
                final_color = "Purple"
            else:
                final_level = "Hazardous"
                final_color = "Maroon"
    
    return {
        "aqi_value": min(final_aqi, 500),
        "aqi_level": final_level,
        "aqi_color": final_color,
        "aqi_source": aqi_source,
        "pm25_atmospheric": pm25_atm,
        "pm10_atmospheric": pm10_atm,
        "pm25_aqi": pm25_aqi,
        "pm10_aqi": pm10_aqi,
        "health_message": HEALTH_MESSAGES.get(final_level, "Unknown air quality level"),
        "timestamp": time.time()
    }


def get_aqi_breakpoint_info() -> Dict[str, Any]:
    """
    Get information about AQI breakpoints used in v2 calculation.
    
    Returns:
        Dictionary with breakpoint information for reference
    """
    return {
        "pm25_breakpoints": [
            {
                "concentration_range": f"{low}-{high if high != float('inf') else '∞'}",
                "aqi_range": f"{aqi_low}-{aqi_high}",
                "level": level,
                "color": color
            }
            for low, high, aqi_low, aqi_high, level, color in PM25_BREAKPOINTS
        ],
        "pm10_breakpoints": [
            {
                "concentration_range": f"{low}-{high if high != float('inf') else '∞'}",
                "aqi_range": f"{aqi_low}-{aqi_high}"
            }
            for low, high, aqi_low, aqi_high in PM10_BREAKPOINTS
        ],
        "algorithm_description": "AQI v2 uses atmospheric (ATM) values only, with PM2.5 as primary and optional PM10 comparison",
        "reference": "Matches AirNow, PurpleAir, IQAir calculations"
    }


def test_aqi_v2_calculations() -> Dict[str, Any]:
    """
    Test AQI v2 calculations with known values.
    
    Returns:
        Dictionary with test results for verification
    """
    test_cases = [
        # (pm25_atm, expected_aqi_range, description)
        (5.0, (0, 50), "Clean air"),
        (15.0, (51, 100), "Moderate pollution"),
        (45.0, (101, 150), "Unhealthy for sensitive groups"),
        (80.0, (151, 200), "Unhealthy"),
        (150.0, (201, 300), "Very unhealthy"),
        (300.0, (301, 400), "Hazardous"),
        (400.0, (401, 500), "Very hazardous")
    ]
    
    results = []
    for pm25_atm, expected_range, description in test_cases:
        try:
            aqi_result = calculate_aqi_v2(pm25_atm)
            aqi_value = aqi_result["aqi_value"]
            in_range = expected_range[0] <= aqi_value <= expected_range[1]
            
            results.append({
                "pm25_atm": pm25_atm,
                "description": description,
                "calculated_aqi": aqi_value,
                "expected_range": expected_range,
                "in_range": in_range,
                "level": aqi_result["aqi_level"],
                "color": aqi_result["aqi_color"]
            })
        except Exception as e:
            results.append({
                "pm25_atm": pm25_atm,
                "description": description,
                "error": str(e),
                "in_range": False
            })
    
    return {
        "test_summary": f"Ran {len(test_cases)} test cases",
        "results": results,
        "all_passed": all(r.get("in_range", False) for r in results)
    }