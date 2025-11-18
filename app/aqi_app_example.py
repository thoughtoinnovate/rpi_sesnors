"""
AQI App Example

Demonstrates the AQI monitoring application with SQLite database storage.
Shows how to add locations, take readings, and query historical data.

Features demonstrated:
- Adding monitoring locations
- Taking sensor readings with AQI calculations
- Querying historical data
- Dashboard data retrieval
- Data export functionality
"""

import sys
import time
from pathlib import Path

# Add the parent directory to path for imports (to access sensors/ and aqi/)
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from aqi.aqi_app import AQIApp, quick_reading


def main():
    """Main demonstration function."""
    print("=== AQI Monitoring App Example ===\n")

    try:
        # Initialize AQI app
        print("1. Initializing AQI monitoring application...")
        app = AQIApp("aqi_demo.db")
        print("   Database initialized successfully\n")

        # Add monitoring locations
        print("2. Adding monitoring locations...")
        try:
            home_id = app.add_monitoring_location(
                name="Home Office",
                latitude=40.7128,
                longitude=-74.0060,
                city="New York",
                country="USA",
                description="Main monitoring location"
            )
            print(f"   Added location: Home Office (ID: {home_id})")
        except Exception as e:
            print(f"   Error adding Home Office: {e}")
            home_id = None

        try:
            outdoor_id = app.add_monitoring_location(
                name="Backyard",
                latitude=40.7130,
                longitude=-74.0062,
                city="New York",
                country="USA",
                description="Outdoor air quality monitoring"
            )
            print(f"   Added location: Backyard (ID: {outdoor_id})")
        except Exception as e:
            print(f"   Error adding Backyard: {e}")
            outdoor_id = None

        print()

        # Take readings at different locations
        print("3. Taking sensor readings...")

        print("   Taking reading at Home Office...")
        home_reading = app.take_reading("Home Office")
        if home_reading:
            print("   ✓ Reading stored successfully")
            print(f"     PM2.5: {home_reading['reading']['concentrations']['atmospheric']['PM2.5']} μg/m³")
            print(f"     AQI: {home_reading['aqi']['aqi_value']} ({home_reading['aqi']['aqi_level']})")
        else:
            print("   ✗ Failed to take reading at Home Office")

        time.sleep(2)  # Brief pause between readings

        print("\n   Taking reading at Backyard...")
        backyard_reading = app.take_reading("Backyard")
        if backyard_reading:
            print("   ✓ Reading stored successfully")
            print(f"     PM2.5: {backyard_reading['reading']['concentrations']['atmospheric']['PM2.5']} μg/m³")
            print(f"     AQI: {backyard_reading['aqi']['aqi_value']} ({backyard_reading['aqi']['aqi_level']})")
        else:
            print("   ✗ Failed to take reading at Backyard")

        print("\n4. Querying recent readings...")

        # Get recent readings for Home Office
        home_readings = app.get_location_readings("Home Office", limit=5)
        print(f"   Recent readings for Home Office ({len(home_readings)} found):")
        for i, reading in enumerate(home_readings, 1):
            timestamp = reading['timestamp'][:19]  # Format timestamp
            pm25 = reading['pm2_5_atmospheric']
            aqi = reading.get('aqi_value', 'N/A')
            level = reading.get('aqi_level', 'N/A')
            print(f"     {i}. {timestamp} - PM2.5: {pm25} μg/m³, AQI: {aqi} ({level})")

        print("\n5. Dashboard summary...")
        try:
            dashboard = app.get_dashboard_data()
            print(f"   Total monitoring locations: {dashboard['total_locations']}")

            locations_data = dashboard.get('locations', [])
            if locations_data:
                for loc_data in locations_data:
                    loc = loc_data['location']
                    stats = loc_data['summary']
                    latest = loc_data['latest_reading']

                    print(f"\n   Location: {loc['name']}")
                    print(f"     Total readings: {stats.get('total_readings', 0)}")
                    print(f"     Average PM2.5: {stats.get('avg_pm25', 0):.1f} μg/m³")
                    if latest:
                        print(f"     Latest AQI: {latest.get('aqi_value', 'N/A')} ({latest.get('aqi_level', 'N/A')})")
            else:
                print("   No location data available")
        except Exception as e:
            print(f"   Error getting dashboard data: {e}")

        print("\n6. Data export example...")
        # Export recent data as JSON
        export_data = app.export_data("Home Office", format_type="json")
        print(f"   Exported {len(export_data.split('},'))} readings as JSON")
        print("   First 200 characters of export:")
        print(f"   {export_data[:200]}...")

        print("\n=== AQI App demonstration completed successfully! ===")

    except Exception as e:
        print(f"\nERROR: {e}")
        print("Make sure the PM25 sensor is connected and accessible")

    finally:
        # Clean up
        try:
            if 'app' in locals():
                app.close()
                print("\nDatabase connection closed.")
        except Exception:
            pass


def demonstrate_quick_reading():
    """Demonstrate the quick reading convenience function."""
    print("\n=== Quick Reading Example ===\n")

    try:
        print("Taking quick reading at Home Office...")
        result = quick_reading("Home Office", "aqi_demo.db")

        if result:
            print("✓ Quick reading successful!")
            print(f"  Reading ID: {result['reading_id']}")
            print(f"  PM2.5: {result['reading']['concentrations']['atmospheric']['PM2.5']} μg/m³")
            print(f"  AQI: {result['aqi']['aqi_value']} ({result['aqi']['aqi_level']})")
        else:
            print("✗ Quick reading failed")

    except Exception as e:
        print(f"ERROR in quick reading: {e}")


def demonstrate_location_management():
    """Demonstrate location management features."""
    print("\n=== Location Management Example ===\n")

    app = None
    try:
        app = AQIApp("aqi_demo.db")

        # List all locations
        locations = app.get_all_locations()
        print(f"Current monitoring locations ({len(locations)}):")
        for loc in locations:
            status = "Active" if loc['is_active'] else "Inactive"
            print(f"  - {loc['name']} ({status})")
            if loc['city']:
                print(f"    {loc['city']}, {loc['country']}")

        # Update a location
        print("\nUpdating location description...")
        if 'home_id' in locals() and home_id:
            success = app.db.update_location(home_id, description="Updated home office location")
            if success:
                print("✓ Location updated successfully")
            else:
                print("✗ Location update failed")
        else:
            print("   Home Office location not available for update")

        app.close()

    except Exception as e:
        print(f"ERROR in location management: {e}")


if __name__ == "__main__":
    main()

    # Uncomment to see additional examples
    # demonstrate_quick_reading()
    # demonstrate_location_management()