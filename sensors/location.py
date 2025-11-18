"""
Location Detection Module

This module provides location detection functionality for the PM25 sensor API,
allowing users to get geographic context for their air quality readings.

Features:
- IP-based geolocation (automatic)
- Manual location setting
- GPS coordinate validation
- Location caching
- Integration with air quality data
"""

import time
import json
import socket
import requests
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from .exceptions import ConfigurationError, InvalidDataError


class LocationDetector:
    """
    Location detection class for PM25 sensor API.
    
    Provides automatic IP-based geolocation and manual location setting
    with validation and caching capabilities.
    """
    
    def __init__(self, cache_file: Optional[str] = None, timeout: int = 10):
        """
        Initialize location detector.
        
        Args:
            cache_file: Optional file to cache location data
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.cache_file = Path(cache_file) if cache_file else None
        self._cached_location = None
        self._cache_timestamp = None
        
        # Load cached location if available
        if self.cache_file and self.cache_file.exists():
            self._load_cached_location()
    
    def detect_location_by_ip(self) -> Dict[str, Any]:
        """
        Detect location using IP-based geolocation.
        
        Returns:
            Dictionary with location information
            
        Raises:
            LocationDetectionError: If location detection fails
        """
        try:
            # Try multiple geolocation services for reliability
            services = [
                self._get_ipinfo,
                self._get_ip_api,
                self._get_geojs
            ]
            
            for service in services:
                try:
                    location = service()
                    if location and self._validate_location_data(location):
                        self._cache_location(location)
                        return location
                except Exception as e:
                    print(f"Location service failed: {e}")
                    continue
            
            raise LocationDetectionError("All location services failed")
            
        except Exception as e:
            raise LocationDetectionError(f"Failed to detect location: {e}")
    
    def set_manual_location(self, latitude: float, longitude: float, 
                         city: Optional[str] = None, country: Optional[str] = None) -> Dict[str, Any]:
        """
        Set location manually.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            city: Optional city name
            country: Optional country name
            
        Returns:
            Dictionary with location information
            
        Raises:
            InvalidDataError: If coordinates are invalid
        """
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            raise InvalidDataError("Latitude", latitude, "must be between -90 and 90")
        
        if not (-180 <= longitude <= 180):
            raise InvalidDataError("Longitude", longitude, "must be between -180 and 180")
        
        location = {
            "latitude": latitude,
            "longitude": longitude,
            "city": city,
            "country": country,
            "source": "manual",
            "timestamp": time.time()
        }
        
        self._cache_location(location)
        return location
    
    def get_location(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get current location (cached or detected).
        
        Args:
            force_refresh: Whether to force location detection
            
        Returns:
            Dictionary with location information
        """
        # Check if we have valid cached location
        if not force_refresh and self._cached_location:
            # Check if cache is recent (1 hour)
            if time.time() - self._cache_timestamp < 3600:
                return self._cached_location
        
        # Try to detect location
        try:
            location = self.detect_location_by_ip()
            return location
        except LocationDetectionError:
            # Return cached location if available, even if old
            if self._cached_location:
                return self._cached_location
            
            # Return default location if nothing available
            return self._get_default_location()
    
    def get_coordinates(self) -> Tuple[float, float]:
        """
        Get latitude and longitude coordinates.
        
        Returns:
            Tuple of (latitude, longitude)
        """
        location = self.get_location()
        return (location["latitude"], location["longitude"])
    
    def get_location_string(self) -> str:
        """
        Get formatted location string.
        
        Returns:
            Formatted location string
        """
        location = self.get_location()
        
        if location.get("city") and location.get("country"):
            return f"{location['city']}, {location['country']}"
        elif location.get("city"):
            return location["city"]
        elif location.get("country"):
            return location["country"]
        else:
            return f"{location['latitude']:.4f}, {location['longitude']:.4f}"
    
    def calculate_distance(self, latitude: float, longitude: float) -> float:
        """
        Calculate distance from given coordinates.
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            
        Returns:
            Distance in kilometers
        """
        lat1, lon1 = self.get_coordinates()
        
        # Haversine formula
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, latitude, longitude])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return r * c
    
    def _get_ipinfo(self) -> Optional[Dict[str, Any]]:
        """Get location from ipinfo.io service."""
        try:
            response = requests.get("https://ipinfo.io/json", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                if "loc" in data:
                    lat, lon = map(float, data["loc"].split(","))
                    return {
                        "latitude": lat,
                        "longitude": lon,
                        "city": data.get("city"),
                        "region": data.get("region"),
                        "country": data.get("country"),
                        "postal": data.get("postal"),
                        "ip": data.get("ip"),
                        "source": "ipinfo.io",
                        "timestamp": time.time()
                    }
        except Exception:
            pass
        return None
    
    def _get_ip_api(self) -> Optional[Dict[str, Any]]:
        """Get location from ip-api.com service."""
        try:
            response = requests.get("http://ip-api.com/json/", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "latitude": data["lat"],
                        "longitude": data["lon"],
                        "city": data.get("city"),
                        "region": data.get("region"),
                        "country": data.get("country"),
                        "postal": data.get("zip"),
                        "ip": data.get("query"),
                        "source": "ip-api.com",
                        "timestamp": time.time()
                    }
        except Exception:
            pass
        return None
    
    def _get_geojs(self) -> Optional[Dict[str, Any]]:
        """Get location from geojs.io service."""
        try:
            response = requests.get("https://get.geojs.io/v1/ip/geo.json", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return {
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country"),
                    "ip": data.get("ip"),
                    "source": "geojs.io",
                    "timestamp": time.time()
                }
        except Exception:
            pass
        return None
    
    def _validate_location_data(self, location: Dict[str, Any]) -> bool:
        """Validate location data structure."""
        required_fields = ["latitude", "longitude"]
        return all(field in location for field in required_fields)
    
    def _cache_location(self, location: Dict[str, Any]) -> None:
        """Cache location data."""
        self._cached_location = location
        self._cache_timestamp = time.time()
        
        # Save to file if cache file specified
        if self.cache_file:
            try:
                with open(self.cache_file, 'w') as f:
                    json.dump(location, f, indent=2)
            except Exception:
                pass
    
    def _load_cached_location(self) -> None:
        """Load cached location from file."""
        try:
            with open(self.cache_file, 'r') as f:
                location = json.load(f)
                if self._validate_location_data(location):
                    self._cached_location = location
                    self._cache_timestamp = location.get("timestamp", 0)
        except Exception:
            pass
    
    def _get_default_location(self) -> Dict[str, Any]:
        """Get default location when detection fails."""
        return {
            "latitude": 40.7128,  # New York
            "longitude": -74.0060,
            "city": "New York",
            "country": "United States",
            "source": "default",
            "timestamp": time.time()
        }


class LocationDetectionError(Exception):
    """Exception raised when location detection fails."""
    pass


def detect_location() -> Dict[str, Any]:
    """
    Convenience function to detect current location.
    
    Returns:
        Dictionary with location information
    """
    detector = LocationDetector()
    return detector.get_location()


def set_location(latitude: float, longitude: float, 
               city: Optional[str] = None, country: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to set manual location.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        city: Optional city name
        country: Optional country name
        
    Returns:
        Dictionary with location information
    """
    detector = LocationDetector()
    return detector.set_manual_location(latitude, longitude, city, country)


def get_location_with_air_quality(sensor, include_location: bool = True) -> Dict[str, Any]:
    """
    Get air quality data with location information.
    
    Args:
        sensor: PM25Sensor instance
        include_location: Whether to include location data
        
    Returns:
        Dictionary with air quality and location data
    """
    # Get air quality data
    aqi_v2 = sensor.get_aqi_v2(include_pm10_comparison=True)
    summary_v2 = sensor.get_air_quality_summary_v2(include_pm10_comparison=True)
    
    result = {
        "air_quality": {
            "pm25_atmospheric": aqi_v2["pm25_atmospheric"],
            "pm10_atmospheric": aqi_v2["pm10_atmospheric"],
            "aqi_value": aqi_v2["aqi_value"],
            "aqi_level": aqi_v2["aqi_level"],
            "aqi_color": aqi_v2["aqi_color"],
            "aqi_source": aqi_v2["aqi_source"],
            "health_message": aqi_v2["health_message"],
            "timestamp": aqi_v2["timestamp"]
        }
    }
    
    if include_location:
        try:
            detector = LocationDetector()
            location = detector.get_location()
            result["location"] = location
        except Exception as e:
            result["location"] = {"error": str(e)}
    
    return result