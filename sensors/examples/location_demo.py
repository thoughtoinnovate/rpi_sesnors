"""
Location Detection Demo

This example demonstrates the location detection functionality integrated with PM25 sensor API.
Shows automatic IP-based geolocation and manual location setting with air quality data.
"""

import sys
import time
from pathlib import Path

# Add the apis module to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from apis import PM25Sensor, LocationDetector, detect_location, set_location


def main():
    """Main function demonstrating location detection with PM25 sensor."""
    print("=== Location Detection Demo ===\n")
    
    try:
        # Initialize sensor
        print("1. Initializing PM25 sensor...")
        sensor = PM25Sensor(auto_connect=True, auto_warmup=True)
        
        # Check sensor status
        status = sensor.get_sensor_status()
        print(f"   Connected: {status['is_connected']}")
        print(f"   Initialized: {status['is_initialized']}")
        
        if not status['is_connected']:
            print("   ERROR: Sensor not connected!")
            return
        
        print("\n2. Automatic Location Detection:")
        try:
            # Detect location automatically
            location = sensor.get_location()
            print(f"   Location: {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}")
            print(f"   Coordinates: {location['latitude']:.4f}, {location['longitude']:.4f}")
            print(f"   Source: {location['source']}")
            print(f"   IP: {location.get('ip', 'Unknown')}")
            
        except Exception as e:
            print(f"   ERROR detecting location: {e}")
        
        print("\n3. Air Quality with Location:")
        try:
            # Get air quality with location
            aqi_with_location = sensor.get_air_quality_with_location(include_location=True)
            
            # Air quality data
            aq = aqi_with_location["air_quality"]
            print(f"   PM2.5: {aq['pm25_atmospheric']} μg/m³")
            print(f"   PM10: {aq['pm10_atmospheric']} μg/m³")
            print(f"   AQI: {aq['aqi_value']} ({aq['aqi_level']})")
            print(f"   Color: {aq['aqi_color']}")
            print(f"   Health: {aq['health_message']}")
            
            # Location data
            if "location" in aqi_with_location:
                loc = aqi_with_location["location"]
                if "error" in loc:
                    print(f"   Location Error: {loc['error']}")
                else:
                    print(f"   Location: {loc.get('city', 'Unknown')}, {loc.get('country', 'Unknown')}")
                    print(f"   Coordinates: {loc['latitude']:.4f}, {loc['longitude']:.4f}")
            
            # Sensor info
            sensor_info = aqi_with_location["sensor_info"]
            print(f"   Sensor Status: {sensor_info['status']}")
            print(f"   Firmware: {sensor_info.get('firmware_version', 'Unknown')}")
            
        except Exception as e:
            print(f"   ERROR getting air quality with location: {e}")
        
        print("\n4. Manual Location Setting:")
        try:
            # Set manual location (San Francisco)
            manual_location = sensor.set_manual_location(
                latitude=37.7749,
                longitude=-122.4194,
                city="San Francisco",
                country="United States"
            )
            print(f"   Set location to: {manual_location['city']}, {manual_location['country']}")
            print(f"   Coordinates: {manual_location['latitude']:.4f}, {manual_location['longitude']:.4f}")
            print(f"   Source: {manual_location['source']}")
            
            # Get location string
            location_str = sensor.get_location_string()
            print(f"   Location string: {location_str}")
            
        except Exception as e:
            print(f"   ERROR setting manual location: {e}")
        
        print("\n5. Location-based Air Quality Monitoring:")
        try:
            print("   Taking 3 readings with location data:")
            for i in range(3):
                aqi_with_loc = sensor.get_air_quality_with_location(include_location=True)
                aq = aqi_with_loc["air_quality"]
                
                if "location" in aqi_with_loc and "error" not in aqi_with_loc["location"]:
                    loc = aqi_with_loc["location"]
                    location_info = f" ({loc.get('city', 'Unknown')})"
                else:
                    location_info = " (Location unknown)"
                
                print(f"   Reading {i+1}: AQI={aq['aqi_value']} ({aq['aqi_level']}){location_info}")
                
                if i < 2:  # Don't sleep after last reading
                    time.sleep(2)
                    
        except Exception as e:
            print(f"   ERROR in location-based monitoring: {e}")
        
        print("\n6. Location Detection Services Test:")
        try:
            # Test location detector directly
            detector = LocationDetector()
            print("   Testing location detection services...")
            
            location = detector.detect_location_by_ip()
            print(f"   ✅ Location detected: {location.get('city', 'Unknown')}")
            print(f"   ✅ Coordinates: {location['latitude']:.4f}, {location['longitude']:.4f}")
            print(f"   ✅ Service used: {location['source']}")
            
        except Exception as e:
            print(f"   ❌ Location detection failed: {e}")
        
        print("\n=== Location detection demo completed! ===")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("Make sure the PM25 sensor is connected and you have internet access for location detection")
        
    finally:
        # Clean up
        try:
            sensor = locals().get('sensor')
            if sensor is not None:
                sensor.disconnect()
                print("\nSensor disconnected.")
        except Exception:
            pass


def test_location_functions():
    """Test location detection functions directly."""
    print("\n=== Direct Location Functions Test ===\n")
    
    print("1. Automatic Location Detection:")
    try:
        location = detect_location()
        print(f"   Location: {location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}")
        print(f"   Coordinates: {location['latitude']:.4f}, {location['longitude']:.4f}")
        print(f"   Source: {location['source']}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n2. Manual Location Setting:")
    try:
        manual_loc = set_location(40.7128, -74.0060, "New York", "United States")
        print(f"   Set location: {manual_loc['city']}, {manual_loc['country']}")
        print(f"   Coordinates: {manual_loc['latitude']:.4f}, {manual_loc['longitude']:.4f}")
        print(f"   Source: {manual_loc['source']}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n3. Location Detector Features:")
    try:
        detector = LocationDetector()
        
        # Get coordinates
        lat, lon = detector.get_coordinates()
        print(f"   Coordinates: {lat:.4f}, {lon:.4f}")
        
        # Get location string
        loc_str = detector.get_location_string()
        print(f"   Location string: {loc_str}")
        
        # Calculate distance from New York
        distance = detector.calculate_distance(40.7128, -74.0060)
        print(f"   Distance from New York: {distance:.1f} km")
        
    except Exception as e:
        print(f"   ERROR: {e}")


def demonstrate_location_caching():
    """Demonstrate location caching functionality."""
    print("\n=== Location Caching Demo ===\n")
    
    try:
        # Create detector with cache file
        cache_file = "location_cache.json"
        detector = LocationDetector(cache_file=cache_file)
        
        print("1. First location detection (from network):")
        location1 = detector.get_location()
        print(f"   Location: {location1.get('city', 'Unknown')}")
        print(f"   Source: {location1['source']}")
        
        print("\n2. Second location detection (from cache):")
        location2 = detector.get_location()
        print(f"   Location: {location2.get('city', 'Unknown')}")
        print(f"   Source: {location2['source']}")
        
        print("\n3. Force refresh location detection:")
        location3 = detector.get_location(force_refresh=True)
        print(f"   Location: {location3.get('city', 'Unknown')}")
        print(f"   Source: {location3['source']}")
        
        # Clean up cache file
        import os
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"\n   Cache file {cache_file} cleaned up")
            
    except Exception as e:
        print(f"   ERROR: {e}")


if __name__ == "__main__":
    main()
    
    # Uncomment to see additional demonstrations
    # test_location_functions()
    # demonstrate_location_caching()