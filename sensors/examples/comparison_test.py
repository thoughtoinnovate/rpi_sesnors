"""
PM25 Sensor Comparison Test

This example performs side-by-side comparison between our independent API
and the original DFRobot repository to validate functional parity.
"""

import sys
import os
import time
from pathlib import Path

# Add paths for both APIs
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent

# Add our independent API
sys.path.insert(0, str(current_dir.parent))
from apis import PM25Sensor, PM25Config

# Add DFRobot API for comparison
dfrobot_path = project_root / "DFRobot_AirQualitySensor" / "python" / "raspberrypi"
if dfrobot_path.exists():
    sys.path.insert(0, str(dfrobot_path))
    from DFRobot_AirQualitySensor import DFRobot_AirQualitySensor
    DFRobot_AVAILABLE = True
else:
    print("Warning: DFRobot repository not found for comparison")
    DFRobot_AVAILABLE = False


class ComparisonTester:
    """Class to perform side-by-side comparison testing."""
    
    def __init__(self):
        """Initialize comparison tester."""
        self.results = []
        self.test_count = 0
        self.errors = []
        
        # Configuration for both APIs
        self.config = PM25Config({
            "i2c": {
                "bus": 1,
                "address": 0x19,
                "timeout": 2.0,
                "max_retries": 3
            },
            "sensor": {
                "warmup_time": 5,
                "read_interval": 1
            },
            "logging": {
                "level": "INFO",
                "console": True
            }
        })
        
        # Initialize sensors
        self.api_sensor = PM25Sensor(self.config, auto_connect=False)
        
        if DFRobot_AVAILABLE:
            self.dfrobot_sensor = DFRobot_AirQualitySensor(1, 0x19)
        else:
            self.dfrobot_sensor = None
    
    def run_comparison_test(self, num_readings: int = 10, interval: float = 2.0):
        """
        Run comprehensive comparison test.
        
        Args:
            num_readings: Number of readings to compare
            interval: Time interval between readings
        """
        print("=" * 60)
        print("PM25 Sensor API Comparison Test")
        print("=" * 60)
        
        try:
            # Initialize both sensors
            print("Initializing sensors...")
            self.api_sensor.initialize()
            
            if DFRobot_AVAILABLE:
                print("DFRobot sensor available for comparison")
                # Test DFRobot connection
                try:
                    version = self.dfrobot_sensor.gain_version()
                    print(f"DFRobot firmware version: {version}")
                except Exception as e:
                    print(f"DFRobot sensor error: {e}")
                    self.dfrobot_sensor = None
            else:
                print("DFRobot sensor not available - testing API only")
            
            print("Starting comparison test...")
            print(f"Number of readings: {num_readings}")
            print(f"Interval between readings: {interval}s")
            print("-" * 60)
            
            # Run comparison readings
            for i in range(num_readings):
                self.test_count += 1
                print(f"\nReading {i + 1}/{num_readings}:")
                
                try:
                    # Get readings from both APIs
                    api_reading = self.get_api_reading()
                    dfrobot_reading = self.get_dfrobot_reading() if self.dfrobot_sensor else None
                    
                    # Compare readings
                    comparison = self.compare_readings(api_reading, dfrobot_reading)
                    self.results.append(comparison)
                    
                    # Display results
                    self.display_comparison(comparison)
                    
                except Exception as e:
                    error_msg = f"Reading {i + 1} failed: {e}"
                    print(f"ERROR: {error_msg}")
                    self.errors.append(error_msg)
                
                # Wait between readings
                if i < num_readings - 1:
                    time.sleep(interval)
            
            # Display summary
            self.display_summary()
            
        except Exception as e:
            print(f"Test failed: {e}")
            self.errors.append(str(e))
        
        finally:
            # Cleanup
            try:
                self.api_sensor.disconnect()
            except:
                pass
    
    def get_api_reading(self) -> dict:
        """Get reading from our independent API."""
        try:
            reading = self.api_sensor.get_complete_reading(use_cache=False)
            return {
                "pm1_0_standard": reading["concentrations"]["standard"]["PM1.0"],
                "pm2_5_standard": reading["concentrations"]["standard"]["PM2.5"],
                "pm10_standard": reading["concentrations"]["standard"]["PM10"],
                "particles_0_3um": reading["particle_counts"]["0.3um"],
                "particles_2_5um": reading["particle_counts"]["2.5um"],
                "timestamp": reading["timestamp"],
                "source": "independent_api"
            }
        except Exception as e:
            return {"error": str(e), "source": "independent_api"}
    
    def get_dfrobot_reading(self) -> dict:
        """Get reading from DFRobot API."""
        try:
            # PM concentrations
            pm1_0 = self.dfrobot_sensor.gain_particle_concentration_ugm3(0x05)
            pm2_5 = self.dfrobot_sensor.gain_particle_concentration_ugm3(0x07)
            pm10 = self.dfrobot_sensor.gain_particle_concentration_ugm3(0x09)
            
            # Particle counts
            particles_0_3 = self.dfrobot_sensor.gain_particlenum_every0_1l(0x11)
            particles_2_5 = self.dfrobot_sensor.gain_particlenum_every0_1l(0x17)
            
            return {
                "pm1_0_standard": pm1_0,
                "pm2_5_standard": pm2_5,
                "pm10_standard": pm10,
                "particles_0_3um": particles_0_3,
                "particles_2_5um": particles_2_5,
                "timestamp": time.time(),
                "source": "dfrobot_api"
            }
        except Exception as e:
            return {"error": str(e), "source": "dfrobot_api"}
    
    def compare_readings(self, api_reading: dict, dfrobot_reading: dict) -> dict:
        """Compare readings from both APIs."""
        comparison = {
            "reading_number": self.test_count,
            "timestamp": time.time(),
            "api_reading": api_reading,
            "dfrobot_reading": dfrobot_reading,
            "differences": {},
            "parity_status": "unknown"
        }
        
        # Compare if both readings are valid
        if "error" not in api_reading and "error" not in dfrobot_reading:
            # Compare PM concentrations
            for param in ["pm1_0_standard", "pm2_5_standard", "pm10_standard"]:
                api_val = api_reading.get(param)
                dfrobot_val = dfrobot_reading.get(param)
                
                if api_val is not None and dfrobot_val is not None:
                    diff = abs(api_val - dfrobot_val)
                    parity = "perfect" if diff == 0 else "close" if diff <= 1 else "different"
                    
                    comparison["differences"][param] = {
                        "api_value": api_val,
                        "dfrobot_value": dfrobot_val,
                        "difference": diff,
                        "parity": parity
                    }
            
            # Compare particle counts
            for param in ["particles_0_3um", "particles_2_5um"]:
                api_val = api_reading.get(param)
                dfrobot_val = dfrobot_reading.get(param)
                
                if api_val is not None and dfrobot_val is not None:
                    diff = abs(api_val - dfrobot_val)
                    parity = "perfect" if diff == 0 else "close" if diff <= 1 else "different"
                    
                    comparison["differences"][param] = {
                        "api_value": api_val,
                        "dfrobot_value": dfrobot_val,
                        "difference": diff,
                        "parity": parity
                    }
            
            # Determine overall parity
            parities = [d["parity"] for d in comparison["differences"].values()]
            if all(p == "perfect" for p in parities):
                comparison["parity_status"] = "perfect"
            elif all(p in ["perfect", "close"] for p in parities):
                comparison["parity_status"] = "good"
            else:
                comparison["parity_status"] = "issues"
        
        else:
            comparison["parity_status"] = "error"
            if "error" in api_reading:
                comparison["api_error"] = api_reading["error"]
            if "error" in dfrobot_reading:
                comparison["dfrobot_error"] = dfrobot_reading["error"]
        
        return comparison
    
    def display_comparison(self, comparison: dict):
        """Display comparison results for a single reading."""
        print(f"  Reading #{comparison['reading_number']}")
        
        if comparison["parity_status"] == "error":
            print(f"    Status: ERROR")
            if "api_error" in comparison:
                print(f"    API Error: {comparison['api_error']}")
            if "dfrobot_error" in comparison:
                print(f"    DFRobot Error: {comparison['dfrobot_error']}")
            return
        
        print(f"    Status: {comparison['parity_status'].upper()}")
        
        # Display PM concentrations
        print("    PM Concentrations (μg/m³):")
        for param in ["pm1_0_standard", "pm2_5_standard", "pm10_standard"]:
            if param in comparison["differences"]:
                diff_data = comparison["differences"][param]
                api_val = diff_data["api_value"]
                dfrobot_val = diff_data["dfrobot_value"]
                diff = diff_data["difference"]
                parity = diff_data["parity"]
                
                print(f"      {param}: API={api_val}, DFRobot={dfrobot_val}, Diff={diff} ({parity})")
        
        # Display particle counts
        print("    Particle Counts (per 0.1L):")
        for param in ["particles_0_3um", "particles_2_5um"]:
            if param in comparison["differences"]:
                diff_data = comparison["differences"][param]
                api_val = diff_data["api_value"]
                dfrobot_val = diff_data["dfrobot_value"]
                diff = diff_data["difference"]
                parity = diff_data["parity"]
                
                print(f"      {param}: API={api_val}, DFRobot={dfrobot_val}, Diff={diff} ({parity})")
    
    def display_summary(self):
        """Display test summary statistics."""
        print("\n" + "=" * 60)
        print("COMPARISON TEST SUMMARY")
        print("=" * 60)
        
        if not self.results:
            print("No valid readings obtained")
            return
        
        # Count parity statuses
        parity_counts = {}
        for result in self.results:
            status = result["parity_status"]
            parity_counts[status] = parity_counts.get(status, 0) + 1
        
        print(f"Total readings attempted: {self.test_count}")
        print(f"Valid comparisons: {len(self.results)}")
        print(f"Errors encountered: {len(self.errors)}")
        print()
        
        print("Parity Status Distribution:")
        for status, count in parity_counts.items():
            percentage = (count / len(self.results)) * 100
            print(f"  {status}: {count} ({percentage:.1f}%)")
        
        # Calculate average differences
        if self.results:
            print("\nAverage Differences:")
            for param in ["pm1_0_standard", "pm2_5_standard", "pm10_standard", 
                         "particles_0_3um", "particles_2_5um"]:
                diffs = []
                for result in self.results:
                    if param in result.get("differences", {}):
                        diffs.append(result["differences"][param]["difference"])
                
                if diffs:
                    avg_diff = sum(diffs) / len(diffs)
                    max_diff = max(diffs)
                    print(f"  {param}: avg={avg_diff:.2f}, max={max_diff}")
        
        # Display errors if any
        if self.errors:
            print("\nErrors Encountered:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        # Overall assessment
        perfect_count = parity_counts.get("perfect", 0)
        good_count = parity_counts.get("good", 0)
        total_valid = len(self.results)
        
        if total_valid > 0:
            success_rate = ((perfect_count + good_count) / total_valid) * 100
            print(f"\nOverall Success Rate: {success_rate:.1f}%")
            
            if success_rate >= 95:
                print("✅ EXCELLENT: APIs show excellent parity")
            elif success_rate >= 85:
                print("✅ GOOD: APIs show good parity with minor differences")
            elif success_rate >= 70:
                print("⚠️  FAIR: APIs show fair parity with some differences")
            else:
                print("❌ POOR: APIs show poor parity - needs investigation")
        
        print("\nRecommendations:")
        if perfect_count == total_valid:
            print("  ✅ Perfect parity achieved - APIs are functionally identical")
        elif success_rate >= 90:
            print("  ✅ High parity achieved - APIs are suitable for production")
        else:
            print("  ⚠️  Investigate differences before production deployment")
        
        if self.errors:
            print("  🔧 Address error conditions for improved reliability")


def main():
    """Main function to run comparison test."""
    tester = ComparisonTester()
    
    # Run comparison with configurable parameters
    num_readings = 10
    interval = 2.0
    
    # Allow command line overrides
    if len(sys.argv) > 1:
        try:
            num_readings = int(sys.argv[1])
        except ValueError:
            print("Invalid number of readings, using default: 10")
    
    if len(sys.argv) > 2:
        try:
            interval = float(sys.argv[2])
        except ValueError:
            print("Invalid interval, using default: 2.0")
    
    tester.run_comparison_test(num_readings, interval)


if __name__ == "__main__":
    main()
