#!/usr/bin/env python3
"""
AQI REST API Server Launcher

Lightweight Flask server for Raspberry Pi 3 air quality monitoring.
Optimized for low resource usage and reliable operation.

Usage:
    python run.py                    # Run on default host/port
    python run.py --host 0.0.0.0     # Bind to all interfaces
    python run.py --port 8080        # Custom port
    AQI_DB_PATH=/path/to/db.db python run.py  # Custom database
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directories to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))

from app.rest_api.app import app


def main():
    """Launch the AQI REST API server."""
    parser = argparse.ArgumentParser(
        description="AQI REST API Server for Raspberry Pi 3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  AQI_DB_PATH    Path to SQLite database file
                 Default: ../aqi_demo.db

Examples:
  python run.py
  python run.py --host 0.0.0.0 --port 8080
  AQI_DB_PATH=/home/pi/aqi_data.db python run.py
        """
    )

    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind server to (default: 127.0.0.1)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind server to (default: 5000)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (not recommended for production)'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Number of worker threads (default: 1 for RPi)'
    )

    args = parser.parse_args()

    # Display startup information
    print("🚀 AQI REST API Server")
    print("=" * 40)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Debug: {args.debug}")
    print(f"Workers: {args.workers}")
    print(f"Database: {os.getenv('AQI_DB_PATH', '../aqi_demo.db')}")
    print("=" * 40)

    # Validate database exists
    db_path = os.getenv('AQI_DB_PATH', str(current_dir.parent / 'aqi_demo.db'))
    if not os.path.exists(db_path):
        print(f"⚠️  Warning: Database file not found at {db_path}")
        print("   The API will still start, but endpoints may return errors")
        print()

    print("Starting server... (Press Ctrl+C to stop)")
    print(f"API will be available at: http://{args.host}:{args.port}")
    print()

    try:
        # Start Flask server
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=(args.workers > 1),  # Use threading for multiple workers
            processes=1  # Keep single process for RPi stability
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        print("Thank you for using AQI REST API! 👋")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()