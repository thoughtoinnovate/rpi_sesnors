#!/usr/bin/env python3
"""
24-Hour Continuous Stability Test for PM25 Sensor

This test runs the PM25 sensor continuously for 24 hours to validate:
- Long-term stability and reliability
- Memory usage stability
- Error rate over extended periods
- Data consistency over time
- Performance degradation detection

Requirements:
- Real PM25 sensor hardware connected
- Stable power supply
- Uninterrupted operation for 24 hours
"""

import sys
import time
import json
import logging
import signal
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
import psutil
import gc

# Add parent directory to path (so we can import apis)
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))
from apis import PM25Sensor, PM25Config


class StabilityTestResults:
    """Container for stability test results and statistics."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_readings = 0
        self.total_errors = 0
        self.readings_data = []
        self.error_events = []
        self.memory_samples = []
        self.performance_stats = []
        self.test_running = True
        
    def add_reading(self, reading_data: Dict[str, Any]):
        """Add a successful reading to results."""
        self.readings_data.append(reading_data)
        self.total_readings += 1
        
    def add_error(self, error_info: Dict[str, Any]):
        """Add an error event to results."""
        self.error_events.append(error_info)
        self.total_errors += 1
        
    def add_memory_sample(self, memory_info: Dict[str, Any]):
        """Add memory usage sample."""
        self.memory_samples.append(memory_info)
        
    def add_performance_sample(self, perf_info: Dict[str, Any]):
        """Add performance statistics sample."""
        self.performance_stats.append(perf_info)
        
    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive test statistics."""
        if not self.start_time:
            return {}
            
        duration = (self.end_time or datetime.now()) - self.start_time
        duration_hours = duration.total_seconds() / 3600
        
        # Calculate reading statistics
        pm25_values = [r.get('pm25_standard', 0) for r in self.readings_data if r.get('pm25_standard')]
        pm10_values = [r.get('pm10_standard', 0) for r in self.readings_data if r.get('pm10_standard')]
        
        stats = {
            'test_duration': {
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'duration_hours': duration_hours,
                'duration_seconds': duration.total_seconds()
            },
            'reading_statistics': {
                'total_readings': self.total_readings,
                'total_errors': self.total_errors,
                'error_rate_percent': (self.total_errors / max(self.total_readings + self.total_errors, 1)) * 100,
                'readings_per_hour': self.total_readings / max(duration_hours, 0.001),
                'success_rate_percent': (self.total_readings / max(self.total_readings + self.total_errors, 1)) * 100
            },
            'data_quality': {
                'pm25_stats': self._calculate_value_stats(pm25_values),
                'pm10_stats': self._calculate_value_stats(pm10_values),
                'data_gaps': self._detect_data_gaps()
            },
            'memory_analysis': self._analyze_memory_usage(),
            'performance_analysis': self._analyze_performance(),
            'error_analysis': self._analyze_errors()
        }
        
        return stats
        
    def _calculate_value_stats(self, values: List[float]) -> Dict[str, Any]:
        """Calculate statistics for a list of values."""
        if not values:
            return {}
            
        values_sorted = sorted(values)
        n = len(values)
        
        return {
            'count': n,
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / n,
            'median': values_sorted[n // 2] if n % 2 == 1 else (values_sorted[n // 2 - 1] + values_sorted[n // 2]) / 2,
            'std_dev': (sum((x - sum(values) / n) ** 2 for x in values) / n) ** 0.5,
            'q25': values_sorted[n // 4],
            'q75': values_sorted[3 * n // 4]
        }
        
    def _detect_data_gaps(self) -> List[Dict[str, Any]]:
        """Detect gaps in data collection."""
        if len(self.readings_data) < 2:
            return []
            
        gaps = []
        for i in range(1, len(self.readings_data)):
            prev_time = self.readings_data[i-1].get('timestamp')
            curr_time = self.readings_data[i].get('timestamp')
            
            if prev_time and curr_time:
                gap_seconds = curr_time - prev_time
                if gap_seconds > 120:  # Gap > 2 minutes
                    gaps.append({
                        'gap_start': prev_time,
                        'gap_end': curr_time,
                        'gap_duration_seconds': gap_seconds
                    })
                    
        return gaps
        
    def _analyze_memory_usage(self) -> Dict[str, Any]:
        """Analyze memory usage patterns."""
        if not self.memory_samples:
            return {}
            
        memory_values = [s['rss_mb'] for s in self.memory_samples]
        
        return {
            'samples_count': len(self.memory_samples),
            'initial_memory_mb': memory_values[0] if memory_values else 0,
            'final_memory_mb': memory_values[-1] if memory_values else 0,
            'peak_memory_mb': max(memory_values) if memory_values else 0,
            'min_memory_mb': min(memory_values) if memory_values else 0,
            'avg_memory_mb': sum(memory_values) / len(memory_values) if memory_values else 0,
            'memory_growth_mb': (memory_values[-1] - memory_values[0]) if len(memory_values) >= 2 else 0,
            'memory_stability': max(memory_values) - min(memory_values) if memory_values else 0
        }
        
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance statistics."""
        if not self.performance_stats:
            return {}
            
        error_rates = [s.get('error_rate', 0) for s in self.performance_stats]
        
        return {
            'samples_count': len(self.performance_stats),
            'avg_error_rate': sum(error_rates) / len(error_rates) if error_rates else 0,
            'peak_error_rate': max(error_rates) if error_rates else 0,
            'performance_stability': max(error_rates) - min(error_rates) if len(error_rates) > 1 else 0
        }
        
    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns."""
        if not self.error_events:
            return {'total_errors': 0}
            
        error_types = {}
        for error in self.error_events:
            error_type = error.get('error_type', 'Unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
        return {
            'total_errors': len(self.error_events),
            'error_types': error_types,
            'first_error_time': min(e.get('timestamp', 0) for e in self.error_events),
            'last_error_time': max(e.get('timestamp', 0) for e in self.error_events),
            'error_frequency_per_hour': len(self.error_events) / max(duration_hours, 0.001)
        }


class StabilityTestRunner:
    """Runs the 24-hour stability test."""
    
    def __init__(self, config_path: str = None):
        """Initialize test runner."""
        self.config = PM25Config()  # Use default config
        self.sensor = None
        self.results = StabilityTestResults()
        self.test_interval = 30  # seconds between readings
        self.memory_sample_interval = 300  # 5 minutes
        self.performance_sample_interval = 600  # 10 minutes
        
        # Setup logging
        self.setup_logging()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def setup_logging(self):
        """Setup comprehensive logging."""
        log_file = Path(f"stability_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger("stability_test")
        self.logger.info("24-Hour Stability Test Starting")
        self.logger.info(f"Log file: {log_file}")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.results.test_running = False
        
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'timestamp': time.time(),
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': process.memory_percent()
        }
        
    def _collect_sensor_reading(self) -> Dict[str, Any]:
        """Collect comprehensive sensor reading."""
        try:
            reading_start = time.time()
            
            # Get all sensor data
            reading = {
                'timestamp': reading_start,
                'pm25_standard': self.sensor.get_pm2_5_standard(use_cache=False),
                'pm10_standard': self.sensor.get_pm10_standard(use_cache=False),
                'pm25_atmospheric': self.sensor.get_pm2_5_atmospheric(use_cache=False),
                'pm10_atmospheric': self.sensor.get_pm10_atmospheric(use_cache=False),
                'particle_counts': self.sensor.get_all_particle_counts(use_cache=False)
            }
            
            reading['reading_duration'] = time.time() - reading_start
            
            # Add AQI v2 calculation
            try:
                aqi_result = self.sensor.get_aqi_v2(use_cache=False)
                reading.update({f'aqi_{k}': v for k, v in aqi_result.items()})
            except Exception as e:
                self.logger.warning(f"AQI v2 calculation failed: {e}")
                reading['aqi_error'] = str(e)
                
            return reading
            
        except Exception as e:
            error_info = {
                'timestamp': time.time(),
                'error_type': type(e).__name__,
                'error_message': str(e),
                'sensor_connected': self.sensor.is_connected() if self.sensor else False
            }
            
            self.logger.error(f"Reading failed: {error_info}")
            self.results.add_error(error_info)
            return None
            
    def run_test(self, duration_hours: int = 24):
        """Run the stability test for specified duration."""
        self.logger.info(f"Starting {duration_hours}-hour stability test")
        
        try:
            # Initialize sensor
            self.sensor = PM25Sensor(config=self.config)
            self.results.start_time = datetime.now()
            
            self.logger.info("Sensor initialized successfully")
            self.logger.info(f"Test interval: {self.test_interval} seconds")
            
            # Timing variables
            last_reading_time = 0
            last_memory_sample = 0
            last_performance_sample = 0
            test_end_time = time.time() + (duration_hours * 3600)
            
            # Main test loop
            while self.results.test_running and time.time() < test_end_time:
                current_time = time.time()
                
                # Collect sensor reading
                if current_time - last_reading_time >= self.test_interval:
                    reading = self._collect_sensor_reading()
                    if reading:
                        self.results.add_reading(reading)
                        self.logger.debug(f"Reading collected: PM2.5={reading.get('pm25_standard')}, PM10={reading.get('pm10_standard')}")
                    last_reading_time = current_time
                    
                # Collect memory sample
                if current_time - last_memory_sample >= self.memory_sample_interval:
                    memory_sample = self._get_memory_usage()
                    self.results.add_memory_sample(memory_sample)
                    self.logger.debug(f"Memory usage: {memory_sample['rss_mb']:.1f} MB")
                    last_memory_sample = current_time
                    
                # Collect performance statistics
                if current_time - last_performance_sample >= self.performance_sample_interval:
                    try:
                        perf_stats = self.sensor.get_performance_statistics()
                        perf_stats['timestamp'] = current_time
                        self.results.add_performance_sample(perf_stats)
                        self.logger.debug(f"Performance: error_rate={perf_stats.get('error_rate', 0):.2f}%")
                    except Exception as e:
                        self.logger.warning(f"Performance stats collection failed: {e}")
                    last_performance_sample = current_time
                    
                # Force garbage collection periodically
                if int(current_time) % 1800 == 0:  # Every 30 minutes
                    gc.collect()
                    
                # Sleep to prevent busy waiting
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Test interrupted by user")
        except Exception as e:
            self.logger.error(f"Test failed with exception: {e}")
            raise
        finally:
            self._cleanup_test()
            
    def _cleanup_test(self):
        """Clean up test and save results."""
        self.logger.info("Cleaning up test...")
        
        try:
            if self.sensor:
                self.sensor.disconnect()
        except Exception as e:
            self.logger.warning(f"Sensor disconnect failed: {e}")
            
        self.results.end_time = datetime.now()
        
        # Calculate and save results
        stats = self.results.calculate_statistics()
        
        # Save results to file
        results_file = Path(f"stability_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        results_data = {
            'test_metadata': {
                'test_type': '24_hour_stability_test',
                'sensor_config': self.config.to_dict(),
                'test_parameters': {
                    'reading_interval_seconds': self.test_interval,
                    'memory_sample_interval_seconds': self.memory_sample_interval,
                    'performance_sample_interval_seconds': self.performance_sample_interval
                }
            },
            'test_statistics': stats,
            'raw_data': {
                'readings': self.results.readings_data[-1000:],  # Last 1000 readings
                'errors': self.results.error_events,
                'memory_samples': self.results.memory_samples,
                'performance_samples': self.results.performance_stats
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
            
        self.logger.info(f"Results saved to: {results_file}")
        
        # Print summary
        self._print_summary(stats)
        
    def _print_summary(self, stats: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "="*60)
        print("24-HOUR STABILITY TEST SUMMARY")
        print("="*60)
        
        duration = stats.get('test_duration', {})
        reading_stats = stats.get('reading_statistics', {})
        
        print(f"Test Duration: {duration.get('duration_hours', 0):.2f} hours")
        print(f"Total Readings: {reading_stats.get('total_readings', 0)}")
        print(f"Total Errors: {reading_stats.get('total_errors', 0)}")
        print(f"Success Rate: {reading_stats.get('success_rate_percent', 0):.2f}%")
        print(f"Error Rate: {reading_stats.get('error_rate_percent', 0):.2f}%")
        print(f"Readings/Hour: {reading_stats.get('readings_per_hour', 0):.1f}")
        
        memory_analysis = stats.get('memory_analysis', {})
        if memory_analysis:
            print(f"\nMemory Usage:")
            print(f"  Initial: {memory_analysis.get('initial_memory_mb', 0):.1f} MB")
            print(f"  Final: {memory_analysis.get('final_memory_mb', 0):.1f} MB")
            print(f"  Peak: {memory_analysis.get('peak_memory_mb', 0):.1f} MB")
            print(f"  Growth: {memory_analysis.get('memory_growth_mb', 0):.1f} MB")
            
        data_quality = stats.get('data_quality', {})
        pm25_stats = data_quality.get('pm25_stats', {})
        if pm25_stats:
            print(f"\nPM2.5 Data Quality:")
            print(f"  Range: {pm25_stats.get('min', 0):.1f} - {pm25_stats.get('max', 0):.1f} μg/m³")
            print(f"  Mean: {pm25_stats.get('mean', 0):.1f} μg/m³")
            print(f"  Std Dev: {pm25_stats.get('std_dev', 0):.2f} μg/m³")
            
        gaps = data_quality.get('data_gaps', [])
        if gaps:
            print(f"\nData Gaps: {len(gaps)} detected")
            for gap in gaps[:5]:  # Show first 5 gaps
                duration_min = gap.get('gap_duration_seconds', 0) / 60
                print(f"  Gap: {duration_min:.1f} minutes")
                
        print("="*60)


def main():
    """Main function to run stability test."""
    import argparse
    
    parser = argparse.ArgumentParser(description='24-Hour PM25 Sensor Stability Test')
    parser.add_argument('--duration', type=int, default=24, 
                       help='Test duration in hours (default: 24)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Reading interval in seconds (default: 30)')
    parser.add_argument('--config', type=str, default=None,
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Create and run test
    test_runner = StabilityTestRunner(args.config)
    test_runner.test_interval = args.interval
    
    try:
        test_runner.run_test(args.duration)
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
        
    print("Stability test completed successfully!")


if __name__ == "__main__":
    main()