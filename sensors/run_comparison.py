#!/usr/bin/env python3
"""
PM25 Sensor API Comparison Test

This script performs side-by-side comparison between our independent API
and the original DFRobot repository to validate functional parity.
"""

import sys
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add paths for both APIs
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent

# Add our independent API
sys.path.insert(0, str(current_dir.parent))
from apis import PM25Sensor, PM25Config

# Add DFRobot API for comparison
dfrobot_path = project_root / "DFRobot_AirQualitySensor" / "python" / "raspberrypi"
dfrobot_available = False
dfrobot_sensor = None

if dfrobot_path.exists():
    sys.path.insert(0, str(dfrobot_path))
    try:
        from DFRobot_AirQualitySensor import DFRobot_AirQualitySensor
        dfrobot_sensor = DFRobot_AirQualitySensor(1, 0x19)
        dfrobot_available = True
        print("✅ DFRobot API loaded successfully")
    except ImportError as e:
        print(f"❌ Failed to import DFRobot API: {e}")
else:
    print("❌ DFRobot repository not found")

class ComparisonTester:
    """Class to perform comprehensive comparison between APIs."""
    
    def __init__(self):
        self.our_sensor = None
        self.dfrobot_sensor = dfrobot_sensor
        self.comparison_results = []
        
    def initialize_sensors(self) -> bool:
        """Initialize both sensors for comparison."""
        print("\n🔧 Initializing sensors...")
        
        try:
            # Initialize our sensor
            config = PM25Config({
                "i2c": {"bus": 1, "address": 0x19, "timeout": 5.0},
                "sensor": {"warmup_time": 5, "enable_validation": True},
                "performance": {"cache_timeout": 0.1}
            })
            
            self.our_sensor = PM25Sensor(config=config, auto_connect=True, auto_warmup=True)
            
            if not self.our_sensor.is_connected():
                print("❌ Failed to connect our sensor")
                return False
            
            print("✅ Our sensor connected successfully")
            
            # Test DFRobot sensor
            if self.dfrobot_sensor and dfrobot_available:
                version = self.dfrobot_sensor.gain_version()
                if version == -1:
                    print("❌ DFRobot sensor not responding")
                    return False
                
                print("✅ DFRobot sensor connected successfully")
                print(f"📋 DFRobot Firmware Version: {version}")
            
            # Get our sensor firmware version
            our_version = self.our_sensor.get_firmware_version()
            print(f"📋 Our API Firmware Version: {our_version}")
            
            return True
            
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            return False
    
    def compare_concentration_readings(self) -> Dict[str, Any]:
        """Compare PM concentration readings."""
        print("\n📊 Comparing PM Concentration Readings...")
        
        concentration_tests = [
            ("PM1.0 Standard", "PARTICLE_PM1_0_STANDARD", "get_pm1_0_standard"),
            ("PM2.5 Standard", "PARTICLE_PM2_5_STANDARD", "get_pm2_5_standard"),
            ("PM10 Standard", "PARTICLE_PM10_STANDARD", "get_pm10_standard"),
            ("PM1.0 Atmospheric", "PARTICLE_PM1_0_ATMOSPHERE", "get_pm1_0_atmospheric"),
            ("PM2.5 Atmospheric", "PARTICLE_PM2_5_ATMOSPHERE", "get_pm2_5_atmospheric"),
            ("PM10 Atmospheric", "PARTICLE_PM10_ATMOSPHERE", "get_pm10_atmospheric"),
        ]
        
        results = {}
        
        for name, dfrobot_const, our_method in concentration_tests:
            try:
                # Read from our API
                our_reading = getattr(self.our_sensor, our_method)(use_cache=False)
                
                # Read from DFRobot API
                dfrobot_reading = -1
                if self.dfrobot_sensor:
                    dfrobot_reading = self.dfrobot_sensor.gain_particle_concentration_ugm3(
                        getattr(self.dfrobot_sensor, dfrobot_const)
                    )
                
                # Compare readings
                match = our_reading == dfrobot_reading
                difference = abs(our_reading - dfrobot_reading) if dfrobot_reading != -1 else -1
                
                result = {
                    "parameter": name,
                    "our_api": our_reading,
                    "dfrobot_api": dfrobot_reading,
                    "match": match,
                    "difference": difference,
                    "status": "✅ PASS" if match else "❌ FAIL"
                }
                
                results[name] = result
                print(f"  {name}: Our={our_reading:3d}, DFRobot={dfrobot_reading:3d}, "
                      f"Match={match}, Diff={difference}")
                
            except Exception as e:
                error_result = {
                    "parameter": name,
                    "error": str(e),
                    "status": "❌ ERROR"
                }
                results[name] = error_result
                print(f"  {name}: ERROR - {e}")
        
        return results
    
    def compare_particle_counts(self) -> Dict[str, Any]:
        """Compare particle count readings."""
        print("\n🔢 Comparing Particle Count Readings...")
        
        particle_tests = [
            ("0.3μm", "PARTICLENUM_0_3_UM_EVERY0_1L_AIR", "get_particles_0_3um"),
            ("0.5μm", "PARTICLENUM_0_5_UM_EVERY0_1L_AIR", "get_particles_0_5um"),
            ("1.0μm", "PARTICLENUM_1_0_UM_EVERY0_1L_AIR", "get_particles_1_0um"),
            ("2.5μm", "PARTICLENUM_2_5_UM_EVERY0_1L_AIR", "get_particles_2_5um"),
            ("5.0μm", "PARTICLENUM_5_0_UM_EVERY0_1L_AIR", "get_particles_5_0um"),
            ("10μm", "PARTICLENUM_10_UM_EVERY0_1L_AIR", "get_particles_10um"),
        ]
        
        results = {}
        
        for name, dfrobot_const, our_method in particle_tests:
            try:
                # Read from our API
                our_reading = getattr(self.our_sensor, our_method)(use_cache=False)
                
                # Read from DFRobot API
                dfrobot_reading = -1
                if self.dfrobot_sensor:
                    dfrobot_reading = self.dfrobot_sensor.gain_particlenum_every0_1l(
                        getattr(self.dfrobot_sensor, dfrobot_const)
                    )
                
                # Compare readings
                match = our_reading == dfrobot_reading
                difference = abs(our_reading - dfrobot_reading) if dfrobot_reading != -1 else -1
                
                result = {
                    "parameter": name,
                    "our_api": our_reading,
                    "dfrobot_api": dfrobot_reading,
                    "match": match,
                    "difference": difference,
                    "status": "✅ PASS" if match else "❌ FAIL"
                }
                
                results[name] = result
                print(f"  {name}: Our={our_reading:6d}, DFRobot={dfrobot_reading:6d}, "
                      f"Match={match}, Diff={difference}")
                
            except Exception as e:
                error_result = {
                    "parameter": name,
                    "error": str(e),
                    "status": "❌ ERROR"
                }
                results[name] = error_result
                print(f"  {name}: ERROR - {e}")
        
        return results
    
    def compare_performance(self) -> Dict[str, Any]:
        """Compare performance between APIs."""
        print("\n⚡ Comparing Performance...")
        
        if not self.dfrobot_sensor:
            return {"error": "DFRobot sensor not available"}
        
        # Test our API performance
        our_times = []
        for i in range(20):
            start_time = time.time()
            reading = self.our_sensor.get_pm2_5_standard(use_cache=False)
            end_time = time.time()
            our_times.append(end_time - start_time)
        
        # Test DFRobot API performance
        dfrobot_times = []
        for i in range(20):
            start_time = time.time()
            reading = self.dfrobot_sensor.gain_particle_concentration_ugm3(
                self.dfrobot_sensor.PARTICLE_PM2_5_STANDARD
            )
            end_time = time.time()
            dfrobot_times.append(end_time - start_time)
        
        # Calculate statistics
        our_avg = sum(our_times) / len(our_times)
        our_min = min(our_times)
        our_max = max(our_times)
        
        dfrobot_avg = sum(dfrobot_times) / len(dfrobot_times)
        dfrobot_min = min(dfrobot_times)
        dfrobot_max = max(dfrobot_times)
        
        performance_ratio = our_avg / dfrobot_avg if dfrobot_avg > 0 else 1
        
        results = {
            "our_api": {
                "avg_time": our_avg,
                "min_time": our_min,
                "max_time": our_max,
                "total_samples": len(our_times)
            },
            "dfrobot_api": {
                "avg_time": dfrobot_avg,
                "min_time": dfrobot_min,
                "max_time": dfrobot_max,
                "total_samples": len(dfrobot_times)
            },
            "performance_ratio": performance_ratio,
            "status": "✅ GOOD" if performance_ratio <= 2.0 else "⚠️ SLOW",
            "conclusion": f"Our API is {performance_ratio:.2f}x {'faster' if performance_ratio < 1 else 'slower'} than DFRobot"
        }
        
        print(f"  Our API:   Avg={our_avg:.3f}s, Min={our_min:.3f}s, Max={our_max:.3f}s")
        print(f"  DFRobot API: Avg={dfrobot_avg:.3f}s, Min={dfrobot_min:.3f}s, Max={dfrobot_max:.3f}s")
        print(f"  Performance Ratio: {performance_ratio:.2f}x")
        print(f"  {results['conclusion']}")
        
        return results
    
    def run_comprehensive_comparison(self) -> Dict[str, Any]:
        """Run comprehensive comparison test."""
        print("🚀 Starting Comprehensive API Comparison")
        print("=" * 60)
        
        if not self.initialize_sensors():
            return {"error": "Failed to initialize sensors"}
        
        # Wait for sensors to stabilize
        print("⏳ Waiting for sensor stabilization...")
        time.sleep(2)
        
        # Run comparison tests
        concentration_results = self.compare_concentration_readings()
        particle_results = self.compare_particle_counts()
        performance_results = self.compare_performance()
        
        # Calculate overall statistics
        all_concentration_results = list(concentration_results.values())
        all_particle_results = list(particle_results.values())
        all_results = all_concentration_results + all_particle_results
        
        total_tests = len([r for r in all_results if "match" in r])
        passed_tests = len([r for r in all_results if r.get("match", False)])
        failed_tests = len([r for r in all_results if not r.get("match", False)])
        error_tests = len([r for r in all_results if "error" in r])
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Generate summary
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": success_rate,
            "functional_parity": success_rate >= 95.0,
            "concentration_results": concentration_results,
            "particle_results": particle_results,
            "performance_results": performance_results,
            "overall_status": "✅ EXCELLENT" if success_rate >= 95 else "⚠️ NEEDS WORK" if success_rate >= 80 else "❌ FAILED"
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 COMPARISON SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Errors: {summary['error_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Functional Parity: {'✅ ACHIEVED' if summary['functional_parity'] else '❌ NOT ACHIEVED'}")
        print(f"Overall Status: {summary['overall_status']}")
        
        if not summary['functional_parity']:
            print("\n⚠️  Functional parity not achieved. Review failed tests above.")
        
        return summary
    
    def cleanup(self):
        """Clean up sensor connections."""
        try:
            if self.our_sensor:
                self.our_sensor.disconnect()
                print("🔌 Our sensor disconnected")
        except Exception:
            pass


def main():
    """Main comparison function."""
    print("PM25 Sensor API Comparison Test")
    print("================================")
    print("This test compares our independent API with the original DFRobot repository")
    print("to validate functional parity and performance.\n")
    
    if not dfrobot_available:
        print("⚠️  Warning: DFRobot API not available. Comparison will be limited.")
        print("Make sure the DFRobot_AirQualitySensor directory exists with the Python files.\n")
    
    tester = ComparisonTester()
    
    try:
        # Run comprehensive comparison
        results = tester.run_comprehensive_comparison()
        
        # Save results to file
        import json
        results_file = current_dir / "comparison_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        # Return appropriate exit code
        if results.get("functional_parity", False):
            sys.exit(1)  # Failed parity
        else:
            sys.exit(0)  # Successful parity
            
    except KeyboardInterrupt:
        print("\n⏹  Comparison interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Comparison failed with error: {e}")
        sys.exit(1)
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()