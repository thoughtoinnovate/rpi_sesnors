"""
AQI Scheduler Module

Automated air quality monitoring scheduler that runs at specified intervals
and collects sensor readings for configured locations.

Features:
- Flexible time interval parsing (e.g., '1h2m1s', '30m', '45s')
- Continuous monitoring with graceful shutdown
- Integration with AQIApp for data storage
- Comprehensive logging and error handling
- Real-time status reporting
"""

import re
import time
import signal
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Import from parent directory
import sys
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from sensors.pm25_sensor import PM25Sensor


class TimeParser:
    """Parse time strings like '1h2m1s' into seconds."""

    @staticmethod
    def parse_time_interval(time_str: str) -> int:
        """
        Parse time format: 1h2m1s -> 3721 seconds

        Args:
            time_str: Time string (e.g., '1h2m1s', '30m', '45s')

        Returns:
            Total seconds

        Raises:
            ValueError: If time format is invalid or interval is zero
        """
        if not time_str or not isinstance(time_str, str):
            raise ValueError("Time string cannot be empty")

        # Regex to match hours, minutes, seconds
        pattern = r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
        match = re.match(pattern, time_str.lower().strip())

        if not match:
            raise ValueError(f"Invalid time format: {time_str}. Use format like '1h2m1s', '30m', or '45s'")

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        total_seconds = hours * 3600 + minutes * 60 + seconds

        if total_seconds == 0:
            raise ValueError("Time interval cannot be zero")

        if total_seconds < 10:
            raise ValueError("Minimum interval is 10 seconds")

        return total_seconds

    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format seconds back into readable duration string."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")

        return "".join(parts)


class AQIScheduler:
    """
    Automated AQI monitoring scheduler.

    Runs continuously at specified intervals, taking sensor readings
    and storing them in the database for the configured location.
    """

    def __init__(self, location_name: str, interval_seconds: int, db_path: str = "aqi_monitoring.db"):
        """
        Initialize the AQI scheduler.

        Args:
            location_name: Name of the location to monitor
            interval_seconds: Interval between readings in seconds
            db_path: Path to the SQLite database file
        """
        self.location_name = location_name
        self.interval_seconds = interval_seconds
        self.db_path = db_path
        self.running = False
        self.readings_taken = 0
        self.start_time = None
        self.last_reading_time = None

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info(f"AQI Scheduler initialized for location '{location_name}'")
        self.logger.info(f"Interval: {interval_seconds} seconds ({TimeParser.format_duration(interval_seconds)})")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        self.logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        self.running = False

    def run(self) -> bool:
        """
        Run the scheduler continuously until stopped.

        Returns:
            True if completed successfully, False if interrupted
        """
        self.logger.info("=" * 60)
        self.logger.info("STARTING AQI MONITORING SCHEDULER")
        self.logger.info("=" * 60)
        self.logger.info(f"Location: {self.location_name}")
        self.logger.info(f"Interval: {TimeParser.format_duration(self.interval_seconds)}")
        self.logger.info(f"Database: {self.db_path}")
        self.logger.info("Press Ctrl+C to stop gracefully")
        self.logger.info("=" * 60)

        self.running = True
        self.start_time = time.time()
        success = True

        try:
            while self.running:
                cycle_start = time.time()

                # Take reading
                reading_success = self._take_reading()

                if not reading_success:
                    self.logger.warning("Reading failed, but continuing scheduler")

                # Calculate next run time
                cycle_elapsed = time.time() - cycle_start
                sleep_time = max(0, self.interval_seconds - cycle_elapsed)

                if sleep_time > 0:
                    self.logger.debug(f"Next reading in {TimeParser.format_duration(int(sleep_time))}")
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"Reading took {cycle_elapsed:.1f}s, longer than interval {self.interval_seconds}s")

        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
            success = False
        finally:
            self._print_final_stats()
            return success

    def _take_reading(self) -> bool:
        """
        Take a single reading and store it in the database.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from .aqi_app import AQIApp

            with AQIApp(self.db_path) as app:
                self.logger.debug(f"Taking reading for location '{self.location_name}'")

                result = app.take_reading(self.location_name)

                if result:
                    self.readings_taken += 1
                    self.last_reading_time = time.time()

                    reading = result['reading']
                    aqi = result['aqi']

                    pm25 = reading['concentrations']['atmospheric']['PM2.5']
                    pm10 = reading['concentrations']['atmospheric']['PM10']
                    aqi_value = aqi['aqi_value']
                    aqi_level = aqi['aqi_level']

                    self.logger.info(
                        f"✅ Reading #{self.readings_taken}: "
                        f"PM2.5={pm25:.1f} μg/m³, PM10={pm10:.1f} μg/m³, "
                        f"AQI={aqi_value} ({aqi_level})"
                    )

                    return True
                else:
                    self.logger.error("❌ Failed to take reading")
                    return False

        except Exception as e:
            self.logger.error(f"❌ Error taking reading: {e}")
            return False

    def _print_final_stats(self):
        """Print final statistics when scheduler stops."""
        if self.start_time:
            runtime = time.time() - self.start_time
            runtime_str = TimeParser.format_duration(int(runtime))

            self.logger.info("=" * 60)
            self.logger.info("SCHEDULER STOPPED")
            self.logger.info("=" * 60)
            self.logger.info(f"Total readings taken: {self.readings_taken}")
            self.logger.info(f"Total runtime: {runtime_str}")

            if self.readings_taken > 0:
                avg_interval = runtime / self.readings_taken
                self.logger.info(f"Average interval: {avg_interval:.1f} seconds")
                readings_per_hour = (self.readings_taken / runtime) * 3600
                self.logger.info(f"Readings per hour: {readings_per_hour:.1f}")

            self.logger.info("=" * 60)

    def get_status(self) -> dict:
        """
        Get current scheduler status.

        Returns:
            Dictionary with status information
        """
        status = {
            'running': self.running,
            'location': self.location_name,
            'interval_seconds': self.interval_seconds,
            'readings_taken': self.readings_taken,
            'start_time': self.start_time,
            'last_reading_time': self.last_reading_time
        }

        if self.start_time:
            status['runtime_seconds'] = time.time() - self.start_time

        if self.last_reading_time and self.start_time:
            status['average_interval'] = (time.time() - self.start_time) / self.readings_taken

        return status


def create_scheduler(location_name: str, interval_str: str, db_path: str = "aqi_monitoring.db") -> AQIScheduler:
    """
    Create a scheduler instance with parsed interval.

    Args:
        location_name: Name of location to monitor
        interval_str: Time interval string (e.g., '1h2m1s')
        db_path: Database file path

    Returns:
        Configured AQIScheduler instance
    """
    interval_seconds = TimeParser.parse_time_interval(interval_str)
    return AQIScheduler(location_name, interval_seconds, db_path)