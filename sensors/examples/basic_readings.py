"""
Basic PM25 Sensor Readings Example

This example demonstrates basic functionality of the PM25 sensor API.
It shows how to initialize the sensor and read various air quality parameters.

Features demonstrated:
- Sensor initialization
- PM concentration readings
- Particle count readings
- Basic error handling
- Sensor status checking
"""

import sys
import time
from pathlib import Path

# Add the apis module to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from apis import PM25Sensor, PM25Config


def main():
    """Main function demonstrating basic sensor readings."""
    print("=== PM25 Sensor Basic Readings Example ===\n")
    
    try:
        # Create sensor with default configuration
        print("1. Initializing PM25 sensor...")
        sensor = PM25Sensor(auto_connect=True, auto_warmup=True)
        
        # Check sensor status
        print("2. Checking sensor status...")
        status = sensor.get_sensor_status()
        print(f"   Connected: {status['is_connected']}")
        print(f"   Initialized: {status['is_initialized']}")
        print(f"   Sleeping: {status['is_sleeping']}")
        print(f"   Warmed up: {status['is_warmed_up']}")
        
        if status['firmware_version']:
            print(f"   Firmware Version: {status['firmware_version']}")
        
        if not status['is_connected']:
            print("   ERROR: Sensor not connected!")
            return
        
        print("\n3. Taking basic readings...")
        
        # PM Concentration readings
        print("\n   PM Concentrations:")
        try:
            pm1_0 = sensor.get_pm1_0_standard()
            print(f"   PM1.0 (Standard): {pm1_0} μg/m³")
            
            pm2_5 = sensor.get_pm2_5_standard()
            print(f"   PM2.5 (Standard): {pm2_5} μg/m³")
            
            pm10 = sensor.get_pm10_standard()
            print(f"   PM10 (Standard): {pm10} μg/m³")
            
            pm1_0_atm = sensor.get_pm1_0_atmospheric()
            print(f"   PM1.0 (Atmospheric): {pm1_0_atm} μg/m³")
            
            pm2_5_atm = sensor.get_pm2_5_atmospheric()
            print(f"   PM2.5 (Atmospheric): {pm2_5_atm} μg/m³")
            
            pm10_atm = sensor.get_pm10_atmospheric()
            print(f"   PM10 (Atmospheric): {pm10_atm} μg/m³")
            
        except Exception as e:
            print(f"   ERROR reading concentrations: {e}")
        
        # Particle count readings
        print("\n   Particle Counts (per 0.1L):")
        try:
            particles_0_3 = sensor.get_particles_0_3um()
            print(f"   0.3μm particles: {particles_0_3}")
            
            particles_0_5 = sensor.get_particles_0_5um()
            print(f"   0.5μm particles: {particles_0_5}")
            
            particles_1_0 = sensor.get_particles_1_0um()
            print(f"   1.0μm particles: {particles_1_0}")
            
            particles_2_5 = sensor.get_particles_2_5um()
            print(f"   2.5μm particles: {particles_2_5}")
            
            particles_5_0 = sensor.get_particles_5_0um()
            print(f"   5.0μm particles: {particles_5_0}")
            
            particles_10 = sensor.get_particles_10um()
            print(f"   10μm particles: {particles_10}")
            
        except Exception as e:
            print(f"   ERROR reading particle counts: {e}")
        
        print("\n4. Getting air quality summary...")
        try:
            summary = sensor.get_air_quality_summary()
            print(f"   PM2.5: {summary['pm25_standard']} μg/m³")
            print(f"   PM10: {summary['pm10_standard']} μg/m³")
            print(f"   AQI Level: {summary['aqi_level']}")
            print(f"   Health Message: {summary['health_message']}")
            print(f"   Dominant Particle Size: {summary['dominant_particle_size']}")
            print(f"   Total Particles: {summary['total_particles']}")
            print(f"   Sensor Status: {summary['sensor_status']}")
            
        except Exception as e:
            print(f"   ERROR getting air quality summary: {e}")
        
        print("\n5. Performance statistics...")
        try:
            stats = sensor.get_performance_statistics()
            print(f"   Total Readings: {stats['total_readings']}")
            print(f"   Total Errors: {stats['total_errors']}")
            print(f"   Error Rate: {stats['error_rate']:.1f}%")
            print(f"   I2C Success Rate: {stats['i2c_statistics']['success_rate']:.1%}")
            
        except Exception as e:
            print(f"   ERROR getting performance stats: {e}")
        
        print("\n6. Multiple readings test...")
        try:
            print("   Taking 5 readings with 1-second intervals:")
            for i in range(5):
                reading = sensor.get_pm2_5_standard()
                print(f"   Reading {i+1}: PM2.5 = {reading} μg/m³")
                time.sleep(1)
                
        except Exception as e:
            print(f"   ERROR in multiple readings: {e}")
        
        print("\n7. Testing cache functionality...")
        try:
            # First reading (from sensor)
            start_time = time.time()
            reading1 = sensor.get_pm2_5_standard(use_cache=False)
            time1 = time.time() - start_time
            
            # Second reading (from cache)
            start_time = time.time()
            reading2 = sensor.get_pm2_5_standard(use_cache=True)
            time2 = time.time() - start_time
            
            print(f"   First reading (sensor): {reading1} μg/m³ ({time1:.3f}s)")
            print(f"   Second reading (cache): {reading2} μg/m³ ({time2:.3f}s)")
            print(f"   Cache speedup: {time1/time2:.1f}x faster" if time2 > 0 else "   Cache speedup: N/A")
            
        except Exception as e:
            print(f"   ERROR testing cache: {e}")
        
        print("\n=== Basic readings completed successfully! ===")
        
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


def demonstrate_configuration():
    """Demonstrate different configuration options."""
    print("\n=== Configuration Examples ===\n")
    
    # Example 1: Default configuration
    print("1. Default configuration:")
    sensor1 = PM25Sensor()
    print(f"   I2C Bus: {sensor1.config.get('i2c.bus')}")
    print(f"   I2C Address: 0x{sensor1.config.get('i2c.address'):02X}")
    print(f"   Timeout: {sensor1.config.get('i2c.timeout')}s")
    sensor1.disconnect()
    
    # Example 2: Custom configuration
    print("\n2. Custom configuration:")
    config_dict = {
        "i2c": {
            "bus": 1,
            "address": 0x19,
            "timeout": 3.0,
            "max_retries": 5
        },
        "sensor": {
            "warmup_time": 3,
            "enable_validation": True
        },
        "performance": {
            "cache_timeout": 0.5
        }
    }
    
    config = PM25Config(config_dict)
    sensor2 = PM25Sensor(config=config)
    print(f"   I2C Bus: {sensor2.config.get('i2c.bus')}")
    print(f"   Timeout: {sensor2.config.get('i2c.timeout')}s")
    print(f"   Max Retries: {sensor2.config.get('i2c.max_retries')}")
    print(f"   Cache Timeout: {sensor2.config.get('performance.cache_timeout')}s")
    sensor2.disconnect()
    
    # Example 3: Configuration from file (if available)
    print("\n3. Configuration from file:")
    try:
        config = PM25Config.load_from_file("config.json")
        sensor3 = PM25Sensor(config=config)
        print("   Loaded configuration from config.json")
        sensor3.disconnect()
    except Exception:
        print("   config.json not found, using defaults")


def demonstrate_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n=== Error Handling Examples ===\n")
    
    try:
        # Example 1: Invalid I2C address
        print("1. Testing invalid I2C address...")
        invalid_config = PM25Config({"i2c": {"address": 0x99}})
        sensor = PM25Sensor(config=invalid_config, auto_connect=False)
        
        try:
            sensor.initialize()
        except Exception as e:
            print(f"   Caught expected error: {type(e).__name__}: {e}")
        
    except Exception as e:
        print(f"   Error in invalid address test: {e}")
    
    try:
        # Example 2: Using sensor without initialization
        print("\n2. Testing uninitialized sensor...")
        sensor = PM25Sensor(auto_connect=False)
        
        try:
            sensor.get_pm2_5_standard()
        except Exception as e:
            print(f"   Caught expected error: {type(e).__name__}: {e}")
        
    except Exception as e:
        print(f"   Error in uninitialized test: {e}")


if __name__ == "__main__":
    main()
    
    # Uncomment to see additional examples
    # demonstrate_configuration()
    # demonstrate_error_handling()