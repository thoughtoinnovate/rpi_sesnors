#!/usr/bin/env python3
"""
AQI App Launcher

Convenient launcher script to run the AQI monitoring application
from the project root directory.
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

# Import and run the AQI app example
from aqi_app_example import main

if __name__ == "__main__":
    print("🚀 Launching AQI Monitoring App...")
    print(f"📂 App directory: {app_dir}")
    print(f"📊 Database: {app_dir / 'aqi_demo.db'}")
    print()

    main()