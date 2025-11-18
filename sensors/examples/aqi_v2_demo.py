"""
AQI v2 Demo - Atmospheric Values Only

This example demonstrates the new AQI v2 calculation that uses only atmospheric (ATM) values
from the PM25 sensor, following the exact specification provided.

The AQI v2 algorithm:
1. Uses PM2.5 Atmospheric (pm.pm25_atm) as the primary value
2. Applies exact table-based breakpoints from specification
3. Optional PM10 comparison if it gives higher AQI
4. Ignores PM1.0 completely (not used in official AQI calculations)

This provides the same AQI values as AirNow, PurpleAir, IQAir, etc.
"""

import sys
import time
from pathlib import Path

# Add the apis module to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from apis import PM25Sensor, PM25Config
from apis.aqi_v2 import calculate_aqi_v2, get_aqi_breakpoint_info, test_aqi_v2_calculations


def main():
    """Main function demonstrating AQI v2 functionality."""
    print("=== AQI v2 Demo - Atmospheric Values Only ===\n")
    
    try:
        # Create sensor with default configuration
        print("1. Initializing PM25 sensor...")
        sensor = PM25Sensor(auto_connect=True, auto_warmup=True)
        
        # Check sensor status
        print("2. Checking sensor status...")
        status = sensor.get_sensor_status()
        print(f"   Connected: {status['is_connected']}")
        print(f"   Initialized: {status['is_initialized']}")
        
        if not status['is_connected']:
            print("   ERROR: Sensor not connected!")
            return
        
        print("\n3. Basic AQI v2 (PM2.5 Atmospheric only):")
        try:
            aqi_v2 = sensor.get_aqi_v2()
            print(f"   PM2.5 ATM: {aqi_v2['pm25_atmospheric']} μg/m³")
            print(f"   AQI: {aqi_v2['aqi_value']} ({aqi_v2['aqi_level']})")
            print(f"   Color: {aqi_v2['aqi_color']}")
            print(f"   Source: {aqi_v2['aqi_source']}")
            print(f"   Health: {aqi_v2['health_message']}")
            
        except Exception as e:
            print(f"   ERROR calculating AQI v2: {e}")
        
        print("\n4. AQI v2 with PM10 comparison:")
        try:
            aqi_v2_pm10 = sensor.get_aqi_v2(include_pm10_comparison=True)
            print(f"   PM2.5 ATM: {aqi_v2_pm10['pm25_atmospheric']} μg/m³")
            print(f"   PM10 ATM: {aqi_v2_pm10['pm10_atmospheric']} μg/m³")
            print(f"   Final AQI: {aqi_v2_pm10['aqi_value']} ({aqi_v2_pm10['aqi_level']})")
            print(f"   AQI Source: {aqi_v2_pm10['aqi_source']}")
            print(f"   PM2.5 AQI: {aqi_v2_pm10['pm25_aqi']}")
            print(f"   PM10 AQI: {aqi_v2_pm10['pm10_aqi']}")
            
        except Exception as e:
            print(f"   ERROR calculating AQI v2 with PM10: {e}")
        
        print("\n5. Air Quality Summary v2:")
        try:
            summary_v2 = sensor.get_air_quality_summary_v2(include_pm10_comparison=True)
            print(f"   Method: {summary_v2['method']}")
            print(f"   PM2.5: {summary_v2['pm25_atmospheric']} μg/m³")
            print(f"   PM10: {summary_v2['pm10_atmospheric']} μg/m³")
            print(f"   AQI: {summary_v2['aqi_value']} ({summary_v2['aqi_level']})")
            print(f"   Color: {summary_v2['aqi_color']}")
            print(f"   Health: {summary_v2['health_message']}")
            
        except Exception as e:
            print(f"   ERROR getting summary v2: {e}")
        
        print("\n6. Comparison: AQI v1 (Standard) vs v2 (Atmospheric):")
        try:
            comparison = sensor.compare_aqi_methods()
            print(f"   v1 (Standard): PM2.5={comparison['v1_standard']['pm25']} → AQI={comparison['v1_standard']['aqi_value']}")
            print(f"   v2 (Atmospheric): PM2.5={comparison['v2_atmospheric']['pm25']} → AQI={comparison['v2_atmospheric']['aqi_value']}")
            print(f"   PM2.5 Difference: {comparison['differences']['pm25_diff']:.1f} μg/m³")
            print(f"   AQI Difference: {comparison['differences']['aqi_diff']}")
            print(f"   Level Changed: {comparison['differences']['level_changed']}")
            
        except Exception as e:
            print(f"   ERROR comparing methods: {e}")
        
        print("\n7. Multiple readings test:")
        try:
            print("   Taking 5 readings with 2-second intervals:")
            for i in range(5):
                aqi_v2 = sensor.get_aqi_v2()
                summary_v2 = sensor.get_air_quality_summary_v2()
                print(f"   Reading {i+1}: PM2.5={aqi_v2['pm25_atmospheric']} → AQI={aqi_v2['aqi_value']} ({aqi_v2['aqi_level']})")
                time.sleep(2)
                
        except Exception as e:
            print(f"   ERROR in multiple readings: {e}")
        
        print("\n8. AQI v2 Breakpoint Information:")
        try:
            breakpoint_info = get_aqi_breakpoint_info()
            print("   PM2.5 Breakpoints:")
            for bp in breakpoint_info['pm25_breakpoints']:
                print(f"     {bp['concentration_range']} μg/m³ → AQI {bp['aqi_range']} ({bp['level']})")
            
        except Exception as e:
            print(f"   ERROR getting breakpoint info: {e}")
        
        print("\n=== AQI v2 demo completed successfully! ===")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("Make sure the PM25 sensor is connected to I2C bus 1 at address 0x19")
        
    finally:
        # Clean up
        try:
            sensor = locals().get('sensor')
            if sensor is not None:
                sensor.disconnect()
                print("\nSensor disconnected.")
        except Exception:
            pass


def demonstrate_aqi_v2_direct():
    """Demonstrate AQI v2 calculation with direct function calls."""
    print("\n=== Direct AQI v2 Function Demo ===\n")
    
    print("1. Testing AQI v2 with known values:")
    test_values = [
        (5.0, "Clean air"),
        (15.0, "Moderate pollution"),
        (45.0, "Unhealthy for sensitive groups"),
        (80.0, "Unhealthy"),
        (150.0, "Very unhealthy"),
        (300.0, "Hazardous"),
        (400.0, "Very hazardous")
    ]
    
    for pm25_atm, description in test_values:
        try:
            aqi_result = calculate_aqi_v2(pm25_atm)
            print(f"   {description}: PM2.5={pm25_atm} → AQI={aqi_result['aqi_value']} ({aqi_result['aqi_level']})")
        except Exception as e:
            print(f"   ERROR with {pm25_atm}: {e}")
    
    print("\n2. Testing PM10 comparison:")
    try:
        # Case where PM10 gives higher AQI
        aqi_result = calculate_aqi_v2(pm25_atm=20.0, pm10_atm=180.0)
        print(f"   PM2.5=20, PM10=180 → AQI={aqi_result['aqi_value']} (Source: {aqi_result['aqi_source']})")
        print(f"   PM2.5 AQI: {aqi_result['pm25_aqi']}, PM10 AQI: {aqi_result['pm10_aqi']}")
        
        # Case where PM2.5 gives higher AQI
        aqi_result = calculate_aqi_v2(pm25_atm=80.0, pm10_atm=50.0)
        print(f"   PM2.5=80, PM10=50 → AQI={aqi_result['aqi_value']} (Source: {aqi_result['aqi_source']})")
        print(f"   PM2.5 AQI: {aqi_result['pm25_aqi']}, PM10 AQI: {aqi_result['pm10_aqi']}")
        
    except Exception as e:
        print(f"   ERROR in PM10 comparison: {e}")
    
    print("\n3. Running AQI v2 test suite:")
    try:
        test_results = test_aqi_v2_calculations()
        print(f"   {test_results['test_summary']}")
        print(f"   All tests passed: {test_results['all_passed']}")
        
        for result in test_results['results']:
            if result.get('in_range', False):
                print(f"   ✓ {result['description']}: PM2.5={result['pm25_atm']} → AQI={result['calculated_aqi']}")
            else:
                print(f"   ✗ {result['description']}: {result.get('error', 'Out of range')}")
                
    except Exception as e:
        print(f"   ERROR running test suite: {e}")


def demonstrate_edge_cases():
    """Demonstrate edge cases and error handling."""
    print("\n=== Edge Cases and Error Handling Demo ===\n")
    
    print("1. Testing edge cases:")
    edge_cases = [
        (0.0, "Zero pollution"),
        (9.0, "Good/Moderate boundary"),
        (9.1, "Just into Moderate"),
        (35.4, "Moderate/USG boundary"),
        (35.5, "Just into Unhealthy for Sensitive Groups"),
        (325.4, "Hazardous boundary"),
        (325.5, "Just into extreme Hazardous"),
        (1000.0, "Very high pollution")
    ]
    
    for pm25_atm, description in edge_cases:
        try:
            aqi_result = calculate_aqi_v2(pm25_atm)
            print(f"   {description}: PM2.5={pm25_atm} → AQI={aqi_result['aqi_value']} ({aqi_result['aqi_level']})")
        except Exception as e:
            print(f"   ERROR with {pm25_atm}: {e}")
    
    print("\n2. Testing error cases:")
    error_cases = [
        (-1.0, "Negative value"),
        (-10.0, "Very negative value"),
        (float('nan'), "NaN value"),
        (float('inf'), "Infinite value"),
        (None, "None value"),
        ("invalid", "String value")
    ]
    
    for value, description in error_cases:
        try:
            aqi_result = calculate_aqi_v2(value)  # type: ignore
            print(f"   {description}: Unexpected success → {aqi_result['aqi_value']}")
        except Exception as e:
            print(f"   {description}: Correctly caught error → {type(e).__name__}")


if __name__ == "__main__":
    main()
    
    # Uncomment to see additional demonstrations
    demonstrate_aqi_v2_direct()
    demonstrate_edge_cases()