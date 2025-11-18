"""
AQI v2 Tests

This module contains comprehensive tests for the AQI v2 calculation functionality
that uses atmospheric (ATM) values only from the PM25 sensor.

Tests cover:
- Exact breakpoint calculations
- Edge cases and boundary conditions
- PM10 comparison logic
- Error handling and validation
- Integration with PM25Sensor class
"""

import pytest
import sys
from pathlib import Path

# Add the apis module to path for testing
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

try:
    from apis.aqi_v2 import (
        calculate_aqi_v2, PM25_BREAKPOINTS, PM10_BREAKPOINTS,
        validate_atmospheric_value, _calculate_pm25_aqi_v2, _calculate_pm10_aqi_v2,
        get_aqi_breakpoint_info, test_aqi_v2_calculations
    )
    from apis import PM25Sensor
except ImportError as e:
    pytest.skip(f"Cannot import AQI v2 modules: {e}", allow_module_level=True)


class TestAQIV2Basic:
    """Test basic AQI v2 calculation functionality."""
    
    def test_clean_air(self):
        """Test clean air scenario (0-9.0 μg/m³)."""
        result = calculate_aqi_v2(5.0)
        
        assert result["aqi_value"] <= 50
        assert result["aqi_level"] == "Good"
        assert result["aqi_color"] == "Green"
        assert result["aqi_source"] == "PM2.5"
        assert result["pm25_atmospheric"] == 5.0
        assert result["pm10_atmospheric"] is None
        assert result["pm25_aqi"] == result["aqi_value"]
        assert result["pm10_aqi"] is None
        assert "Air quality is satisfactory" in result["health_message"]
    
    def test_moderate_pollution(self):
        """Test moderate pollution scenario (9.1-35.4 μg/m³)."""
        result = calculate_aqi_v2(20.0)
        
        assert 51 <= result["aqi_value"] <= 100
        assert result["aqi_level"] == "Moderate"
        assert result["aqi_color"] == "Yellow"
        assert result["aqi_source"] == "PM2.5"
    
    def test_unhealthy_for_sensitive_groups(self):
        """Test unhealthy for sensitive groups (35.5-55.4 μg/m³)."""
        result = calculate_aqi_v2(45.0)
        
        assert 101 <= result["aqi_value"] <= 150
        assert result["aqi_level"] == "Unhealthy for Sensitive Groups"
        assert result["aqi_color"] == "Orange"
    
    def test_unhealthy(self):
        """Test unhealthy scenario (55.5-125.4 μg/m³)."""
        result = calculate_aqi_v2(80.0)
        
        assert 151 <= result["aqi_value"] <= 200
        assert result["aqi_level"] == "Unhealthy"
        assert result["aqi_color"] == "Red"
    
    def test_very_unhealthy(self):
        """Test very unhealthy scenario (125.5-225.4 μg/m³)."""
        result = calculate_aqi_v2(150.0)
        
        assert 201 <= result["aqi_value"] <= 300
        assert result["aqi_level"] == "Very Unhealthy"
        assert result["aqi_color"] == "Purple"
    
    def test_hazardous(self):
        """Test hazardous scenario (225.5-325.4 μg/m³)."""
        result = calculate_aqi_v2(300.0)
        
        assert 301 <= result["aqi_value"] <= 400
        assert result["aqi_level"] == "Hazardous"
        assert result["aqi_color"] == "Maroon"
    
    def test_extreme_hazardous(self):
        """Test extreme hazardous scenario (325.5+ μg/m³)."""
        result = calculate_aqi_v2(400.0)
        
        assert 401 <= result["aqi_value"] <= 500
        assert result["aqi_level"] == "Hazardous"
        assert result["aqi_color"] == "Maroon"


class TestAQIV2Boundaries:
    """Test boundary conditions and edge cases."""
    
    def test_exact_boundaries(self):
        """Test exact boundary values."""
        boundaries = [
            (0.0, 0, "Good"),
            (9.0, 50, "Good"),
            (9.1, 51, "Moderate"),
            (35.4, 100, "Moderate"),
            (35.5, 101, "Unhealthy for Sensitive Groups"),
            (55.4, 150, "Unhealthy for Sensitive Groups"),
            (55.5, 151, "Unhealthy"),
            (125.4, 200, "Unhealthy"),
            (125.5, 201, "Very Unhealthy"),
            (225.4, 300, "Very Unhealthy"),
            (225.5, 301, "Hazardous"),
            (325.4, 400, "Hazardous"),
            (325.5, 401, "Hazardous")
        ]
        
        for pm25_atm, expected_aqi, expected_level in boundaries:
            result = calculate_aqi_v2(pm25_atm)
            assert result["aqi_value"] == expected_aqi, f"Failed at PM2.5={pm25_atm}"
            assert result["aqi_level"] == expected_level, f"Failed at PM2.5={pm25_atm}"
    
    def test_zero_pollution(self):
        """Test zero pollution case."""
        result = calculate_aqi_v2(0.0)
        assert result["aqi_value"] == 0
        assert result["aqi_level"] == "Good"
    
    def test_maximum_aqi_capping(self):
        """Test that AQI is capped at 500."""
        result = calculate_aqi_v2(1000.0)  # Very high value
        assert result["aqi_value"] <= 500


class TestPM10Comparison:
    """Test PM10 comparison functionality."""
    
    def test_pm10_higher_aqi(self):
        """Test case where PM10 gives higher AQI than PM2.5."""
        # PM2.5 gives moderate AQI, PM10 gives unhealthy AQI
        result = calculate_aqi_v2(pm25_atm=20.0, pm10_atm=180.0)
        
        assert result["aqi_source"] == "PM10"
        assert result["pm25_aqi"] < result["pm10_aqi"]
        assert result["aqi_value"] == result["pm10_aqi"]
        assert result["aqi_level"] == "Unhealthy"
    
    def test_pm25_higher_aqi(self):
        """Test case where PM2.5 gives higher AQI than PM10."""
        # PM2.5 gives unhealthy AQI, PM10 gives moderate AQI
        result = calculate_aqi_v2(pm25_atm=80.0, pm10_atm=50.0)
        
        assert result["aqi_source"] == "PM2.5"
        assert result["pm25_aqi"] > result["pm10_aqi"]
        assert result["aqi_value"] == result["pm25_aqi"]
    
    def test_equal_aqi(self):
        """Test case where PM2.5 and PM10 give equal AQI."""
        result = calculate_aqi_v2(pm25_atm=20.0, pm10_atm=20.0)
        
        assert result["aqi_source"] == "PM2.5"  # PM2.5 is primary
        assert result["pm25_aqi"] == result["pm10_aqi"]
    
    def test_no_pm10_provided(self):
        """Test when PM10 is not provided."""
        result = calculate_aqi_v2(pm25_atm=30.0)
        
        assert result["aqi_source"] == "PM2.5"
        assert result["pm10_atmospheric"] is None
        assert result["pm10_aqi"] is None


class TestValidation:
    """Test input validation."""
    
    def test_valid_values(self):
        """Test valid input values."""
        valid_values = [0.0, 5.5, 25.0, 100.0, 500.0]
        
        for value in valid_values:
            try:
                validate_atmospheric_value(value)
            except Exception:
                pytest.fail(f"Valid value {value} raised exception")
    
    def test_negative_values(self):
        """Test negative input values."""
        with pytest.raises(Exception):
            validate_atmospheric_value(-1.0)
    
    def test_too_high_values(self):
        """Test values that are too high."""
        with pytest.raises(Exception):
            validate_atmospheric_value(2000.0)  # Above 1000 limit
    
    def test_non_numeric_values(self):
        """Test non-numeric input values."""
        with pytest.raises(Exception):
            validate_atmospheric_value("invalid")
        
        with pytest.raises(Exception):
            validate_atmospheric_value(None)
    
    def test_nan_infinity(self):
        """Test NaN and infinity values."""
        import math
        
        with pytest.raises(Exception):
            validate_atmospheric_value(math.nan)
        
        with pytest.raises(Exception):
            validate_atmospheric_value(math.inf)


class TestBreakpointInfo:
    """Test breakpoint information functions."""
    
    def test_get_breakpoint_info(self):
        """Test getting breakpoint information."""
        info = get_aqi_breakpoint_info()
        
        assert "pm25_breakpoints" in info
        assert "pm10_breakpoints" in info
        assert "algorithm_description" in info
        assert "reference" in info
        
        assert len(info["pm25_breakpoints"]) == 7  # 7 PM2.5 breakpoints
        assert len(info["pm10_breakpoints"]) == 6  # 6 PM10 breakpoints
    
    def test_breakpoint_structure(self):
        """Test breakpoint data structure."""
        for low, high, aqi_low, aqi_high, level, color in PM25_BREAKPOINTS:
            assert isinstance(low, (int, float))
            assert isinstance(high, (int, float))
            assert isinstance(aqi_low, int)
            assert isinstance(aqi_high, int)
            assert isinstance(level, str)
            assert isinstance(color, str)
            assert low <= high
            assert aqi_low <= aqi_high


class TestAQIV2TestSuite:
    """Test the built-in test suite."""
    
    def test_test_suite(self):
        """Test the built-in test suite function."""
        results = test_aqi_v2_calculations()
        
        assert "test_summary" in results
        assert "results" in results
        assert "all_passed" in results
        assert len(results["results"]) > 0
        assert isinstance(results["all_passed"], bool)


class TestPM25SensorIntegration:
    """Test integration with PM25Sensor class using real hardware."""
    
    def test_sensor_has_aqi_v2_methods(self, sensor):
        """Test that sensor has AQI v2 methods."""
        assert hasattr(sensor, 'get_aqi_v2')
        assert hasattr(sensor, 'get_air_quality_summary_v2')
        assert hasattr(sensor, 'compare_aqi_methods')
    
    def test_method_signatures(self, sensor):
        """Test method signatures."""
        # Test that methods accept expected parameters
        import inspect
        
        # get_aqi_v2 should accept use_cache and include_pm10_comparison
        sig = inspect.signature(sensor.get_aqi_v2)
        assert 'use_cache' in sig.parameters
        assert 'include_pm10_comparison' in sig.parameters
        
        # get_air_quality_summary_v2 should accept same parameters
        sig = inspect.signature(sensor.get_air_quality_summary_v2)
        assert 'use_cache' in sig.parameters
        assert 'include_pm10_comparison' in sig.parameters
        
        # get_air_quality_summary_v2 should accept same parameters
        sig = inspect.signature(sensor.get_air_quality_summary_v2)
        assert 'use_cache' in sig.parameters
        assert 'include_pm10_comparison' in sig.parameters


class TestAQIV2RealData:
    """Test AQI v2 functionality with real sensor data."""
    
    def test_real_sensor_aqi_calculation(self, sensor):
        """Test AQI v2 calculation with real sensor data."""
        # Get real sensor readings
        pm25_standard = sensor.get_pm2_5_standard(use_cache=False)
        pm10_standard = sensor.get_pm10_standard(use_cache=False)
        
        # Test AQI v2 calculation with real data
        aqi_result = sensor.get_aqi_v2(use_cache=False, include_pm10_comparison=True)
        
        # Verify structure
        assert "aqi_value" in aqi_result
        assert "aqi_level" in aqi_result
        assert "aqi_color" in aqi_result
        assert "aqi_source" in aqi_result
        assert "health_message" in aqi_result
        assert "pm25_atmospheric" in aqi_result
        assert "pm10_atmospheric" in aqi_result
        assert "pm25_aqi" in aqi_result
        assert "pm10_aqi" in aqi_result
        assert "timestamp" in aqi_result
        
        # Verify data consistency
        assert isinstance(aqi_result["pm25_atmospheric"], (int, float))
        assert aqi_result["pm25_atmospheric"] >= 0
        assert aqi_result["pm25_aqi"] == aqi_result["aqi_value"]
        assert aqi_result["aqi_value"] == aqi_result["pm25_aqi"]
        assert isinstance(aqi_result["aqi_value"], int)
        assert aqi_result["aqi_value"] >= 0
        assert aqi_result["aqi_value"] <= 500
        
        # Verify AQI level is valid
        valid_levels = ["Good", "Moderate", "Unhealthy for Sensitive Groups", 
                      "Unhealthy", "Very Unhealthy", "Hazardous", "Beyond AQI"]
        assert aqi_result["aqi_level"] in valid_levels
        
        # Verify color is valid
        valid_colors = ["Green", "Yellow", "Orange", "Red", "Purple", "Maroon"]
        assert aqi_result["aqi_color"] in valid_colors
    
    def test_real_sensor_air_quality_summary(self, sensor):
        """Test air quality summary with real sensor data."""
        # Get comprehensive summary with real data
        summary = sensor.get_air_quality_summary_v2(use_cache=False, include_pm10_comparison=True)
        
        # Verify comprehensive structure
        required_fields = [
            "aqi_value", "aqi_level", "aqi_color", "aqi_source",
            "health_message", "pm25_atmospheric", "pm10_atmospheric",
            "pm25_aqi", "pm10_aqi", "particle_counts", 
            "timestamp", "data_source"
        ]
        
        for field in required_fields:
            assert field in summary, f"Missing field: {field}"
        
        # Verify data consistency
        assert summary["data_source"] == "real_sensor"
        assert isinstance(summary["timestamp"], float)
        assert summary["timestamp"] > 0
        
        # Verify particle counts structure
        particle_counts = summary["particle_counts"]
        assert isinstance(particle_counts, dict)
        expected_sizes = ["0.3um", "0.5um", "1.0um", "2.5um", "5.0um", "10um"]
        for size in expected_sizes:
            assert size in particle_counts
            assert isinstance(particle_counts[size], int)
            assert particle_counts[size] >= 0
    
    def test_real_sensor_aqi_comparison(self, sensor):
        """Test AQI comparison functionality with real sensor data."""
        # Get comparison result
        comparison = sensor.compare_aqi_methods(use_cache=False)
        
        # Verify comparison structure
        assert "v2_result" in comparison
        assert "legacy_result" in comparison
        assert "comparison_summary" in comparison
        
        # Both results should have valid AQI values
        assert comparison["v2_result"]["aqi_value"] >= 0
        assert comparison["legacy_result"]["aqi_value"] >= 0
        
        # Comparison summary should be meaningful
        summary = comparison["comparison_summary"]
        assert "values_match" in summary
        assert "difference" in summary
        assert "higher_source" in summary


class TestPerformance:
    """Test performance aspects."""
    
    def test_calculation_speed(self):
        """Test that calculations are fast."""
        import time
        
        start_time = time.time()
        
        # Run 1000 calculations
        for i in range(1000):
            calculate_aqi_v2(25.0 + i * 0.1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 1000 calculations in under 1 second
        assert duration < 1.0, f"Too slow: {duration:.3f}s for 1000 calculations"
    
    def test_memory_usage(self):
        """Test that calculations don't leak memory."""
        import gc
        import sys
        
        # Get initial object count
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Run many calculations
        for i in range(10000):
            calculate_aqi_v2(25.0 + i * 0.001)
        
        # Check final object count
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Should not have created excessive numbers of objects
        object_increase = final_objects - initial_objects
        assert object_increase < 1000, f"Too many objects created: {object_increase}"


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])