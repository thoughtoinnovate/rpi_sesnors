"""
PM25 Sensor Utility Functions

This module provides utility functions for data validation, conversion,
and common operations used across the PM25 sensor API.
"""

import time
import logging
import statistics
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

from .constants import (
    MAX_PM_CONCENTRATION, MAX_PARTICLE_COUNT, MIN_READ_INTERVAL,
    PM_TYPES, PARTICLE_SIZES
)
from .exceptions import CalibrationError, InvalidDataError


def validate_pm_concentration(value: Union[int, float], parameter_name: str = "concentration") -> float:
    """
    Validate PM concentration value is within expected range.
    
    Args:
        value: Concentration value to validate
        parameter_name: Name of parameter for error messages
        
    Returns:
        Validated concentration value as float
        
    Raises:
        CalibrationError: If value is out of valid range
    """
    try:
        concentration = float(value)
    except (ValueError, TypeError):
        raise CalibrationError(parameter_name, value, f"numeric value (0-{MAX_PM_CONCENTRATION})")
    
    if concentration < 0:
        raise CalibrationError(parameter_name, concentration, f"non-negative value (max {MAX_PM_CONCENTRATION})")
    
    if concentration > MAX_PM_CONCENTRATION:
        # Log warning but allow slightly higher values (might be heavily polluted)
        logging.getLogger("pm25_sensor.utils").warning(
            f"High {parameter_name}: {concentration} μg/m³ "
            f"(expected max: {MAX_PM_CONCENTRATION} μg/m³)"
        )
    
    return concentration


def validate_particle_count(value: Union[int, float], parameter_name: str = "particle_count") -> int:
    """
    Validate particle count value is within expected range.
    
    Args:
        value: Particle count value to validate
        parameter_name: Name of parameter for error messages
        
    Returns:
        Validated particle count as int
        
    Raises:
        CalibrationError: If value is out of valid range
    """
    try:
        count = int(value)
    except (ValueError, TypeError):
        raise CalibrationError(parameter_name, value, f"integer value (0-{MAX_PARTICLE_COUNT})")
    
    if count < 0:
        raise CalibrationError(parameter_name, count, f"non-negative integer (max {MAX_PARTICLE_COUNT})")
    
    if count > MAX_PARTICLE_COUNT:
        # Log warning but allow slightly higher values (might be very dusty)
        logging.getLogger("pm25_sensor.utils").warning(
            f"High {parameter_name}: {count} "
            f"(expected max: {MAX_PARTICLE_COUNT})"
        )
    
    return count


def validate_register_address(register: int) -> int:
    """
    Validate register address is within valid range.
    
    Args:
        register: Register address to validate
        
    Returns:
        Validated register address
        
    Raises:
        InvalidDataError: If register address is invalid
    """
    try:
        reg = int(register)
    except (ValueError, TypeError):
        raise InvalidDataError(f"Invalid register address: {register}")
    
    if reg < 0 or reg > 0xFF:
        raise InvalidDataError(f"Register address out of range: {reg} (expected 0x00-0xFF)")
    
    return reg


def convert_bytes_to_value(data: List[int], byte_order: str = "msb") -> int:
    """
    Convert list of bytes to integer value.
    
    Args:
        data: List of bytes to convert
        byte_order: "msb" for most significant byte first, "lsb" for least significant
        
    Returns:
        Converted integer value
        
    Raises:
        InvalidDataError: If data is invalid
    """
    if not data:
        raise InvalidDataError("Empty byte array")
    
    if len(data) > 4:
        raise InvalidDataError(f"Too many bytes: {len(data)} (max 4)")
    
    for byte in data:
        if not isinstance(byte, int) or byte < 0 or byte > 255:
            raise InvalidDataError(f"Invalid byte value: {byte} (expected 0-255)")
    
    if byte_order.lower() == "msb":
        result = 0
        for byte in data:
            result = (result << 8) | byte
        return result
    elif byte_order.lower() == "lsb":
        result = 0
        for i, byte in enumerate(data):
            result |= byte << (8 * i)
        return result
    else:
        raise InvalidDataError(f"Invalid byte order: {byte_order} (expected 'msb' or 'lsb')")


def calculate_air_quality_index(pm25_concentration: float) -> Dict[str, Any]:
    """
    Calculate Air Quality Index based on PM2.5 concentration.
    
    Args:
        pm25_concentration: PM2.5 concentration in μg/m³
        
    Returns:
        Dictionary with AQI information
    """
    # EPA AQI breakpoints for PM2.5
    if pm25_concentration <= 12.0:
        aqi_level = "Good"
        aqi_color = "green"
        aqi_value = int((50.0 / 12.0) * pm25_concentration)
        health_message = "Air quality is satisfactory"
    elif pm25_concentration <= 35.4:
        aqi_level = "Moderate"
        aqi_color = "yellow"
        aqi_value = int(((100.0 - 50.0) / (35.4 - 12.0)) * (pm25_concentration - 12.0) + 50.0)
        health_message = "Air quality is acceptable for most people"
    elif pm25_concentration <= 55.4:
        aqi_level = "Unhealthy for Sensitive Groups"
        aqi_color = "orange"
        aqi_value = int(((150.0 - 100.0) / (55.4 - 35.4)) * (pm25_concentration - 35.4) + 100.0)
        health_message = "Sensitive groups may experience health effects"
    elif pm25_concentration <= 150.4:
        aqi_level = "Unhealthy"
        aqi_color = "red"
        aqi_value = int(((200.0 - 150.0) / (150.4 - 55.4)) * (pm25_concentration - 55.4) + 150.0)
        health_message = "Everyone may experience health effects"
    elif pm25_concentration <= 250.4:
        aqi_level = "Very Unhealthy"
        aqi_color = "purple"
        aqi_value = int(((300.0 - 200.0) / (250.4 - 150.4)) * (pm25_concentration - 150.4) + 200.0)
        health_message = "Health alert: everyone may experience serious health effects"
    else:
        aqi_level = "Hazardous"
        aqi_color = "maroon"
        aqi_value = int(((500.0 - 300.0) / (500.4 - 250.4)) * (pm25_concentration - 250.4) + 300.0)
        health_message = "Emergency conditions: everyone affected"
    
    return {
        "aqi_value": min(aqi_value, 500),
        "aqi_level": aqi_level,
        "aqi_color": aqi_color,
        "health_message": health_message,
        "pm25_concentration": pm25_concentration,
        "timestamp": time.time()
    }


def analyze_particle_distribution(particle_counts: Dict[str, int]) -> Dict[str, Any]:
    """
    Analyze particle size distribution.
    
    Args:
        particle_counts: Dictionary with particle counts by size
        
    Returns:
        Dictionary with distribution analysis
    """
    if not particle_counts:
        return {
            "total_particles": 0,
            "distribution": {},
            "dominant_size": None,
            "size_percentages": {},
            "concentration_estimate": 0.0
        }
    
    total_particles = sum(particle_counts.values())
    
    # Calculate percentages
    distribution = {}
    for size, count in particle_counts.items():
        percentage = (count / total_particles * 100) if total_particles > 0 else 0
        distribution[size] = {
            "count": count,
            "percentage": round(percentage, 2)
        }
    
    # Find dominant size
    dominant_size = max(particle_counts.items(), key=lambda x: x[1])[0] if particle_counts else None
    
    # Estimate mass concentration (simplified)
    # Using approximate particle masses (very rough calculation)
    mass_factors = {
        "0.3um": 0.000014,  # ~14 femtograms
        "0.5um": 0.000065,  # ~65 femtograms
        "1.0um": 0.000524,  # ~524 femtograms
        "2.5um": 0.008180,  # ~8.18 picograms
        "5.0um": 0.065450,  # ~65.45 picograms
        "10um": 0.523600   # ~523.6 picograms
    }
    
    estimated_mass = 0.0
    for size, count in particle_counts.items():
        factor = mass_factors.get(size, 0.0001)  # default factor
        estimated_mass += count * factor
    
    return {
        "total_particles": total_particles,
        "distribution": distribution,
        "dominant_size": dominant_size,
        "size_percentages": {size: data["percentage"] for size, data in distribution.items()},
        "estimated_mass_ug_m3": estimated_mass,
        "analysis_timestamp": time.time()
    }


def smooth_readings(readings: List[float], window_size: int = 5) -> List[float]:
    """
    Apply moving average smoothing to sensor readings.
    
    Args:
        readings: List of sensor readings
        window_size: Size of moving average window
        
    Returns:
        List of smoothed readings
    """
    if not readings or window_size <= 1:
        return readings.copy()
    
    smoothed = []
    half_window = window_size // 2
    
    for i in range(len(readings)):
        start = max(0, i - half_window)
        end = min(len(readings), i + half_window + 1)
        window = readings[start:end]
        smoothed.append(statistics.mean(window))
    
    return smoothed


def detect_outliers(readings: List[float], threshold: float = 2.0) -> List[int]:
    """
    Detect outliers in sensor readings using standard deviation method.
    
    Args:
        readings: List of sensor readings
        threshold: Number of standard deviations to use as threshold
        
    Returns:
        List of indices of outlier readings
    """
    if len(readings) < 3:
        return []
    
    mean_val = statistics.mean(readings)
    std_val = statistics.stdev(readings)
    
    if std_val == 0:
        return []
    
    outliers = []
    for i, reading in enumerate(readings):
        z_score = abs(reading - mean_val) / std_val
        if z_score > threshold:
            outliers.append(i)
    
    return outliers


def calculate_reading_statistics(readings: List[float]) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics for sensor readings.
    
    Args:
        readings: List of sensor readings
        
    Returns:
        Dictionary with statistical analysis
    """
    if not readings:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "std": None,
            "variance": None
        }
    
    return {
        "count": len(readings),
        "mean": statistics.mean(readings),
        "median": statistics.median(readings),
        "min": min(readings),
        "max": max(readings),
        "std": statistics.stdev(readings) if len(readings) > 1 else 0,
        "variance": statistics.variance(readings) if len(readings) > 1 else 0,
        "range": max(readings) - min(readings)
    }


def format_sensor_data(data: Dict[str, Any], format_type: str = "readable") -> str:
    """
    Format sensor data for display or logging.
    
    Args:
        data: Sensor data dictionary
        format_type: "readable", "json", "csv", or "compact"
        
    Returns:
        Formatted string representation
    """
    if format_type.lower() == "json":
        import json
        return json.dumps(data, indent=2, default=str)
    
    elif format_type.lower() == "csv":
        if not data:
            return ""
        
        headers = []
        values = []
        
        def flatten_dict(d, prefix=""):
            for key, value in d.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    flatten_dict(value, full_key)
                else:
                    headers.append(full_key)
                    values.append(str(value))
        
        flatten_dict(data)
        return ",".join(headers) + "\n" + ",".join(values)
    
    elif format_type.lower() == "compact":
        compact_parts = []
        for key, value in data.items():
            if isinstance(value, (int, float, str, bool)):
                compact_parts.append(f"{key}={value}")
        return " ".join(compact_parts)
    
    else:  # readable format (default)
        lines = ["PM25 Sensor Data:"]
        
        def format_dict(d, indent=0):
            for key, value in d.items():
                spaces = "  " * indent
                if isinstance(value, dict):
                    lines.append(f"{spaces}{key}:")
                    format_dict(value, indent + 1)
                else:
                    lines.append(f"{spaces}{key}: {value}")
        
        format_dict(data)
        return "\n".join(lines)


def save_readings_to_file(readings: List[Dict[str, Any]], file_path: Union[str, Path], 
                        format_type: str = "csv") -> bool:
    """
    Save sensor readings to file.
    
    Args:
        readings: List of reading dictionaries
        file_path: Path to save file
        format_type: "csv", "json", or "txt"
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format_type.lower() == "csv":
            if not readings:
                return True
            
            # Get headers from first reading
            headers = set()
            for reading in readings:
                headers.update(reading.keys())
            headers = sorted(headers)
            
            with open(file_path, 'w') as f:
                # Write header
                f.write(",".join(headers) + "\n")
                
                # Write data
                for reading in readings:
                    row = [str(reading.get(header, "")) for header in headers]
                    f.write(",".join(row) + "\n")
        
        elif format_type.lower() == "json":
            import json
            with open(file_path, 'w') as f:
                json.dump(readings, f, indent=2, default=str)
        
        else:  # txt format
            with open(file_path, 'w') as f:
                for i, reading in enumerate(readings):
                    f.write(f"Reading {i+1}:\n")
                    f.write(format_sensor_data(reading, "readable"))
                    f.write("\n" + "-"*50 + "\n")
        
        return True
        
    except Exception as e:
        logging.getLogger("pm25_sensor.utils").error(f"Failed to save readings to {file_path}: {e}")
        return False


def get_pm_type_description(register: int) -> str:
    """Get human-readable description for PM type register."""
    return PM_TYPES.get(register, f"Unknown PM type (0x{register:02X})")


def get_particle_size_description(register: int) -> str:
    """Get human-readable description for particle size register."""
    return PARTICLE_SIZES.get(register, f"Unknown particle size (0x{register:02X})")


def calculate_time_interval(readings: List[Dict[str, Any]], 
                         timestamp_key: str = "timestamp") -> Dict[str, float]:
    """
    Calculate time intervals between readings.
    
    Args:
        readings: List of reading dictionaries with timestamps
        timestamp_key: Key name for timestamp field
        
    Returns:
        Dictionary with interval statistics
    """
    if len(readings) < 2:
        return {
            "count": len(readings),
            "total_duration": 0.0,
            "average_interval": 0.0,
            "min_interval": 0.0,
            "max_interval": 0.0
        }
    
    timestamps = []
    for reading in readings:
        timestamp = reading.get(timestamp_key)
        if timestamp is not None:
            timestamps.append(float(timestamp))
    
    if len(timestamps) < 2:
        return {
            "count": len(timestamps),
            "total_duration": 0.0,
            "average_interval": 0.0,
            "min_interval": 0.0,
            "max_interval": 0.0
        }
    
    intervals = []
    for i in range(1, len(timestamps)):
        intervals.append(timestamps[i] - timestamps[i-1])
    
    return {
        "count": len(intervals),
        "total_duration": timestamps[-1] - timestamps[0],
        "average_interval": statistics.mean(intervals),
        "min_interval": min(intervals),
        "max_interval": max(intervals)
    }


def create_reading_summary(readings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a comprehensive summary of sensor readings.
    
    Args:
        readings: List of reading dictionaries
        
    Returns:
        Dictionary with reading summary
    """
    if not readings:
        return {
            "total_readings": 0,
            "time_span": 0.0,
            "data_quality": "no_data"
        }
    
    # Extract timestamps
    timestamps = []
    for reading in readings:
        timestamp = reading.get("timestamp")
        if timestamp is not None:
            timestamps.append(float(timestamp))
    
    if not timestamps:
        return {
            "total_readings": len(readings),
            "time_span": 0.0,
            "data_quality": "no_timestamps"
        }
    
    time_span = timestamps[-1] - timestamps[0]
    
    # Analyze data quality
    quality_score = 100.0
    quality_issues = []
    
    # Check for missing timestamps
    if len(timestamps) < len(readings):
        quality_score -= 10
        quality_issues.append("missing_timestamps")
    
    # Check for gaps in data
    if len(timestamps) > 1:
        intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        avg_interval = statistics.mean(intervals)
        if avg_interval > MIN_READ_INTERVAL * 2:
            quality_score -= 15
            quality_issues.append("data_gaps")
    
    # Determine overall quality
    if quality_score >= 90:
        data_quality = "excellent"
    elif quality_score >= 75:
        data_quality = "good"
    elif quality_score >= 60:
        data_quality = "fair"
    else:
        data_quality = "poor"
    
    return {
        "total_readings": len(readings),
        "readings_with_timestamps": len(timestamps),
        "time_span_seconds": time_span,
        "time_span_hours": time_span / 3600,
        "average_interval": time_span / (len(timestamps) - 1) if len(timestamps) > 1 else 0,
        "data_quality_score": quality_score,
        "data_quality": data_quality,
        "quality_issues": quality_issues,
        "first_reading_time": timestamps[0],
        "last_reading_time": timestamps[-1],
        "summary_timestamp": time.time()
    }
