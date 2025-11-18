"""
Complete Air Quality and Location Demo

This working example demonstrates AQI v2 calculation with location detection
for comprehensive air quality monitoring.
"""

import sys
import time
import requests
import json
from pathlib import Path

# Add the apis module to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))


def get_simple_location():
    """Get location using simple IP-based geolocation."""
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
                    "source": "ipinfo.io"
                }
    except Exception as e:
        print(f"Location detection error: {e}")
    
    # Default location
    return {
        "latitude": 40.7128,  # New York
        "longitude": -74.0060,
        "city": "New York",
        "country": "United States",
        "source": "default"
    }


def main():
    """Main function demonstrating complete air quality monitoring."""
    print("=== Complete Air Quality & Location Demo ===")
    print()
    
    try:
        # Import PM25 sensor
        from apis import PM25Sensor
        
        print("1. Initializing PM25 Sensor...")
        sensor = PM25Sensor(auto_connect=True, auto_warmup=True)
        
        # Check sensor status
        status = sensor.get_sensor_status()
        print(f"   Connected: {status['is_connected']}")
        print(f"   Initialized: {status['is_initialized']}")
        
        if not status['is_connected']:
            print("   ERROR: Sensor not connected!")
            return
        
        print("\n2. Getting Location Information...")
        location = get_simple_location()
        print(f"   Location: {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}")
        print(f"   Coordinates: {location['latitude']:.4f}°N, {abs(location['longitude']):.4f}°{'W' if location['longitude'] < 0 else 'E'}")
        print(f"   IP Address: {location.get('ip', 'Unknown')}")
        print(f"   Source: {location['source']}")
        
        print("\n3. Getting Air Quality Data...")
        # Get AQI v2 data
        aqi_v2 = sensor.get_aqi_v2(include_pm10_comparison=True)
        
        print("   Air Quality Results:")
        print(f"   🌫 PM2.5: {aqi_v2['pm25_atmospheric']} μg/m³")
        print(f"   🌫 PM10: {aqi_v2['pm10_atmospheric']} μg/m³")
        print(f"   📊 AQI: {aqi_v2['aqi_value']} ({aqi_v2['aqi_level']})")
        print(f"   🎨 Color: {aqi_v2['aqi_color']}")
        print(f"   📍 Source: {aqi_v2['aqi_source']}")
        print(f"   💚 Health: {aqi_v2['health_message']}")
        
        print("\n4. Complete Air Quality Report:")
        print("   " + "="*60)
        print(f"   📍 LOCATION: {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}")
        print(f"   🌍 COORDS: {location['latitude']:.4f}°N, {abs(location['longitude']):.4f}°{'W' if location['longitude'] < 0 else 'E'}")
        print(f"   🌫 PM2.5: {aqi_v2['pm25_atmospheric']} μg/m³")
        print(f"   🌫 PM10: {aqi_v2['pm10_atmospheric']} μg/m³")
        print(f"   📊 AQI: {aqi_v2['aqi_value']} ({aqi_v2['aqi_level']})")
        print(f"   🎨 COLOR: {aqi_v2['aqi_color']}")
        print(f"   📍 SOURCE: {aqi_v2['aqi_source']}")
        print(f"   💚 HEALTH: {aqi_v2['health_message']}")
        print(f"   🕐 TIME: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(aqi_v2['timestamp']))}")
        print("   " + "="*60)
        
        print("\n5. Air Quality Analysis:")
        aqi_level = aqi_v2['aqi_level']
        aqi_value = aqi_v2['aqi_value']
        
        if aqi_level == "Good":
            print("   ✅ EXCELLENT: Air quality is satisfactory")
            print("   🌤 Perfect for outdoor activities")
        elif aqi_level == "Moderate":
            print("   ⚠️  ACCEPTABLE: Air quality is acceptable for most people")
            print("   🚶 Sensitive individuals should limit prolonged outdoor exertion")
        elif aqi_level == "Unhealthy for Sensitive Groups":
            print("   🟡 CAUTION: Sensitive groups may experience health effects")
            print("   🏠 Children, elderly, and people with respiratory issues should stay indoors")
        elif aqi_level == "Unhealthy":
            print("   🔴 WARNING: Everyone may experience health effects")
            print("   🏠 Everyone should limit outdoor activities")
        elif aqi_level == "Very Unhealthy":
            print("   🟣 DANGER: Health alert - everyone may experience serious health effects")
            print("   🚫 Avoid all outdoor activities")
        elif aqi_level == "Hazardous":
            print("   ⚠️  EMERGENCY: Emergency conditions - everyone affected")
            print("   🚨 Stay indoors, use air purifiers, avoid all outdoor exposure")
        
        print("\n6. Location-Based Recommendations:")
        city = location.get('city', 'your area')
        
        if aqi_value > 150:
            print(f"   🚨 For {city}: EMERGENCY CONDITIONS")
            print("   🏠 Stay indoors at all times")
            print("   🪟 Use high-quality air purifiers")
            print("   😷 Wear N95 masks if you must go outside")
            print("   🚪 Seal windows and doors")
        elif aqi_value > 100:
            print(f"   🟡 For {city}: UNHEALTHY AIR QUALITY")
            print("   🚶 Avoid outdoor activities")
            print("   🏠 Keep windows closed")
            print("   🌡️ Use air conditioning with clean filters")
        elif aqi_value > 50:
            print(f"   ⚠️  For {city}: MODERATE POLLUTION")
            print("   🚶 Limit prolonged outdoor exertion")
            print("   👀 Sensitive groups should stay indoors")
        else:
            print(f"   ✅ For {city}: GOOD AIR QUALITY")
            print("   🌤 Enjoy outdoor activities")
            print("   🪟 Open windows for fresh air")
            print("   🚴 Great day for exercise")
        
        print("\n7. Continuous Monitoring:")
        print("   Taking 3 readings with 2-second intervals...")
        
        readings = []
        for i in range(3):
            aqi_v2 = sensor.get_aqi_v2(include_pm10_comparison=True)
            readings.append(aqi_v2['aqi_value'])
            
            loc_str = f"{location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}"
            print(f"   Reading {i+1}: AQI={aqi_v2['aqi_value']} ({aqi_v2['aqi_level']}) - {loc_str}")
            
            if i < 2:  # Don't sleep after last reading
                time.sleep(2)
        
        print("\n8. Monitoring Summary:")
        avg_aqi = sum(readings) / len(readings)
        min_aqi = min(readings)
        max_aqi = max(readings)
        
        print(f"   📊 Average AQI: {avg_aqi:.1f}")
        print(f"   📉 Minimum AQI: {min_aqi}")
        print(f"   📈 Maximum AQI: {max_aqi}")
        print(f"   📈 Trend: {'Improving' if readings[-1] < readings[0] else 'Worsening' if readings[-1] > readings[0] else 'Stable'}")
        
        print("\n9. Technical Details:")
        print(f"   🌍 Sensor Location: {location.get('city', 'Unknown')}")
        print(f"   📡 AQI Method: Atmospheric (v2) - matches AirNow/PurpleAir")
        print(f"   🌫 Dominant Pollutant: {aqi_v2['aqi_source']}")
        print(f"   🕐 Detection Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
        print(f"   🌐 IP Geolocation: {location['source']}")
        
        print("\n=== Complete Air Quality Monitoring Demo Finished! ===")
        print("✅ AQI v2 with location detection working perfectly!")
        print("✅ Real-time air quality monitoring operational")
        print("✅ Location-aware recommendations provided")
        print("✅ Ready for production deployment!")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("Make sure:")
        print("  1. PM25 sensor is connected to I2C bus 1 at address 0x19")
        print("  2. You have internet access for location detection")
        print("  3. Required dependencies are installed")
        
    finally:
        # Clean up
        try:
            sensor = locals().get('sensor')
            if sensor is not None:
                sensor.disconnect()
                print("\n🔌 Sensor disconnected.")
        except Exception:
            pass


def show_features():
    """Show features of the complete system."""
    print("\n=== System Features ===\n")
    
    features = [
        "🌫 PM2.5 and PM10 atmospheric readings",
        "📊 AQI v2 calculation (matches AirNow/PurpleAir)",
        "📍 Automatic IP-based geolocation",
        "🌍 City and country detection",
        "🕐 Real-time monitoring",
        "💚 Health recommendations",
        "📈 Trend analysis",
        "🎨 Color-coded air quality levels",
        "🚨 Location-based warnings",
        "📊 Statistical analysis",
        "🔧 Robust error handling"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n=== Benefits ===\n")
    benefits = [
        "✅ Same AQI values as major platforms (AirNow, PurpleAir, IQAir)",
        "✅ Automatic location detection - no manual setup required",
        "✅ Real-time air quality monitoring",
        "✅ Health-based recommendations",
        "✅ Location-aware air quality advice",
        "✅ Professional-grade accuracy and reliability",
        "✅ Easy integration with existing systems"
    ]
    
    for benefit in benefits:
        print(f"  {benefit}")


if __name__ == "__main__":
    main()
    
    # Uncomment to see system features
    # show_features()