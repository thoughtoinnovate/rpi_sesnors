"""
End-to-End Integration Tests for PM25 Sensor

This module tests complete workflows and real-world usage scenarios.
All tests use real hardware - no mocks allowed.

Test Areas:
- Complete sensor workflows
- Real-world usage patterns
- Long-term stability
- Data analysis and reporting
- Configuration management
"""

import pytest
import time
import json
import tempfile
from pathlib import Path

from .conftest import (
    validate_reading_range, measure_read_time, wait_for_sensor_stabilization
)


class TestCompleteSensorWorkflow:
    """Test complete sensor initialization and operation workflows."""
    
    @pytest.mark.integration
    def test_full_initialization_workflow(self, test_config):
        """Test complete sensor initialization workflow."""
        from apis import PM25Sensor
        
        # Create sensor without auto-initialization
        sensor = PM25Sensor(config=test_config, auto_connect=False, auto_warmup=False)
        
        # Step 1: Manual initialization
        assert not sensor.is_connected(), "Should not be connected initially"
        assert not sensor.is_initialized(), "Should not be initialized initially"
        
        # Step 2: Connect
        init_result = sensor.initialize()
        assert init_result, "Initialization should succeed"
        assert sensor.is_connected(), "Should be connected after initialization"
        assert sensor.is_initialized(), "Should be initialized after initialization"
        
        # Step 3: Verify firmware version
        version = sensor.get_firmware_version()
        assert version != -1, "Should get valid firmware version"
        
        # Step 4: Take readings
        pm25 = sensor.get_pm2_5_standard()
        assert pm25 >= 0, "Should get valid PM2.5 reading"
        
        # Step 5: Get complete reading
        complete = sensor.get_complete_reading()
        assert "timestamp" in complete, "Complete reading should have timestamp"
        assert "concentrations" in complete, "Complete reading should have concentrations"
        assert "particle_counts" in complete, "Complete reading should have particle counts"
        assert "air_quality_index" in complete, "Complete reading should have AQI"
        
        # Step 6: Cleanup
        sensor.disconnect()
        assert not sensor.is_connected(), "Should be disconnected after cleanup"
    
    @pytest.mark.integration
    def test_context_manager_workflow(self, test_config):
        """Test sensor usage with context manager."""
        from apis import PM25Sensor
        
        # Test context manager
        with PM25Sensor(config=test_config) as sensor:
            assert sensor.is_initialized(), "Should be initialized in context"
            assert sensor.is_connected(), "Should be connected in context"
            
            # Take readings
            reading = sensor.get_air_quality_summary()
            assert "pm25_standard" in reading, "Should have PM2.5 data"
            assert "aqi_level" in reading, "Should have AQI level"
        
        # Should be disconnected after context exit
        assert not sensor.is_connected(), "Should be disconnected after context exit"
    
    @pytest.mark.integration
    def test_power_management_workflow(self, sensor):
        """Test complete power management workflow."""
        # Ensure sensor is awake
        if sensor.is_sleeping():
            sensor.wake_from_sleep()
            time.sleep(1)
        
        # Take baseline reading
        baseline_reading = sensor.get_pm2_5_standard()
        assert baseline_reading >= 0, "Should get baseline reading"
        
        # Enter sleep mode
        sleep_result = sensor.enter_sleep_mode()
        if sleep_result:
            assert sensor.is_sleeping(), "Should be in sleep mode"
            
            # Try reading during sleep (might fail or return cached data)
            time.sleep(1)
            try:
                sleep_reading = sensor.get_pm2_5_standard()
                # Reading during sleep might be limited
            except Exception:
                pass  # Expected during sleep
            
            # Wake from sleep
            wake_result = sensor.wake_from_sleep()
            assert wake_result, "Should wake successfully"
            assert not sensor.is_sleeping(), "Should be awake after wake"
            
            # Wait for stabilization
            time.sleep(2)
            
            # Verify sensor is responsive after wake
            post_wake_reading = sensor.get_pm2_5_standard()
            assert post_wake_reading >= 0, "Should get reading after wake"
    
    @pytest.mark.integration
    def test_complete_data_collection_workflow(self, sensor):
        """Test complete data collection and analysis workflow."""
        # Collect multiple readings
        readings = []
        num_readings = 5
        
        for i in range(num_readings):
            # Get complete reading
            complete_reading = sensor.get_complete_reading(use_cache=False)
            readings.append(complete_reading)
            
            # Validate structure
            assert "timestamp" in complete_reading
            assert "concentrations" in complete_reading
            assert "particle_counts" in complete_reading
            assert "air_quality_index" in complete_reading
            
            # Validate data
            pm25 = complete_reading["concentrations"]["standard"]["PM2.5"]
            assert pm25 >= 0, f"Reading {i}: PM2.5 should be valid"
            
            time.sleep(0.5)
        
        # Get reading history
        history = sensor.get_reading_history()
        assert len(history) >= num_readings, "Should have reading history"
        
        # Get statistics
        stats = sensor.get_reading_statistics()
        assert "pm2_5_standard" in stats, "Should have PM2.5 statistics"
        
        # Test data export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = Path(f.name)
        
        try:
            # Save readings to file
            save_result = sensor.save_readings_to_file(temp_file, "json")
            assert save_result, "Should save readings successfully"
            
            # Verify file was created and contains valid data
            assert temp_file.exists(), "File should exist"
            
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)
            
            assert isinstance(saved_data, list), "Should save list of readings"
            assert len(saved_data) >= num_readings, "Should save all readings"
            
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()


class TestRealWorldUsagePatterns:
    """Test real-world usage patterns and scenarios."""
    
    @pytest.mark.integration
    def test_continuous_monitoring_pattern(self, sensor):
        """Test continuous monitoring usage pattern."""
        monitoring_duration = 10  # seconds
        reading_interval = 1.0  # seconds
        
        readings = []
        start_time = time.time()
        
        while time.time() - start_time < monitoring_duration:
            try:
                # Get air quality summary
                summary = sensor.get_air_quality_summary(use_cache=False)
                readings.append(summary)
                
                # Validate summary
                assert "pm25_standard" in summary
                assert "aqi_level" in summary
                assert summary["pm25_standard"] >= 0
                
                time.sleep(reading_interval)
                
            except Exception as e:
                # Log but continue monitoring
                print(f"Monitoring error: {e}")
        
        # Analyze collected data
        assert len(readings) >= monitoring_duration * 0.8, "Should collect most readings"
        
        # Check data consistency
        pm25_values = [r["pm25_standard"] for r in readings]
        assert all(v >= 0 for v in pm25_values), "All PM2.5 values should be valid"
    
    @pytest.mark.integration
    def test_periodic_sampling_pattern(self, sensor):
        """Test periodic sampling with power saving."""
        num_cycles = 3
        sample_duration = 2  # seconds
        sleep_duration = 1  # seconds
        
        for cycle in range(num_cycles):
            # Wake sensor (if sleeping)
            if sensor.is_sleeping():
                sensor.wake_from_sleep()
                time.sleep(1)
            
            # Take samples
            samples = []
            sample_start = time.time()
            
            while time.time() - sample_start < sample_duration:
                reading = sensor.get_pm2_5_standard(use_cache=False)
                samples.append(reading)
                time.sleep(0.5)
            
            # Validate samples
            valid_samples = [s for s in samples if s >= 0]
            assert len(valid_samples) > 0, f"Cycle {cycle+1}: Should have valid samples"
            
            # Enter sleep mode between cycles
            if cycle < num_cycles - 1:  # Don't sleep after last cycle
                sensor.enter_sleep_mode()
                time.sleep(sleep_duration)
        
        # Ensure sensor is awake at the end
        if sensor.is_sleeping():
            sensor.wake_from_sleep()
    
    @pytest.mark.integration
    def test_burst_reading_pattern(self, sensor):
        """Test burst reading pattern for rapid data collection."""
        burst_size = 10
        burst_interval = 0.1  # seconds
        
        # Clear cache to ensure fresh readings
        sensor.clear_all_caches()
        
        # Take burst of readings
        burst_readings = []
        for i in range(burst_size):
            start_time = time.time()
            
            # Get multiple parameters in burst
            pm25 = sensor.get_pm2_5_standard(use_cache=False)
            pm10 = sensor.get_pm10_standard(use_cache=False)
            particles = sensor.get_particles_2_5um(use_cache=False)
            
            end_time = time.time()
            read_time = end_time - start_time
            
            burst_readings.append({
                "pm25": pm25,
                "pm10": pm10,
                "particles": particles,
                "read_time": read_time
            })
            
            # Validate reading
            assert pm25 >= 0, f"Burst reading {i}: PM2.5 should be valid"
            assert pm10 >= 0, f"Burst reading {i}: PM10 should be valid"
            assert particles >= 0, f"Burst reading {i}: Particles should be valid"
            assert read_time <= 0.5, f"Burst reading {i}: Should be fast"
            
            time.sleep(burst_interval)
        
        # Analyze burst performance
        avg_read_time = sum(r["read_time"] for r in burst_readings) / len(burst_readings)
        assert avg_read_time <= 0.2, f"Average burst read time {avg_read_time:.3f}s should be fast"
    
    @pytest.mark.integration
    def test_multi_parameter_monitoring(self, sensor):
        """Test monitoring multiple parameters simultaneously."""
        monitoring_duration = 5  # seconds
        interval = 0.5  # seconds
        
        readings = []
        start_time = time.time()
        
        while time.time() - start_time < monitoring_duration:
            # Get all parameters
            complete_reading = sensor.get_complete_reading(use_cache=False)
            readings.append(complete_reading)
            
            # Validate all data types
            concentrations = complete_reading["concentrations"]
            particle_counts = complete_reading["particle_counts"]
            aqi_info = complete_reading["air_quality_index"]
            
            # Validate concentrations
            for conc_type in ["standard", "atmospheric"]:
                for size in ["PM1.0", "PM2.5", "PM10"]:
                    value = concentrations[conc_type][size]
                    assert value >= 0, f"{conc_type} {size} should be valid"
            
            # Validate particle counts
            for size in ["0.3um", "0.5um", "1.0um", "2.5um", "5.0um", "10um"]:
                value = particle_counts[size]
                assert value >= 0, f"Particle count {size} should be valid"
            
            # Validate AQI
            assert "aqi_level" in aqi_info
            assert "aqi_value" in aqi_info
            
            time.sleep(interval)
        
        # Should have collected multiple readings
        assert len(readings) >= 3, "Should collect multiple readings"


class TestLongTermStability:
    """Test long-term stability and reliability."""
    
    @pytest.mark.integration
    def test_extended_operation_stability(self, sensor):
        """Test stability over extended operation (shortened for testing)."""
        test_duration = 30  # Shortened for testing (real test: 3600+)
        reading_interval = 2.0  # seconds
        
        readings = []
        errors = []
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            try:
                reading = sensor.get_pm2_5_standard(use_cache=False)
                timestamp = time.time()
                
                readings.append({
                    "timestamp": timestamp,
                    "value": reading
                })
                
                assert reading >= 0, f"Reading at {timestamp - start_time:.1f}s should be valid"
                
            except Exception as e:
                errors.append({
                    "timestamp": time.time(),
                    "error": str(e)
                })
            
            time.sleep(reading_interval)
        
        # Analyze stability
        total_readings = len(readings)
        total_errors = len(errors)
        success_rate = (total_readings / (total_readings + total_errors)) * 100 if (total_readings + total_errors) > 0 else 0
        
        assert success_rate >= 90, f"Success rate {success_rate}% should be >= 90%"
        assert total_readings >= test_duration / reading_interval * 0.8, "Should collect most readings"
        
        # Check reading consistency
        values = [r["value"] for r in readings]
        if len(values) >= 2:
            variance = max(values) - min(values)
            # Allow reasonable variance
            assert variance <= 200, f"Reading variance {variance} should be reasonable"
    
    @pytest.mark.integration
    def test_memory_leak_detection(self, sensor):
        """Test for memory leaks during extended operation."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            # Perform many operations
            for i in range(100):
                # Complete reading with all data
                complete_reading = sensor.get_complete_reading(use_cache=False)
                
                # Store in history (test memory management)
                if i % 10 == 0:
                    history = sensor.get_reading_history()
                    assert len(history) > 0, "Should maintain history"
                
                time.sleep(0.01)
            
            # Check memory usage
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            memory_increase_mb = memory_increase / (1024 * 1024)
            
            # Memory increase should be reasonable
            assert memory_increase_mb <= 20, f"Memory increase {memory_increase_mb:.1f}MB should be <= 20MB"
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")
    
    @pytest.mark.integration
    def test_performance_consistency(self, sensor):
        """Test performance consistency over time."""
        read_times = []
        num_readings = 50
        
        for i in range(num_readings):
            start_time = time.time()
            reading = sensor.get_pm2_5_standard(use_cache=False)
            end_time = time.time()
            
            read_time = end_time - start_time
            read_times.append(read_time)
            
            assert reading >= 0, f"Reading {i} should be valid"
            
            time.sleep(0.1)
        
        # Analyze performance consistency
        avg_time = sum(read_times) / len(read_times)
        max_time = max(read_times)
        min_time = min(read_times)
        
        # Performance should be consistent
        assert avg_time <= 0.1, f"Average time {avg_time:.3f}s should be <= 0.1s"
        assert max_time <= 1.0, f"Max time {max_time:.3f}s should be <= 1.0s"
        
        # Variance should be reasonable
        variance_ratio = max_time / min_time if min_time > 0 else 1
        assert variance_ratio <= 10, f"Performance variance {variance_ratio:.1f}x should be reasonable"


class TestConfigurationManagement:
    """Test configuration management in real scenarios."""
    
    @pytest.mark.integration
    def test_dynamic_configuration_changes(self, sensor):
        """Test dynamic configuration changes."""
        # Test cache timeout changes
        original_timeout = sensor.config.get("performance.cache_timeout")
        
        # Change cache timeout
        sensor.config.set("performance.cache_timeout", 0.1)
        
        # Take reading (should cache)
        reading1 = sensor.get_pm2_5_standard(use_cache=True)
        
        # Immediate second reading (should use cache)
        reading2 = sensor.get_pm2_5_standard(use_cache=True)
        
        # Should be identical (from cache)
        assert reading1 == reading2, "Cached readings should be identical"
        
        # Wait for cache to expire
        time.sleep(0.2)
        
        # Take another reading (cache expired)
        reading3 = sensor.get_pm2_5_standard(use_cache=True)
        
        # Restore original timeout
        sensor.config.set("performance.cache_timeout", original_timeout)
    
    @pytest.mark.integration
    def test_configuration_persistence(self, test_config):
        """Test configuration persistence across sensor instances."""
        from apis import PM25Sensor
        
        # Create sensor with custom config
        custom_config = test_config.copy()
        custom_config.set("sensor.max_pm_concentration", 500)
        
        sensor1 = PM25Sensor(config=custom_config)
        assert sensor1.config.get("sensor.max_pm_concentration") == 500
        
        # Create another sensor with same config
        sensor2 = PM25Sensor(config=custom_config)
        assert sensor2.config.get("sensor.max_pm_concentration") == 500
        
        # Cleanup
        sensor1.disconnect()
        sensor2.disconnect()


class TestDataAnalysisAndReporting:
    """Test data analysis and reporting capabilities."""
    
    @pytest.mark.integration
    def test_air_quality_analysis(self, sensor):
        """Test air quality analysis features."""
        # Get complete reading
        complete_reading = sensor.get_complete_reading()
        
        # Validate AQI calculation
        aqi_info = complete_reading["air_quality_index"]
        assert "aqi_level" in aqi_info
        assert "aqi_value" in aqi_info
        assert "health_message" in aqi_info
        
        # Validate particle analysis
        particle_analysis = complete_reading["particle_analysis"]
        assert "dominant_size" in particle_analysis
        assert "total_particles" in particle_analysis
        
        # Get air quality summary
        summary = sensor.get_air_quality_summary()
        assert "pm25_standard" in summary
        assert "aqi_level" in summary
        assert "health_message" in summary
        assert "dominant_particle_size" in summary
    
    @pytest.mark.integration
    def test_performance_statistics(self, sensor):
        """Test performance statistics tracking."""
        # Get initial statistics
        initial_stats = sensor.get_performance_statistics()
        initial_reads = initial_stats["total_readings"]
        
        # Perform some operations
        for i in range(10):
            sensor.get_pm2_5_standard(use_cache=False)
            time.sleep(0.1)
        
        # Get updated statistics
        final_stats = sensor.get_performance_statistics()
        final_reads = final_stats["total_readings"]
        
        # Verify statistics updated
        reads_increase = final_reads - initial_reads
        assert reads_increase >= 8, f"Should have increased reads by ~10, got {reads_increase}"
        
        # Verify other statistics
        assert "error_rate" in final_stats
        assert "i2c_statistics" in final_stats
        assert "cache_info" in final_stats
        
        # Reset statistics
        sensor.reset_statistics()
        reset_stats = sensor.get_performance_statistics()
        assert reset_stats["total_readings"] == 0, "Should reset reads to 0"
    
    @pytest.mark.integration
    def test_data_export_functionality(self, sensor):
        """Test data export in different formats."""
        # Collect some data
        for i in range(5):
            sensor.get_complete_reading(use_cache=False)
            time.sleep(0.2)
        
        # Test JSON export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_file = Path(f.name)
        
        try:
            result = sensor.save_readings_to_file(json_file, "json")
            assert result, "JSON export should succeed"
            assert json_file.exists(), "JSON file should exist"
            
            # Validate JSON content
            with open(json_file, 'r') as f:
                data = json.load(f)
            assert isinstance(data, list), "JSON should contain list"
            assert len(data) >= 5, "Should export all readings"
            
        finally:
            if json_file.exists():
                json_file.unlink()
        
        # Test CSV export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_file = Path(f.name)
        
        try:
            result = sensor.save_readings_to_file(csv_file, "csv")
            assert result, "CSV export should succeed"
            assert csv_file.exists(), "CSV file should exist"
            
            # Validate CSV content
            with open(csv_file, 'r') as f:
                content = f.read()
            assert len(content) > 0, "CSV should have content"
            assert "timestamp" in content, "CSV should have headers"
            
        finally:
            if csv_file.exists():
                csv_file.unlink()