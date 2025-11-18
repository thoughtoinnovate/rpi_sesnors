"""
Performance Benchmarking Tests for PM25 Sensor

This module tests performance characteristics and benchmarks.
All tests use real hardware - no mocks allowed.

Test Areas:
- Read speed benchmarks
- Memory usage analysis
- Cache performance
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any

from .conftest import (
    measure_read_time, validate_reading_range
)


class TestReadSpeedPerformance:
    """Test reading speed and performance."""
    
    @pytest.mark.performance
    def test_single_read_speed(self, sensor, reading_data):
        """Test speed of individual sensor reads."""
        read_times = []
        num_readings = 50
        
        for i in range(num_readings):
            reading, read_time = measure_read_time(
                sensor.get_pm2_5_standard, use_cache=False
            )
            
            validate_reading_range(
                reading,
                reading_data["pm_concentration"]["min"],
                reading_data["pm_concentration"]["max"],
                f"Performance reading {i+1}"
            )
            
            read_times.append(read_time)
        
        # Analyze performance
        avg_time = sum(read_times) / len(read_times)
        min_time = min(read_times)
        max_time = max(read_times)
        
        # Performance assertions
        assert avg_time <= 0.1, f"Average read time {avg_time:.3f}s should be <= 0.1s"
        assert max_time <= 0.5, f"Max read time {max_time:.3f}s should be <= 0.5s"
        assert min_time <= 0.05, f"Min read time {min_time:.3f}s should be <= 0.05s"
        
        # Performance consistency
        variance = max_time - min_time
        assert variance <= 0.2, f"Read time variance {variance:.3f}s should be <= 0.2s"
    
    @pytest.mark.performance
    def test_different_parameter_speed(self, sensor, reading_data):
        """Test speed of reading different parameters."""
        parameters = [
            ("PM1.0", sensor.get_pm1_0_standard),
            ("PM2.5", sensor.get_pm2_5_standard),
            ("PM10", sensor.get_pm10_standard),
            ("0.3μm", sensor.get_particles_0_3um),
            ("2.5μm", sensor.get_particles_2_5um),
            ("10μm", sensor.get_particles_10um),
        ]
        
        performance_results = {}
        
        for name, func in parameters:
            times = []
            
            for i in range(10):
                reading, read_time = measure_read_time(func, use_cache=False)
                times.append(read_time)
                
                # Validate reading
                if "PM" in name:
                    validate_reading_range(
                        reading,
                        reading_data["pm_concentration"]["min"],
                        reading_data["pm_concentration"]["max"],
                        f"{name} reading {i+1}"
                    )
                else:
                    validate_reading_range(
                        reading,
                        reading_data["particle_count"]["min"],
                        reading_data["particle_count"]["max"],
                        f"{name} reading {i+1}"
                    )
            
            avg_time = sum(times) / len(times)
            performance_results[name] = avg_time
        
        # All parameters should be reasonably fast
        for name, avg_time in performance_results.items():
            assert avg_time <= 0.15, f"{name} average time {avg_time:.3f}s should be <= 0.15s"
        
        # Performance should be consistent across parameters
        all_times = list(performance_results.values())
        max_avg = max(all_times)
        min_avg = min(all_times)
        
        performance_ratio = max_avg / min_avg if min_avg > 0 else 1
        assert performance_ratio <= 3.0, f"Performance ratio {performance_ratio:.2f}x should be <= 3.0x"
    
    @pytest.mark.performance
    def test_cache_performance(self, sensor):
        """Test cache performance impact."""
        # Clear cache
        sensor.clear_all_caches()
        
        # Test uncached reads
        uncached_times = []
        for i in range(10):
            reading, read_time = measure_read_time(
                sensor.get_pm2_5_standard, use_cache=False
            )
            uncached_times.append(read_time)
        
        # Test cached reads
        cached_times = []
        for i in range(10):
            reading, read_time = measure_read_time(
                sensor.get_pm2_5_standard, use_cache=True
            )
            cached_times.append(read_time)
        
        # Analyze cache performance
        avg_uncached = sum(uncached_times) / len(uncached_times)
        avg_cached = sum(cached_times) / len(cached_times)
        
        # Cache should be faster
        if avg_cached > 0:
            speedup = avg_uncached / avg_cached
            assert speedup >= 2.0, f"Cache speedup {speedup:.2f}x should be >= 2.0x"
        
        # Both should be within reasonable time
        assert avg_uncached <= 0.1, f"Uncached average {avg_uncached:.3f}s should be <= 0.1s"
        assert avg_cached <= 0.05, f"Cached average {avg_cached:.3f}s should be <= 0.05s"


class TestMemoryUsagePerformance:
    """Test memory usage and efficiency."""
    
    @pytest.mark.performance
    def test_memory_usage_stability(self, sensor, performance_tracker):
        """Test memory usage over extended operation."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            # Perform many operations
            for i in range(200):
                # Complete reading with all data
                complete_reading = sensor.get_complete_reading(use_cache=False)
                
                # Store in history periodically
                if i % 20 == 0:
                    history = sensor.get_reading_history()
                    assert len(history) > 0, "Should maintain history"
                
                time.sleep(0.01)
            
            # Check memory usage
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            memory_increase_mb = memory_increase / (1024 * 1024)
            
            # Memory increase should be reasonable
            assert memory_increase_mb <= 25, f"Memory increase {memory_increase_mb:.1f}MB should be <= 25MB"
            
            # Check for memory leaks (rapid increase)
            memory_per_operation = memory_increase / 200
            assert memory_per_operation <= 51200, f"Memory per operation {memory_per_operation} bytes should be reasonable"
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")
    
    @pytest.mark.performance
    def test_history_memory_efficiency(self, sensor):
        """Test memory efficiency of reading history."""
        # Clear history
        sensor.clear_reading_history()
        
        # Add many readings
        num_readings = 100
        for i in range(num_readings):
            reading = sensor.get_complete_reading(use_cache=False)
            # Reading is automatically added to history
        
        # Check history size
        history = sensor.get_reading_history()
        assert len(history) >= num_readings, "Should have all readings in history"
        
        # History should not exceed maximum size
        max_size = sensor.config.get("sensor.max_history_size", 1000)
        assert len(history) <= max_size, "History should not exceed maximum size"
        
        # Test history retrieval performance
        start_time = time.time()
        full_history = sensor.get_reading_history()
        retrieval_time = time.time() - start_time
        
        assert retrieval_time <= 0.1, f"History retrieval {retrieval_time:.3f}s should be fast"
        assert len(full_history) == len(history), "Retrieved history should match"


class TestConcurrentAccessPerformance:
    """Test performance under concurrent access."""
    
    @pytest.mark.performance
    def test_concurrent_read_performance(self, sensor, reading_data):
        """Test performance with concurrent readers."""
        def concurrent_reader(worker_id: int, num_reads: int) -> Dict[str, Any]:
            """Worker function for concurrent reading."""
            results = {
                "worker_id": worker_id,
                "reads": 0,
                "successful_reads": 0,
                "total_time": 0,
                "errors": []
            }
            
            start_time = time.time()
            
            for i in range(num_reads):
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
            
            results["total_time"] = time.time() - start_time
            return results
        
        # Run concurrent workers
        num_workers = 4
        reads_per_worker = 25
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(concurrent_reader, i, reads_per_worker)
                for i in range(num_workers)
            ]
            
            worker_results = [future.result() for future in as_completed(futures)]
        
        # Analyze concurrent performance
        total_reads = sum(result["reads"] for result in worker_results)
        total_successful = sum(result["successful_reads"] for result in worker_results)
        total_errors = sum(len(result["errors"]) for result in worker_results)
        total_time = max(result["total_time"] for result in worker_results)
        
        # Performance metrics
        success_rate = (total_successful / total_reads) * 100 if total_reads > 0 else 0
        reads_per_second = total_reads / total_time if total_time > 0 else 0
        
        # Concurrent performance assertions
        assert success_rate >= 90, f"Concurrent success rate {success_rate}% should be >= 90%"
        assert reads_per_second >= 20, f"Concurrent reads per second {reads_per_second} should be >= 20"
        assert total_errors <= total_reads * 0.1, f"Error rate should be <= 10%"
    
    @pytest.mark.performance
    def test_thread_safety(self, sensor):
        """Test thread safety of sensor operations."""
        def safe_worker(worker_id: int) -> Dict[str, Any]:
            """Worker that tests thread safety."""
            results = {"worker_id": worker_id, "operations": 0, "errors": 0}
            
            for i in range(20):
                try:
                    # Mix of different operations
                    if i % 3 == 0:
                        sensor.get_pm2_5_standard(use_cache=False)
                    elif i % 3 == 1:
                        sensor.get_particles_2_5um(use_cache=False)
                    else:
                        sensor.get_performance_statistics()
                    
                    results["operations"] += 1
                    
                except Exception as e:
                    results["errors"] += 1
            
            return results
        
        # Run multiple threads
        num_threads = 3
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(safe_worker, i) for i in range(num_threads)]
            thread_results = [future.result() for future in as_completed(futures)]
        
        # Analyze thread safety
        total_operations = sum(result["operations"] for result in thread_results)
        total_errors = sum(result["errors"] for result in thread_results)
        
        error_rate = (total_errors / total_operations) * 100 if total_operations > 0 else 0
        
        # Should have minimal errors due to thread safety issues
        assert error_rate <= 5, f"Thread safety error rate {error_rate}% should be <= 5%"


class TestCachePerformance:
    """Test cache performance and efficiency."""
    
    @pytest.mark.performance
    def test_cache_hit_rate(self, sensor):
        """Test cache hit rate and performance."""
        # Clear cache
        sensor.clear_all_caches()
        
        # Populate cache with different parameters
        parameters = [
            sensor.get_pm1_0_standard,
            sensor.get_pm2_5_standard,
            sensor.get_pm10_standard,
            sensor.get_particles_0_3um,
            sensor.get_particles_2_5um,
        ]
        
        # Initial reads to populate cache
        for func in parameters:
            func(use_cache=False)
        
        # Test cache hits
        cache_hits = 0
        total_cache_tests = 20
        
        for i in range(total_cache_tests):
            func = parameters[i % len(parameters)]
            reading1 = func(use_cache=False)  # Fresh read
            reading2 = func(use_cache=True)   # Cached read
            
            if reading1 == reading2:
                cache_hits += 1
        
        # Cache performance
        hit_rate = (cache_hits / total_cache_tests) * 100
        assert hit_rate >= 80, f"Cache hit rate {hit_rate}% should be >= 80%"
    
    @pytest.mark.performance
    def test_cache_memory_usage(self, sensor):
        """Test cache memory efficiency."""
        # Clear cache
        sensor.clear_all_caches()
        
        # Populate cache with many different readings
        for i in range(50):
            sensor.get_pm2_5_standard(use_cache=False)
            time.sleep(0.01)  # Allow cache timeout to expire some entries
        
        # Get cache info
        cache_info = sensor.get_performance_statistics()["cache_info"]
        
        # Should have reasonable cache size
        concentration_cache = cache_info.get("concentration_cache", {})
        particle_cache = cache_info.get("particle_count_cache", {})
        
        # Cache should not grow unbounded
        total_cached_entries = len(concentration_cache) + len(particle_cache)
        assert total_cached_entries <= 20, f"Cache size {total_cached_entries} should be reasonable"
        
        # Cache entries should have valid timestamps
        for cache_type, cache_data in [("concentration", concentration_cache), ("particle", particle_cache)]:
            for register, entry in cache_data.items():
                assert "timestamp" in entry, f"{cache_type} cache entry should have timestamp"
                assert "value" in entry, f"{cache_type} cache entry should have value"
                assert "valid" in entry, f"{cache_type} cache entry should have validity flag"


class TestComparisonPerformance:
    """Test performance benchmarks for our implementation."""
    
    @pytest.mark.performance
    def test_performance_benchmarks(self, sensor):
        """Test performance benchmarks for our implementation."""
        
        # Test our API performance
        our_times = []
        for i in range(20):
            reading, read_time = measure_read_time(
                sensor.get_pm2_5_standard, use_cache=False
            )
            our_times.append(read_time)
        
        our_avg = sum(our_times) / len(our_times)
        our_max = max(our_times)
        
        # Performance should be reasonable
        assert our_max <= 1.0, f"Our API max time {our_max:.3f}s should be <= 1.0s"
        assert our_avg <= 0.2, f"Our API average {our_avg:.3f}s should be <= 0.2s"
        
        # Maximum times should be reasonable
        assert our_max <= 0.5, f"Our API max {our_max:.3f}s should be <= 0.5s"


class TestPerformanceRegression:
    """Test for performance regressions."""
    
    @pytest.mark.performance
    def test_performance_regression_detection(self, sensor):
        """Test for performance regressions over time."""
        # Baseline performance test
        baseline_times = []
        for i in range(30):
            reading, read_time = measure_read_time(
                sensor.get_pm2_5_standard, use_cache=False
            )
            baseline_times.append(read_time)
        
        baseline_avg = sum(baseline_times) / len(baseline_times)
        
        # Extended operation test
        extended_times = []
        for i in range(100):
            reading, read_time = measure_read_time(
                sensor.get_pm2_5_standard, use_cache=False
            )
            extended_times.append(read_time)
            
            # Periodic check for performance degradation
            if (i + 1) % 25 == 0:
                recent_avg = sum(extended_times[-25:]) / 25
                degradation_ratio = recent_avg / baseline_avg if baseline_avg > 0 else 1
                
                # Performance should not degrade significantly
                assert degradation_ratio <= 3.0, f"Performance degradation {degradation_ratio:.2f}x should be <= 3.0x"
        
        # Overall performance should be consistent
        overall_avg = sum(extended_times) / len(extended_times)
        overall_ratio = overall_avg / baseline_avg if baseline_avg > 0 else 1
        
        assert overall_ratio <= 2.0, f"Overall performance ratio {overall_ratio:.2f}x should be <= 2.0x"
    
    @pytest.mark.performance
    def test_stress_performance(self, sensor):
        """Test performance under stress conditions."""
        stress_duration = 10  # seconds
        target_reads_per_second = 10
        
        readings_taken = 0
        errors = 0
        start_time = time.time()
        
        while time.time() - start_time < stress_duration:
            try:
                reading = sensor.get_pm2_5_standard(use_cache=False)
                if reading >= 0:
                    readings_taken += 1
                else:
                    errors += 1
                    
            except Exception:
                errors += 1
            
            # Small delay to achieve target rate
            time.sleep(1.0 / target_reads_per_second)
        
        actual_duration = time.time() - start_time
        actual_reads_per_second = readings_taken / actual_duration
        error_rate = (errors / (readings_taken + errors)) * 100 if (readings_taken + errors) > 0 else 0
        
        # Stress performance assertions
        assert actual_reads_per_second >= target_reads_per_second * 0.8, f"Stress reads/sec {actual_reads_per_second:.1f} should be >= {target_reads_per_second * 0.8}"
        assert error_rate <= 10, f"Stress error rate {error_rate}% should be <= 10%"
        assert readings_taken >= stress_duration * target_reads_per_second * 0.7, f"Should achieve reasonable throughput under stress"