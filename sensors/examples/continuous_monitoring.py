"""
Continuous PM25 Sensor Monitoring Example

This example demonstrates real-world continuous monitoring with the PM25 sensor.
It shows how to implement long-term monitoring with data logging, analysis, and power management.

Features demonstrated:
- Continuous monitoring loop
- Data logging to file
- Real-time data analysis
- Power management for battery operation
- Error handling and recovery
- Performance monitoring
"""

import sys
import time
import json
import csv
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add the apis module to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from apis import PM25Sensor, PM25Config


class ContinuousMonitor:
    """Continuous monitoring class for PM25 sensor."""
    
    def __init__(self, config = None):
        """Initialize continuous monitor."""
        self.config = config if config is not None else PM25Config({})
        self.sensor = None
        self.running = False
        self.data_log: List[Dict[str, Any]] = []
        
        # Monitoring parameters
        self.reading_interval = self.config.get("monitoring.interval", 30.0)  # seconds
        self.log_file = self.config.get("monitoring.log_file", "pm25_data.json")
        self.enable_power_save = self.config.get("monitoring.enable_power_save", False)
        self.power_save_duration = self.config.get("monitoring.power_save_duration", 300.0)  # seconds
        
        # Statistics
        self.start_time = None
        self.total_readings = 0
        self.total_errors = 0
        
        # Signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
    
    def start_monitoring(self, duration_minutes = None):
        """Start continuous monitoring."""
        print("=== PM25 Continuous Monitoring ===\n")
        
        try:
            # Initialize sensor
            print("Initializing PM25 sensor...")
            self.sensor = PM25Sensor(config=self.config, auto_connect=True, auto_warmup=True)
            
            if not self.sensor.is_connected():
                print("ERROR: Failed to connect to sensor!")
                return
            
            print(f"Sensor connected successfully")
            print(f"Firmware version: {self.sensor.get_firmware_version()}")
            
            # Setup monitoring
            self.running = True
            self.start_time = time.time()
            
            if duration_minutes is not None:
                end_time = self.start_time + (duration_minutes * 60)
                print(f"Monitoring for {duration_minutes} minutes...")
            else:
                end_time = None
                print("Monitoring indefinitely (Ctrl+C to stop)...")
            
            print(f"Reading interval: {self.reading_interval} seconds")
            print(f"Log file: {self.log_file}")
            print(f"Power save: {'Enabled' if self.enable_power_save else 'Disabled'}")
            print("\nStarting monitoring...")
            print("-" * 80)
            
            # Main monitoring loop
            while self.running:
                loop_start = time.time()
                
                try:
                    # Check if monitoring duration exceeded
                    if end_time is not None and time.time() >= end_time:
                        print("Monitoring duration completed.")
                        break
                    
                    # Take reading
                    reading = self._take_reading()
                    
                    if reading:
                        self.total_readings += 1
                        self._process_reading(reading)
                        
                        # Periodic status update
                        if self.total_readings % 10 == 0:
                            self._print_status()
                    
                    # Power management
                    if self.enable_power_save:
                        self._handle_power_save()
                    
                    # Calculate sleep time
                    loop_time = time.time() - loop_start
                    sleep_time = max(0, self.reading_interval - loop_time)
                    
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                
                except KeyboardInterrupt:
                    print("\nMonitoring interrupted by user.")
                    break
                except Exception as e:
                    self.total_errors += 1
                    print(f"ERROR in monitoring loop: {e}")
                    time.sleep(5)  # Wait before retrying
            
            # Final status and cleanup
            self._print_final_status()
            self._save_data()
            
        except Exception as e:
            print(f"FATAL ERROR: {e}")
        finally:
            self._cleanup()
    
    def _take_reading(self):
        """Take a complete sensor reading."""
        try:
            if self.sensor is None:
                print("ERROR: Sensor not initialized")
                return None
                
            # Wake sensor if in power save mode
            if self.sensor.is_sleeping():
                self.sensor.wake_from_sleep()
                time.sleep(2)  # Allow time to wake up
            
            # Get complete reading
            reading = self.sensor.get_complete_reading(use_cache=False)
            
            # Add monitoring metadata
            reading["monitoring_timestamp"] = time.time()
            reading["monitoring_datetime"] = datetime.now().isoformat()
            reading["reading_number"] = self.total_readings + 1
            
            return reading
            
        except Exception as e:
            print(f"ERROR taking reading: {e}")
            return None
    
    def _process_reading(self, reading: Dict[str, Any]):
        """Process and display a reading."""
        # Extract key values
        timestamp = reading["monitoring_datetime"]
        pm25 = reading["concentrations"]["standard"]["PM2.5"]
        pm10 = reading["concentrations"]["standard"]["PM10"]
        aqi_level = reading["air_quality_index"]["aqi_level"]
        aqi_value = reading["air_quality_index"]["aqi_value"]
        dominant_particle = reading["particle_analysis"]["dominant_size"]
        total_particles = reading["particle_analysis"]["total_particles"]
        
        # Display reading
        print(f"{timestamp} | PM2.5: {pm25:3d} μg/m³ | PM10: {pm10:3d} μg/m³ | "
              f"AQI: {aqi_level} ({aqi_value}) | "
              f"Dominant: {dominant_particle} | Total: {total_particles:6d}")
        
        # Store in log
        self.data_log.append(reading)
        
        # Check for alerts
        self._check_alerts(reading)
    
    def _check_alerts(self, reading: Dict[str, Any]):
        """Check for air quality alerts."""
        pm25 = reading["concentrations"]["standard"]["PM2.5"]
        aqi_level = reading["air_quality_index"]["aqi_level"]
        
        # PM2.5 alerts
        if pm25 > 150:
            print(f"  ⚠️  ALERT: Very high PM2.5 level: {pm25} μg/m³")
        elif pm25 > 100:
            print(f"  ⚠️  WARNING: High PM2.5 level: {pm25} μg/m³")
        
        # AQI alerts
        if aqi_level in ["Unhealthy", "Very Unhealthy", "Hazardous"]:
            print(f"  ⚠️  AIR QUALITY ALERT: {aqi_level}")
        elif aqi_level == "Unhealthy for Sensitive Groups":
            print(f"  ⚠️  Air quality caution: {aqi_level}")
    
    def _handle_power_save(self):
        """Handle power saving mode."""
        # Simple power save: sleep between readings
        if self.total_readings > 0 and self.total_readings % 5 == 0:
            print("  Entering power save mode...")
            if self.sensor is not None:
                self.sensor.enter_sleep_mode()
                time.sleep(min(10, self.reading_interval / 2))
                self.sensor.wake_from_sleep()
                time.sleep(2)  # Allow wake up time
    
    def _print_status(self):
        """Print monitoring status."""
        if self.start_time:
            elapsed = time.time() - self.start_time
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            
            print(f"\n--- Status Update ---")
            print(f"Elapsed: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
            print(f"Readings: {self.total_readings}")
            print(f"Errors: {self.total_errors}")
            
            if self.total_readings > 0:
                error_rate = (self.total_errors / (self.total_readings + self.total_errors)) * 100
                print(f"Error rate: {error_rate:.1f}%")
            
            # Sensor statistics
            if self.sensor is not None:
                stats = self.sensor.get_performance_statistics()
                print(f"I2C Success Rate: {stats['i2c_statistics']['success_rate']:.1%}")
                cache_info = stats.get('cache_info', {}).get('concentration_cache', {})
                cache_valid = cache_info.get('0x07', {}).get('valid', 'N/A')
                print(f"Cache hits: {cache_valid}")
            print("---------------------\n")
    
    def _print_final_status(self):
        """Print final monitoring statistics."""
        print("\n" + "=" * 80)
        print("MONITORING COMPLETE")
        print("=" * 80)
        
        if self.start_time:
            elapsed = time.time() - self.start_time
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            
            print(f"Total monitoring time: {int(hours)}h {int(minutes)}m")
            print(f"Total readings: {self.total_readings}")
            print(f"Total errors: {self.total_errors}")
            
            if self.total_readings > 0:
                error_rate = (self.total_errors / (self.total_readings + self.total_errors)) * 100
                print(f"Overall error rate: {error_rate:.1f}%")
                
                # Data analysis
                pm25_values = [r["concentrations"]["standard"]["PM2.5"] for r in self.data_log]
                if pm25_values:
                    avg_pm25 = sum(pm25_values) / len(pm25_values)
                    max_pm25 = max(pm25_values)
                    min_pm25 = min(pm25_values)
                    
                    print(f"PM2.5 Statistics:")
                    print(f"  Average: {avg_pm25:.1f} μg/m³")
                    print(f"  Maximum: {max_pm25} μg/m³")
                    print(f"  Minimum: {min_pm25} μg/m³")
                    
                    # Air quality distribution
                    aqi_levels = [r["air_quality_index"]["aqi_level"] for r in self.data_log]
                    aqi_counts = {}
                    for level in aqi_levels:
                        aqi_counts[level] = aqi_counts.get(level, 0) + 1
                    
                    print(f"Air Quality Distribution:")
                    for level, count in sorted(aqi_counts.items()):
                        percentage = (count / len(aqi_levels)) * 100
                        print(f"  {level}: {count} ({percentage:.1f}%)")
        
        print("=" * 80)
    
    def _save_data(self):
        """Save logged data to file."""
        if not self.data_log:
            print("No data to save.")
            return
        
        try:
            # Save as JSON
            json_file = Path(self.log_file)
            with open(json_file, 'w') as f:
                json.dump(self.data_log, f, indent=2)
            print(f"Data saved to {json_file}")
            
            # Also save as CSV for easy analysis
            csv_file = json_file.with_suffix('.csv')
            self._save_csv(csv_file)
            
        except Exception as e:
            print(f"ERROR saving data: {e}")
    
    def _save_csv(self, csv_file: Path):
        """Save data as CSV file."""
        try:
            with open(csv_file, 'w', newline='') as f:
                if not self.data_log:
                    return
                
                # Get headers from first reading
                first_reading = self.data_log[0]
                headers = ['timestamp', 'datetime', 'reading_number', 
                          'pm25_standard', 'pm10_standard', 'pm1_0_standard',
                          'pm25_atmospheric', 'pm10_atmospheric', 'pm1_0_atmospheric',
                          'particles_0_3um', 'particles_0_5um', 'particles_1_0um',
                          'particles_2_5um', 'particles_5_0um', 'particles_10um',
                          'aqi_level', 'aqi_value', 'dominant_particle_size', 'total_particles']
                
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                # Write data
                for reading in self.data_log:
                    row = {
                        'timestamp': reading.get('monitoring_timestamp', ''),
                        'datetime': reading.get('monitoring_datetime', ''),
                        'reading_number': reading.get('reading_number', ''),
                        'pm25_standard': reading['concentrations']['standard'].get('PM2.5', ''),
                        'pm10_standard': reading['concentrations']['standard'].get('PM10', ''),
                        'pm1_0_standard': reading['concentrations']['standard'].get('PM1.0', ''),
                        'pm25_atmospheric': reading['concentrations']['atmospheric'].get('PM2.5', ''),
                        'pm10_atmospheric': reading['concentrations']['atmospheric'].get('PM10', ''),
                        'pm1_0_atmospheric': reading['concentrations']['atmospheric'].get('PM1.0', ''),
                        'particles_0_3um': reading['particle_counts'].get('0.3um', ''),
                        'particles_0_5um': reading['particle_counts'].get('0.5um', ''),
                        'particles_1_0um': reading['particle_counts'].get('1.0um', ''),
                        'particles_2_5um': reading['particle_counts'].get('2.5um', ''),
                        'particles_5_0um': reading['particle_counts'].get('5.0um', ''),
                        'particles_10um': reading['particle_counts'].get('10um', ''),
                        'aqi_level': reading['air_quality_index'].get('aqi_level', ''),
                        'aqi_value': reading['air_quality_index'].get('aqi_value', ''),
                        'dominant_particle_size': reading['particle_analysis'].get('dominant_size', ''),
                        'total_particles': reading['particle_analysis'].get('total_particles', '')
                    }
                    writer.writerow(row)
            
            print(f"CSV data saved to {csv_file}")
            
        except Exception as e:
            print(f"ERROR saving CSV: {e}")
    
    def _cleanup(self):
        """Clean up resources."""
        try:
            if self.sensor:
                self.sensor.disconnect()
                print("Sensor disconnected.")
        except Exception:
            pass


def main():
    """Main function for continuous monitoring example."""
    print("PM25 Sensor Continuous Monitoring Example")
    print("=====================================\n")
    
    # Configuration for monitoring
    config_dict = {
        "i2c": {
            "bus": 1,
            "address": 0x19,
            "timeout": 5.0,
            "max_retries": 3
        },
        "sensor": {
            "warmup_time": 5,
            "enable_validation": True
        },
        "monitoring": {
            "interval": 10.0,  # Read every 10 seconds
            "log_file": "pm25_continuous_monitoring.json",
            "enable_power_save": False,  # Set to True for battery operation
            "power_save_duration": 60.0
        },
        "performance": {
            "cache_timeout": 2.0
        },
        "logging": {
            "level": "INFO"
        }
    }
    
    config = PM25Config(config_dict)
    
    # Create and start monitor
    monitor = ContinuousMonitor(config)
    
    # Monitor for 5 minutes (set to None for indefinite)
    monitor.start_monitoring(duration_minutes=5)


def demo_power_saving():
    """Demonstrate power saving mode."""
    print("\n=== Power Saving Demo ===\n")
    
    # Configuration with power saving
    config_dict = {
        "monitoring": {
            "interval": 5.0,
            "enable_power_save": True,
            "log_file": "pm25_power_save.json"
        }
    }
    
    config = PM25Config(config_dict)
    monitor = ContinuousMonitor(config)
    
    # Monitor for 2 minutes with power saving
    monitor.start_monitoring(duration_minutes=2)


if __name__ == "__main__":
    main()
    
    # Uncomment to see power saving demo
    # demo_power_saving()