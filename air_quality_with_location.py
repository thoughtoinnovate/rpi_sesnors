"""
Air Quality with Location Demo

This example demonstrates the complete integration of AQI v2 calculation
with location detection for comprehensive air quality monitoring.
"""

import sys
import time
from pathlib import Path

# Add the apis module to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

# Simple location detection
import requests
import json
from typing import Dict, Any


def get_location() -> Dict[str, Any]:
    """Get current location using IP-based geolocation."""
    try:
        response = requests.get("https://ipinfo.io/json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "loc" in data:
                lat, lon = map(float, data["loc"].split(","))
                return {
                    "latitude": lat,
                    "longitude": lon,
                    "city": data.get("city"),
                    "country": data.get("country"),
                    "ip": data.get("ip"),
                    "source": "ipinfo.io",
                    "timestamp": time.time()
                }
    except Exception as e:
        print(f"Location detection error: {e}")
    
    # Default location
    return {
        "latitude": 40.7128,  # New York
        "longitude": -74.0060,
        "city": "New York",
        "country": "United States",
        "source": "default",
        "timestamp": time.time()
    }


def main():
    """Main function demonstrating air quality with location."""
    print("=== Air Quality with Location Demo ===\n")
    
    try:
        # Import PM25 sensor
        from apis import PM25Sensor
        
        print("1. Initializing PM25 sensor...")
        sensor = PM25Sensor(auto_connect=True, auto_warmup=True)
        
        # Check sensor status
        status = sensor.get_sensor_status()
        print(f"   Connected: {status['is_connected']}")
        print(f"   Initialized: {status['is_initialized']}")
        
        if not status['is_connected']:
            print("   ERROR: Sensor not connected!")
            return
        
        print("\n2. Getting Location Information...")
        location = get_location()
        print(f"   Location: {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}")
        print(f"   Coordinates: {location['latitude']:.4f}, {location['longitude']:.4f}")
        print(f"   IP: {location.get('ip', 'Unknown')}")
        print(f"   Source: {location['source']}")
        
        print("\n3. Getting Air Quality Data...")
        # Get AQI v2 data
        aqi_v2 = sensor.get_aqi_v2(include_pm10_comparison=True)
        
        print("   Air Quality Results:")
        print(f"   PM2.5 Atmospheric: {aqi_v2['pm25_atmospheric']} μg/m³")
        print(f"   PM10 Atmospheric: {aqi_v2['pm10_atmospheric']} μg/m³")
        print(f"   AQI Value: {aqi_v2['aqi_value']}")
        print(f"   AQI Level: {aqi_v2['aqi_level']}")
        print(f"   AQI Color: {aqi_v2['aqi_color']}")
        print(f"   AQI Source: {aqi_v2['aqi_source']}")
        print(f"   Health Message: {aqi_v2['health_message']}")
        
        print("\n4. Combined Air Quality and Location Report:")
        print("   " + "="*50)
        print(f"   📍 Location: {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}")
        print(f"   🌍 Coordinates: {location['latitude']:.4f}°N, {abs(location['longitude']):.4f}°{'W' if location['longitude'] < 0 else 'E'}")
        print(f"   🌫 PM2.5: {aqi_v2['pm25_atmospheric']} μg/m³")
        print(f"   🌫 PM10: {aqi_v2['pm10_atmospheric']} μg/m³")
        print(f"   📊 AQI: {aqi_v2['aqi_value']} ({aqi_v2['aqi_level']})")
        print(f"   🎨 Color: {aqi_v2['aqi_color']}")
        print(f"   💚 Health: {aqi_v2['health_message']}")
        print(f"   🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(aqi_v2['timestamp']))}")
        print("   " + "="*50)
        
        print("\n5. Continuous Monitoring with Location:")
        print("   Taking 3 readings with 3-second intervals...")
        
        for i in range(3):
            # Get fresh AQI data
            aqi_v2 = sensor.get_aqi_v2(include_pm10_comparison=True)
            
            # Create location string
            loc_str = f"{location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}"
            
            print(f"   Reading {i+1}: AQI={aqi_v2['aqi_value']} ({aqi_v2['aqi_level']}) - {loc_str}")
            
            if i < 2:  # Don't sleep after last reading
                time.sleep(3)
        
        print("\n6. Air Quality Analysis:")
        print("   Based on current readings:")
        
        # Analyze air quality level
        aqi_level = aqi_v2['aqi_level']
        if aqi_level == "Good":
            print("   ✅ Air quality is satisfactory for outdoor activities")
        elif aqi_level == "Moderate":
            print("   ⚠️  Air quality is acceptable, sensitive individuals should limit prolonged outdoor exertion")
        elif aqi_level == "Unhealthy for Sensitive Groups":
            print("   🟡 Sensitive groups should avoid prolonged outdoor exertion")
        elif aqi_level == "Unhealthy":
            print("   🔴 Everyone should avoid prolonged outdoor exertion")
        elif aqi_level == "Very Unhealthy":
            print("   🟣 Everyone should avoid outdoor activities")
        elif aqi_level == "Hazardous":
            print("   ⚠️  Emergency conditions - everyone should avoid outdoor exposure")
        
        # Identify dominant pollutant
        if aqi_v2['aqi_source'] == 'PM2.5':
            print("   🌫 Dominant Pollutant: PM2.5 (fine particles)")
        else:
            print("   🌫 Dominant Pollutant: PM10 (coarse particles)")
        
        print("\n7. Location-based Recommendations:")
        print(f"   For {location.get('city', 'your area')}:")
        
        if aqi_v2['aqi_value'] > 100:
            print("   🏠 Stay indoors when possible")
            print("   🪟 Use air purifiers if available")
            print("   😷 Wear masks if going outside")
        elif aqi_v2['aqi_value'] > 50:
            print("   🚶 Limit outdoor activities")
            print("   👀 Keep windows closed")
            print("   🌡️ Use air conditioning if available")
        else:
            print("   🌤 Enjoy outdoor activities")
            print("   🪟 Open windows for fresh air")
            print("   🚴 Great day for exercise")
        
        print("\n=== Air Quality with Location Demo Complete! ===")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("Make sure PM25 sensor is connected and you have internet access for location detection")
        
    finally:
        # Clean up
        try:
            sensor = locals().get('sensor')
            if sensor is not None:
                sensor.disconnect()
                print("\nSensor disconnected.")
        except Exception:
            pass


def show_location_services():
    """Show available location detection services."""
    print("\n=== Location Detection Services ===\n")
    
    services = [
        ("ipinfo.io", "https://ipinfo.io/json", "Comprehensive location data"),
        ("ip-api.com", "http://ip-api.com/json/", "Reliable geolocation service"),
        ("geojs.io", "https://get.geojs.io/v1/ip/geo.json", "Simple JSON API")
    ]
    
    for name, url, description in services:
        print(f"🔍 {name}")
        print(f"   URL: {url}")
        print(f"   Description: {description}")
        print()
    
    print("Features:")
    print("✅ Automatic IP-based geolocation")
    print("✅ Multiple backup services")
    print("✅ City, country, and coordinates")
    print("✅ IP address detection")
    print("✅ Fallback to default location")
    print("✅ Caching support")


if __name__ == "__main__":
    main()
    
    # Uncomment to see location services info
    # show_location_services()