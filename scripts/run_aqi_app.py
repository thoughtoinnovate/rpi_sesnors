#!/usr/bin/env python3
"""
AQI App Launcher

Convenient launcher script to run the AQI monitoring application
from the project root directory.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import and run the AQI app example
from app.aqi_app_example import main

if __name__ == "__main__":
    print("🚀 Launching AQI Monitoring App...")
    app_dir = parent_dir / "app"
    print(f"📂 App directory: {app_dir}")
    print(f"📊 Database: {app_dir / 'aqi_demo.db'}")
    print()

    main()