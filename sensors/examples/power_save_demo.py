"""
PM25 Sensor Power Management Demo

This example demonstrates power management features of the PM25 sensor API.
It shows how to use sleep/wake modes for battery-powered applications.

Features demonstrated:
- Sleep/wake cycles
- Power consumption optimization
- Battery monitoring simulation
- Power management strategies
- Performance vs power trade-offs
"""

import sys
import time
from pathlib import Path
from typing import Dict, List

# Add the apis module to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from apis import PM25Sensor, PM25Config


class PowerManager:
    """Power management demonstration class."""
    
    def __init__(self, config: PM25Config = None):
        """Initialize power manager."""
        self.config = config or PM25Config()
        self.sensor = None
        self.power_stats = {
            'total_cycles': 0,
            'sleep_time': 0.0,
            'active_time': 0.0,
            'readings_during_sleep': 0,
            'readings_during_active': 0,
            'battery_level': 100.0  # Simulated battery
        }
    
    def initialize_sensor(self):
        """Initialize the sensor."""
        print("Initializing PM25 sensor for power management demo...")
        self.sensor = PM25Sensor(config=self.config, auto_connect=True, auto_warmup=True)
        
        if not self.sensor.is_connected():
            print("ERROR: Failed to connect to sensor!")
            return False
        
        print(f"Sensor connected successfully")
        print(f"Firmware version: {self.sensor.get_firmware_version()}")
        return True
    
    def demo_basic_sleep_wake(self):
        """Demonstrate basic sleep/wake functionality."""
        print("\n=== Basic Sleep/Wake Demo ===")
        
        # Take baseline reading while awake
        print("\n1. Taking baseline reading (awake)...")
        baseline_reading = self.sensor.get_pm2_5_standard()
        baseline_time = time.time()
        print(f"   Baseline PM2.5: {baseline_reading} μg/m³")
        
        # Enter sleep mode
        print("\n2. Entering sleep mode...")
        sleep_start = time.time()
        sleep_result = self.sensor.enter_sleep_mode()
        
        if sleep_result:
            print(f"   Sleep mode activated successfully")
            print(f"   Sensor sleeping: {self.sensor.is_sleeping()}")
            
            # Try reading while sleeping
            print("\n3. Attempting reading while sleeping...")
            try:
                sleep_reading = self.sensor.get_pm2_5_standard()
                print(f"   Reading during sleep: {sleep_reading} μg/m³")
                self.power_stats['readings_during_sleep'] += 1
            except Exception as e:
                print(f"   Expected error during sleep: {type(e).__name__}")
            
            # Wait in sleep mode
            sleep_duration = 5
            print(f"   Sleeping for {sleep_duration} seconds...")
            time.sleep(sleep_duration)
            
            # Wake from sleep
            print("\n4. Waking from sleep...")
            wake_start = time.time()
            wake_result = self.sensor.wake_from_sleep()
            
            if wake_result:
                print(f"   Wake successful")
                print(f"   Sensor sleeping: {self.sensor.is_sleeping()}")
                
                # Allow stabilization time
                time.sleep(2)
                
                # Take reading after wake
                print("\n5. Taking reading after wake...")
                wake_reading = self.sensor.get_pm2_5_standard()
                wake_time = time.time()
                print(f"   Post-wake PM2.5: {wake_reading} μg/m³")
                
                # Compare readings
                reading_diff = abs(wake_reading - baseline_reading)
                print(f"   Reading difference: {reading_diff} μg/m³")
                
                # Update statistics
                self.power_stats['total_cycles'] += 1
                self.power_stats['sleep_time'] += wake_start - sleep_start
                self.power_stats['active_time'] += wake_time - wake_start
                self.power_stats['readings_during_active'] += 1
                
            else:
                print("   ERROR: Failed to wake from sleep")
        else:
            print("   ERROR: Failed to enter sleep mode")
    
    def demo_power_cycle(self):
        """Demonstrate complete power cycle."""
        print("\n=== Power Cycle Demo ===")
        
        print("\n1. Performing complete power cycle...")
        cycle_start = time.time()
        
        # Take pre-cycle reading
        pre_cycle_reading = self.sensor.get_pm2_5_standard()
        print(f"   Pre-cycle PM2.5: {pre_cycle_reading} μg/m³")
        
        # Perform power cycle
        cycle_result = self.sensor.perform_power_cycle(sleep_duration=3.0)
        
        if cycle_result:
            print("   Power cycle completed successfully")
            
            # Take post-cycle reading
            post_cycle_reading = self.sensor.get_pm2_5_standard()
            cycle_time = time.time()
            print(f"   Post-cycle PM2.5: {post_cycle_reading} μg/m³")
            
            # Compare readings
            reading_diff = abs(post_cycle_reading - pre_cycle_reading)
            print(f"   Reading difference: {reading_diff} μg/m³")
            
            # Update statistics
            self.power_stats['total_cycles'] += 1
            self.power_stats['sleep_time'] += 3.0  # Power cycle includes 3s sleep
            self.power_stats['active_time'] += cycle_time - cycle_start - 3.0
            self.power_stats['readings_during_active'] += 1
            
        else:
            print("   ERROR: Power cycle failed")
    
    def demo_battery_optimization(self):
        """Demonstrate battery-optimized operation."""
        print("\n=== Battery Optimization Demo ===")
        
        # Simulate battery operation
        initial_battery = self.power_stats['battery_level']
        print(f"\nInitial battery level: {initial_battery:.1f}%")
        
        # Strategy 1: Aggressive power saving
        print("\n1. Testing aggressive power saving...")
        self._test_power_strategy("aggressive", sleep_duration=10, active_duration=5)
        
        # Strategy 2: Moderate power saving
        print("\n2. Testing moderate power saving...")
        self._test_power_strategy("moderate", sleep_duration=5, active_duration=10)
        
        # Strategy 3: Minimal power saving
        print("\n3. Testing minimal power saving...")
        self._test_power_strategy("minimal", sleep_duration=2, active_duration=15)
        
        # Show battery consumption comparison
        final_battery = self.power_stats['battery_level']
        battery_used = initial_battery - final_battery
        print(f"\nBattery consumption: {battery_used:.1f}%")
        print(f"Final battery level: {final_battery:.1f}%")
    
    def _test_power_strategy(self, strategy_name: str, sleep_duration: int, active_duration: int):
        """Test a specific power management strategy."""
        print(f"\n   Strategy: {strategy_name}")
        print(f"   Sleep duration: {sleep_duration}s")
        print(f"   Active duration: {active_duration}s")
        
        strategy_cycles = 3
        for cycle in range(strategy_cycles):
            print(f"\n   Cycle {cycle + 1}:")
            
            # Active phase
            active_start = time.time()
            readings_taken = 0
            
            while time.time() - active_start < active_duration:
                try:
                    reading = self.sensor.get_pm2_5_standard()
                    readings_taken += 1
                    self.power_stats['readings_during_active'] += 1
                    time.sleep(1)
                except Exception as e:
                    print(f"     Reading error: {e}")
            
            active_time = time.time() - active_start
            print(f"     Active phase: {active_time:.1f}s, {readings_taken} readings")
            
            # Sleep phase
            sleep_start = time.time()
            sleep_result = self.sensor.enter_sleep_mode()
            
            if sleep_result:
                print(f"     Entered sleep mode")
                time.sleep(sleep_duration)
                
                wake_result = self.sensor.wake_from_sleep()
                if wake_result:
                    print(f"     Woke from sleep")
                    time.sleep(1)  # Stabilization
                else:
                    print(f"     Failed to wake")
            else:
                print(f"     Failed to enter sleep")
            
            sleep_time = time.time() - sleep_start
            self.power_stats['sleep_time'] += sleep_time
            self.power_stats['active_time'] += active_time
            
            # Simulate battery consumption
            self._simulate_battery_consumption(active_time, sleep_time)
    
    def _simulate_battery_consumption(self, active_time: float, sleep_time: float):
        """Simulate battery consumption based on power states."""
        # Assumed consumption rates (arbitrary units)
        ACTIVE_CONSUMPTION = 0.1  # % per second when active
        SLEEP_CONSUMPTION = 0.01   # % per second when sleeping
        
        battery_used = (active_time * ACTIVE_CONSUMPTION) + (sleep_time * SLEEP_CONSUMPTION)
        self.power_stats['battery_level'] = max(0, self.power_stats['battery_level'] - battery_used)
    
    def demo_power_consumption_analysis(self):
        """Analyze power consumption patterns."""
        print("\n=== Power Consumption Analysis ===")
        
        if self.power_stats['total_cycles'] == 0:
            print("No power cycles to analyze.")
            return
        
        # Calculate statistics
        total_time = self.power_stats['sleep_time'] + self.power_stats['active_time']
        sleep_percentage = (self.power_stats['sleep_time'] / total_time) * 100 if total_time > 0 else 0
        active_percentage = (self.power_stats['active_time'] / total_time) * 100 if total_time > 0 else 0
        
        total_readings = (self.power_stats['readings_during_active'] + 
                         self.power_stats['readings_during_sleep'])
        
        print(f"\nPower Management Statistics:")
        print(f"   Total cycles: {self.power_stats['total_cycles']}")
        print(f"   Total time: {total_time:.1f}s")
        print(f"   Sleep time: {self.power_stats['sleep_time']:.1f}s ({sleep_percentage:.1f}%)")
        print(f"   Active time: {self.power_stats['active_time']:.1f}s ({active_percentage:.1f}%)")
        print(f"   Total readings: {total_readings}")
        print(f"   Readings during active: {self.power_stats['readings_during_active']}")
        print(f"   Readings during sleep: {self.power_stats['readings_during_sleep']}")
        
        if self.power_stats['active_time'] > 0:
            reading_rate = self.power_stats['readings_during_active'] / self.power_stats['active_time']
            print(f"   Reading rate (active): {reading_rate:.2f} readings/second")
        
        # Power efficiency
        if total_readings > 0:
            energy_per_reading = total_time / total_readings
            print(f"   Energy per reading: {energy_per_reading:.2f} seconds/reading")
        
        # Battery status
        print(f"\nBattery Status:")
        print(f"   Current level: {self.power_stats['battery_level']:.1f}%")
        
        if self.power_stats['battery_level'] < 20:
            print("   ⚠️  LOW BATTERY WARNING")
        elif self.power_stats['battery_level'] < 50:
            print("   ⚠️  Battery below 50%")
    
    def demo_automatic_power_management(self):
        """Demonstrate automatic power management based on conditions."""
        print("\n=== Automatic Power Management Demo ===")
        
        # Simulate different environmental conditions
        conditions = [
            {"name": "Clean Air", "pm25_threshold": 12, "reading_interval": 60},
            {"name": "Moderate Pollution", "pm25_threshold": 35, "reading_interval": 30},
            {"name": "High Pollution", "pm25_threshold": 55, "reading_interval": 15},
            {"name": "Very High Pollution", "pm25_threshold": 150, "reading_interval": 5}
        ]
        
        for condition in conditions:
            print(f"\nTesting condition: {condition['name']}")
            print(f"PM2.5 threshold: {condition['pm25_threshold']} μg/m³")
            print(f"Reading interval: {condition['reading_interval']} seconds")
            
            # Simulate readings for this condition
            for i in range(3):
                try:
                    reading = self.sensor.get_pm2_5_standard()
                    print(f"   Reading {i+1}: PM2.5 = {reading} μg/m³")
                    
                    # Automatic power management decision
                    if reading <= condition['pm25_threshold']:
                        print(f"   → Air quality good, using power saving")
                        self.sensor.enter_sleep_mode()
                        time.sleep(min(10, condition['reading_interval'] / 2))
                        self.sensor.wake_from_sleep()
                        time.sleep(2)
                    else:
                        print(f"   → Air quality poor, staying active")
                        time.sleep(condition['reading_interval'])
                    
                except Exception as e:
                    print(f"   Error: {e}")
                    break
    
    def cleanup(self):
        """Clean up resources."""
        if self.sensor:
            try:
                self.sensor.disconnect()
                print("\nSensor disconnected.")
            except Exception:
                pass


def main():
    """Main function for power management demo."""
    print("PM25 Sensor Power Management Demo")
    print("=================================\n")
    
    # Configuration optimized for power management
    config_dict = {
        "i2c": {
            "bus": 1,
            "address": 0x19,
            "timeout": 3.0,
            "max_retries": 2
        },
        "sensor": {
            "warmup_time": 3,
            "enable_validation": True
        },
        "performance": {
            "cache_timeout": 1.0
        }
    }
    
    config = PM25Config(config_dict)
    power_manager = PowerManager(config)
    
    try:
        # Initialize sensor
        if not power_manager.initialize_sensor():
            return
        
        # Run demonstrations
        power_manager.demo_basic_sleep_wake()
        time.sleep(2)
        
        power_manager.demo_power_cycle()
        time.sleep(2)
        
        power_manager.demo_battery_optimization()
        time.sleep(2)
        
        power_manager.demo_automatic_power_management()
        time.sleep(2)
        
        # Final analysis
        power_manager.demo_power_consumption_analysis()
        
        print("\n=== Power Management Demo Complete ===")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nERROR: {e}")
    finally:
        power_manager.cleanup()


def demo_power_strategies():
    """Compare different power management strategies."""
    print("\n=== Power Strategy Comparison ===\n")
    
    strategies = {
        "Always On": {"sleep_ratio": 0.0, "reading_frequency": 1.0},
        "Conservative": {"sleep_ratio": 0.3, "reading_frequency": 0.8},
        "Balanced": {"sleep_ratio": 0.5, "reading_frequency": 0.6},
        "Aggressive": {"sleep_ratio": 0.7, "reading_frequency": 0.4},
        "Maximum Savings": {"sleep_ratio": 0.9, "reading_frequency": 0.2}
    }
    
    print("Power Strategy Comparison:")
    print("-" * 60)
    print(f"{'Strategy':<15} {'Sleep %':<8} {'Readings/h':<12} {'Battery Life':<12}")
    print("-" * 60)
    
    for strategy, params in strategies.items():
        sleep_ratio = params["sleep_ratio"]
        reading_freq = params["reading_frequency"]
        
        # Calculate estimated battery life (arbitrary units)
        base_battery_life = 24  # hours when always on
        battery_life = base_battery_life / (1 - sleep_ratio * 0.8)  # Sleep saves 80% power
        
        readings_per_hour = reading_freq * 60  # readings per hour
        
        print(f"{strategy:<15} {sleep_ratio*100:>7.0f}% {readings_per_hour:>11.0f} {battery_life:>11.1f}h")
    
    print("-" * 60)


if __name__ == "__main__":
    main()
    
    # Uncomment to see strategy comparison
    # demo_power_strategies()