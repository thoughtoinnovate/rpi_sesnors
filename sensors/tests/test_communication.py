"""
I2C Communication Robustness Tests for PM25 Sensor

This module tests I2C communication stability, error recovery, and robustness.
All tests use real hardware - no mocks allowed.

Test Areas:
- Connection stability and recovery
- Rapid read operations
- Bus error handling
- Timeout and retry behavior
- Continuous operation stability
"""

import pytest
import time
import threading
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from .conftest import (
    validate_reading_range, measure_read_time, wait_for_sensor_stabilization
)


class TestConnectionStability:
    """Test I2C connection stability and recovery."""
    
    def test_initial_connection(self, sensor):
        """Test initial sensor connection."""
        assert sensor.is_connected(), "Sensor should be connected after initialization"
        assert sensor.is_initialized(), "Sensor should be initialized"
    
    def test_connection_persistence(self, sensor, reading_data):
        """Test that connection remains stable over multiple operations."""
        initial_connected = sensor.is_connected()
        
        # Perform multiple reads
        for i in range(10):
            reading = sensor.get_pm2_5_standard(use_cache=False)
            validate_reading_range(
                reading,
                reading_data["pm_concentration"]["min"],
                reading_data["pm_concentration"]["max"],
                f"PM2.5 reading {i+1}"
            )
            time.sleep(0.1)
        
        final_connected = sensor.is_connected()
        assert initial_connected and final_connected, "Connection should remain stable"
    
    def test_reconnection_after_disconnect(self, sensor, test_config):
        """Test reconnection after manual disconnect."""
        # Disconnect sensor
        sensor.disconnect()
        assert not sensor.is_connected(), "Sensor should be disconnected"
        
        # Reconnect
        reconnected = sensor.initialize()
        assert reconnected, "Sensor should reconnect successfully"
        assert sensor.is_connected(), "Sensor should be connected after reconnection"
        
        # Verify sensor still works
        reading = sensor.get_pm2_5_standard()
        assert reading >= 0, "Sensor should return valid readings after reconnection"
    
    def test_multiple_connection_cycles(self, sensor, test_config):
        """Test multiple connect/disconnect cycles."""
        for cycle in range(3):
            # Disconnect
            sensor.disconnect()
            assert not sensor.is_connected(), f"Cycle {cycle+1}: Should be disconnected"
            
            # Reconnect
            success = sensor.initialize()
            assert success, f"Cycle {cycle+1}: Should reconnect successfully"
            assert sensor.is_connected(), f"Cycle {cycle+1}: Should be connected"
            
            # Test reading
            reading = sensor.get_pm2_5_standard()
            assert reading >= 0, f"Cycle {cycle+1}: Should return valid reading"
            
            time.sleep(0.5)


class TestRapidReadOperations:
    """Test rapid read operations and performance."""
    
    def test_rapid_sequential_reads(self, sensor, reading_data):
        """Test rapid sequential read operations."""
        num_reads = 50
        read_times = []
        valid_readings = 0
        
        for i in range(num_reads):
            start_time = time.time()
            reading = sensor.get_pm2_5_standard(use_cache=False)
            end_time = time.time()
            
            read_time = end_time - start_time
            read_times.append(read_time)
            
            if reading >= 0:
                valid_readings += 1
                validate_reading_range(
                    reading,
                    reading_data["pm_concentration"]["min"],
                    reading_data["pm_concentration"]["max"],
                    f"Rapid read {i+1}"
                )
        
        # Analyze performance
        avg_read_time = sum(read_times) / len(read_times)
        max_read_time = max(read_times)
        success_rate = (valid_readings / num_reads) * 100
        
        assert success_rate >= 95, f"Success rate {success_rate}% should be >= 95%"
        assert avg_read_time <= 0.1, f"Average read time {avg_read_time:.3f}s should be <= 0.1s"
        assert max_read_time <= 1.0, f"Max read time {max_read_time:.3f}s should be <= 1.0s"
    
    def test_rapid_alternating_reads(self, sensor, reading_data):
        """Test rapid alternating reads of different parameters."""
        read_functions = [
            ("PM1.0", sensor.get_pm1_0_standard),
            ("PM2.5", sensor.get_pm2_5_standard),
            ("PM10", sensor.get_pm10_standard),
            ("0.3μm", sensor.get_particles_0_3um),
            ("2.5μm", sensor.get_particles_2_5um),
            ("10μm", sensor.get_particles_10um),
        ]
        
        num_cycles = 20
        for cycle in range(num_cycles):
            for name, func in read_functions:
                reading, read_time = measure_read_time(func, use_cache=False)
                
                # Validate reading based on type
                if "PM" in name:
                    validate_reading_range(
                        reading,
                        reading_data["pm_concentration"]["min"],
                        reading_data["pm_concentration"]["max"],
                        f"{name} cycle {cycle+1}"
                    )
                else:
                    validate_reading_range(
                        reading,
                        reading_data["particle_count"]["min"],
                        reading_data["particle_count"]["max"],
                        f"{name} particles cycle {cycle+1}"
                    )
                
                assert read_time <= 0.1, f"{name} read time {read_time:.3f}s should be <= 0.1s"
    
    def test_concurrent_reads(self, sensor, reading_data):
        """Test concurrent read operations from multiple threads."""
        def read_worker(worker_id: int) -> Dict[str, Any]:
            """Worker function for concurrent reads."""
            results = {
                "worker_id": worker_id,
                "reads": 0,
                "successful_reads": 0,
                "errors": []
            }
            
            for i in range(10):
                try:
                    reading = sensor.get_pm2_5_standard(use_cache=False)
                    results["reads"] += 1
                    
                    if reading >= 0:
                        results["successful_reads"] += 1
                        validate_reading_range(
                            reading,
                            reading_data["pm_concentration"]["min"],
                            reading_data["pm_concentration"]["max"],
                            f"Worker {worker_id} read {i+1}"
                        )
                    else:
                        results["errors"].append(f"Invalid reading: {reading}")
                        
                except Exception as e:
                    results["errors"].append(str(e))
                
                time.sleep(0.01)  # Small delay between reads
            
            return results
        
        # Run concurrent workers
        num_workers = 5
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(read_worker, i) for i in range(num_workers)]
            worker_results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        total_reads = sum(result["reads"] for result in worker_results)
        total_successful = sum(result["successful_reads"] for result in worker_results)
        total_errors = sum(len(result["errors"]) for result in worker_results)
        
        success_rate = (total_successful / total_reads) * 100 if total_reads > 0 else 0
        
        assert success_rate >= 90, f"Concurrent success rate {success_rate}% should be >= 90%"
        assert total_errors <= total_reads * 0.1, f"Too many errors: {total_errors}/{total_reads}"


class TestSensorWarmupBehavior:
    """Test sensor behavior during warmup period."""
    
    def test_warmup_reading_stability(self, sensor, test_config):
        """Test reading stability during warmup period."""
        # Reset sensor (simulate cold start)
        sensor.disconnect()
        time.sleep(1)
        
        # Reinitialize without auto-warmup
        sensor._auto_warmup = False
        sensor.initialize()
        
        readings = []
        warmup_duration = test_config.get("sensor.warmup_time", 5)
        
        # Take readings during warmup
        for i in range(warmup_duration * 2):  # Read every 0.5 seconds
            try:
                reading = sensor.get_pm2_5_standard(use_cache=False)
                readings.append(reading)
            except Exception as e:
                readings.append(None)  # Mark failed reads
            
            time.sleep(0.5)
        
        # Wait for full warmup
        wait_for_sensor_stabilization(sensor, warmup_duration)
        
        # Take final stable reading
        stable_reading = sensor.get_pm2_5_standard()
        
        # Analyze warmup behavior
        valid_readings = [r for r in readings if r is not None and r >= 0]
        invalid_readings = [r for r in readings if r is None or r < 0]
        
        # Should have some valid readings during warmup
        assert len(valid_readings) > 0, "Should have valid readings during warmup"
        
        # Final reading should be valid
        assert stable_reading >= 0, "Final stable reading should be valid"
        
        # Invalid readings should be limited
        invalid_rate = len(invalid_readings) / len(readings) * 100
        assert invalid_rate <= 50, f"Invalid reading rate {invalid_rate}% should be <= 50%"
    
    def test_stabilization_time(self, sensor):
        """Test sensor stabilization time after warmup."""
        # Ensure sensor is warmed up
        wait_for_sensor_stabilization(sensor)
        
        # Take consecutive readings and check for stability
        readings = []
        for i in range(10):
            reading = sensor.get_pm2_5_standard(use_cache=False)
            readings.append(reading)
            time.sleep(0.5)
        
        # Calculate variance
        if len(readings) >= 2:
            variance = max(readings) - min(readings)
            # Allow some variance but not excessive
            assert variance <= 50, f"Reading variance {variance} should be <= 50 units"


class TestContinuousOperation:
    """Test continuous operation stability."""
    
    def test_extended_continuous_reading(self, sensor, reading_data):
        """Test extended continuous reading (short version for testing)."""
        duration_seconds = 30  # Shortened for testing, should be 3600+ for real test
        interval = 1.0
        
        readings = []
        errors = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            try:
                reading = sensor.get_pm2_5_standard(use_cache=False)
                timestamp = time.time()
                
                readings.append({
                    "timestamp": timestamp,
                    "value": reading
                })
                
                validate_reading_range(
                    reading,
                    reading_data["pm_concentration"]["min"],
                    reading_data["pm_concentration"]["max"],
                    f"Continuous reading at {timestamp - start_time:.1f}s"
                )
                
            except Exception as e:
                errors.append({
                    "timestamp": time.time(),
                    "error": str(e)
                })
            
            time.sleep(interval)
        
        # Analyze results
        total_readings = len(readings)
        total_errors = len(errors)
        success_rate = (total_readings / (total_readings + total_errors)) * 100 if (total_readings + total_errors) > 0 else 0
        
        assert success_rate >= 95, f"Continuous operation success rate {success_rate}% should be >= 95%"
        assert total_readings >= duration_seconds * 0.9, f"Should have at least 90% expected readings"
    
    def test_memory_usage_stability(self, sensor, performance_tracker):
        """Test memory usage stability during continuous operation."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            # Perform many readings
            for i in range(100):
                reading = sensor.get_complete_reading(use_cache=False)
                
                # Check memory every 20 readings
                if i % 20 == 0:
                    current_memory = process.memory_info().rss
                    memory_increase = current_memory - initial_memory
                    memory_increase_mb = memory_increase / (1024 * 1024)
                    
                    # Memory increase should be reasonable
                    assert memory_increase_mb <= 10, f"Memory increase {memory_increase_mb:.1f}MB should be <= 10MB"
        
        except ImportError:
            pytest.skip("psutil not available for memory testing")
    
    def test_performance_degradation(self, sensor, performance_tracker):
        """Test for performance degradation over time."""
        read_times = []
        
        # Take 100 readings and track timing
        for i in range(100):
            start_time = time.time()
            reading = sensor.get_pm2_5_standard(use_cache=False)
            end_time = time.time()
            
            read_time = end_time - start_time
            read_times.append(read_time)
            
            time.sleep(0.1)  # Small delay between reads
        
        # Analyze performance trends
        first_10_avg = sum(read_times[:10]) / 10
        last_10_avg = sum(read_times[-10:]) / 10
        
        # Performance should not degrade significantly
        degradation_ratio = last_10_avg / first_10_avg if first_10_avg > 0 else 1
        assert degradation_ratio <= 2.0, f"Performance degradation {degradation_ratio:.2f}x should be <= 2.0x"
        
        # Overall average should be reasonable
        overall_avg = sum(read_times) / len(read_times)
        assert overall_avg <= 0.1, f"Overall average read time {overall_avg:.3f}s should be <= 0.1s"


class TestErrorRecovery:
    """Test error recovery and robustness."""
    
    def test_invalid_register_handling(self, sensor):
        """Test handling of invalid register access."""
        # This test would require accessing private methods or creating custom scenarios
        # For now, we test that the sensor handles edge cases gracefully
        
        # Test rapid successive operations that might cause bus contention
        for i in range(20):
            try:
                reading = sensor.get_pm2_5_standard(use_cache=False)
                assert reading >= 0, f"Reading {i} should be valid"
            except Exception as e:
                # Should not raise exceptions frequently
                assert False, f"Unexpected exception in rapid operations: {e}"
    
    def test_timeout_handling(self, sensor):
        """Test timeout handling in communication."""
        # Get current performance statistics
        initial_stats = sensor.get_performance_statistics()
        
        # Perform operations that might timeout
        for i in range(10):
            try:
                reading = sensor.get_pm2_5_standard(use_cache=False)
                assert reading >= 0, f"Reading {i} should be valid"
            except Exception as e:
                # Log but don't fail - sensor should handle timeouts gracefully
                print(f"Timeout or error in reading {i}: {e}")
        
        # Check final statistics
        final_stats = sensor.get_performance_statistics()
        
        # Error rate should be reasonable
        error_rate = final_stats["error_rate"]
        assert error_rate <= 50, f"Error rate {error_rate}% should be <= 50%"
    
    def test_bus_contention_recovery(self, sensor):
        """Test recovery from I2C bus contention."""
        # Simulate bus contention with rapid operations
        def rapid_operations():
            for i in range(50):
                try:
                    sensor.get_pm2_5_standard(use_cache=False)
                except Exception:
                    pass  # Ignore errors during contention
        
        # Run in multiple threads to simulate contention
        threads = []
        for i in range(3):
            thread = threading.Thread(target=rapid_operations)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Sensor should still be responsive after contention
        time.sleep(1)  # Allow bus to settle
        final_reading = sensor.get_pm2_5_standard()
        assert final_reading >= 0, "Sensor should be responsive after bus contention"
        assert sensor.is_connected(), "Sensor should remain connected after contention"


class TestCommunicationStatistics:
    """Test communication statistics tracking."""
    
    def test_statistics_accuracy(self, sensor, performance_tracker):
        """Test accuracy of communication statistics."""
        # Get initial statistics
        initial_stats = sensor.get_performance_statistics()
        initial_reads = initial_stats["total_readings"]
        initial_errors = initial_stats["total_errors"]
        
        # Perform known number of operations
        num_operations = 20
        successful_operations = 0
        
        for i in range(num_operations):
            try:
                reading = sensor.get_pm2_5_standard(use_cache=False)
                if reading >= 0:
                    successful_operations += 1
            except Exception:
                pass  # Count as error
        
        # Get final statistics
        final_stats = sensor.get_performance_statistics()
        final_reads = final_stats["total_readings"]
        final_errors = final_stats["total_errors"]
        
        # Verify statistics
        reads_increase = final_reads - initial_reads
        errors_increase = final_errors - initial_errors
        
        assert reads_increase >= num_operations * 0.8, f"Reads increased by {reads_increase}, expected ~{num_operations}"
        assert errors_increase <= num_operations * 0.2, f"Errors increased by {errors_increase}, should be <= {num_operations * 0.2}"
    
    def test_statistics_reset(self, sensor):
        """Test statistics reset functionality."""
        # Perform some operations to generate statistics
        for i in range(10):
            sensor.get_pm2_5_standard(use_cache=False)
        
        # Get statistics before reset
        pre_reset_stats = sensor.get_performance_statistics()
        assert pre_reset_stats["total_readings"] > 0, "Should have readings before reset"
        
        # Reset statistics
        sensor.reset_statistics()
        
        # Get statistics after reset
        post_reset_stats = sensor.get_performance_statistics()
        assert post_reset_stats["total_readings"] == 0, "Readings should be reset to 0"
        assert post_reset_stats["total_errors"] == 0, "Errors should be reset to 0"
        assert post_reset_stats["last_reading_time"] is None, "Last reading time should be cleared"