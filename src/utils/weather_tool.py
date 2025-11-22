"""
Weather Tool for ARK Agent AGI
Provides weather information using OpenWeatherMap API
"""

import os
from typing import Any, Dict, Optional

import requests

from utils.logging_utils import log_event


class WeatherTool:
    """
    Weather information via OpenWeatherMap API
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

        log_event("WeatherTool", {"event": "initialized", "has_api_key": bool(self.api_key)})

    def get_weather(self, city: str, units: str = "metric") -> Dict[str, Any]:
        """
        Get current weather for a city

        Args:
            city: City name
            units: metric (Celsius) or imperial (Fahrenheit)

        Returns:
            Weather data dictionary
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Weather API key not configured. Set OPENWEATHER_API_KEY environment variable.",
                "city": city,
            }

        try:
            params = {"q": city, "appid": self.api_key, "units": units}
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "city": data.get("name"),
                "country": data.get("sys", {}).get("country"),
                "temperature": data.get("main", {}).get("temp"),
                "feels_like": data.get("main", {}).get("feels_like"),
                "humidity": data.get("main", {}).get("humidity"),
                "description": data.get("weather", [{}])[0].get("description"),
                "wind_speed": data.get("wind", {}).get("speed"),
                "units": units,
            }
        except Exception as e:
            log_event("WeatherTool", {"event": "error", "city": city, "error": str(e)})
            return {"success": False, "error": str(e), "city": city}


weather_tool = WeatherTool()
