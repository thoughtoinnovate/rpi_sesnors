#!/usr/bin/env python3
"""
AQI Scheduler Runner

Command-line interface for running the AQI monitoring scheduler.

Usage:
    python run_scheduler.py "Home Office" "30m"
    python run_scheduler.py "Backyard" "1h15m"
    python run_scheduler.py "Living Room" "5m30s"

Features:
- Flexible time interval parsing
- Location-based monitoring
- Graceful shutdown handling
- Comprehensive logging
- Real-time status updates
"""

import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from aqi.scheduler import AQIScheduler, TimeParser


def setup_logging(log_level: str = 'INFO'):
    """Setup logging configuration."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def validate_location(db_path: str, location_name: str) -> bool:
    """Validate that the location exists in the database."""
    try:
        from aqi.aqi_app import AQIDatabase
        with AQIDatabase(db_path) as db:
            location = db.get_location_by_name(location_name)
            return location is not None
    except Exception:
        return False


def main():
    """Main entry point for the scheduler."""
    parser = argparse.ArgumentParser(
        description="AQI Monitoring Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scheduler.py "Home Office" "30m"
  python run_scheduler.py "Backyard" "1h15m"
  python run_scheduler.py "Living Room" "5m30s"

Time format: Use combinations of:
  - h: hours (e.g., 2h)
  - m: minutes (e.g., 30m)
  - s: seconds (e.g., 45s)

Examples: '1h2m1s', '30m', '45s', '2h', '90m'
        """
    )

    parser.add_argument(
        "location",
        help="Location name to monitor (must exist in database)"
    )
    parser.add_argument(
        "interval",
        help="Time interval between readings (e.g., '1h2m1s', '30m', '45s')"
    )
    parser.add_argument(
        "--db",
        default="aqi_monitoring.db",
        help="Database file path (default: aqi_monitoring.db)"
    )
    parser.add_argument(
        "--log-level",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--dry-run",
        action='store_true',
        help="Validate configuration without starting scheduler"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        # Validate location exists
        if not validate_location(args.db, args.location):
            logger.error(f"❌ Location '{args.location}' not found in database '{args.db}'")
            logger.info("💡 Use the AQI app to add locations first:")
            logger.info("   python run_aqi_app.py")
            sys.exit(1)

        # Parse and validate interval
        interval_seconds = TimeParser.parse_time_interval(args.interval)
        interval_formatted = TimeParser.format_duration(interval_seconds)

        # Display configuration
        print("🚀 AQI Monitoring Scheduler")
        print("=" * 40)
        print(f"📍 Location: {args.location}")
        print(f"⏰ Interval: {args.interval} ({interval_formatted})")
        print(f"💾 Database: {args.db}")
        print(f"📝 Log Level: {args.log_level}")
        print("=" * 40)

        if args.dry_run:
            print("✅ Dry run - Configuration validated successfully!")
            print("💡 Remove --dry-run to start actual monitoring")
            return

        print("🟢 Starting scheduler... (Press Ctrl+C to stop)")
        print()

        # Create and run scheduler
        scheduler = AQIScheduler(args.location, interval_seconds, args.db)
        success = scheduler.run()

        if success:
            print("\n✅ Scheduler completed successfully")
        else:
            print("\n❌ Scheduler stopped due to errors")
            sys.exit(1)

    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Scheduler stopped by user (Ctrl+C)")
        print("Thank you for using AQI Scheduler! 👋")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()