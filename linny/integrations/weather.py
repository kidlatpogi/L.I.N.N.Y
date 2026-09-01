"""
Weather Client using Open-Meteo API with caching, accurate WMO translation,
cloud cover & rain metrics, and automatic City Geocoding.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

import requests

from ..core.logger import get_logger

logger = get_logger("weather")

# High-precision WMO Weather interpretation codes
WMO_CODES = {
    0: ("Clear Sky", "It is bright and clear outside. Great day to head out!"),
    1: ("Mainly Clear", "Skies are mostly clear and pleasant."),
    2: ("Partly Cloudy", "Partly cloudy with scattered cloud cover."),
    3: ("Overcast", "Overcast skies today."),
    45: ("Foggy", "Foggy conditions. Drive carefully as visibility is reduced."),
    48: ("Depositing Rime Fog", "Dense freezing fog."),
    51: ("Light Drizzle", "Light drizzle outside. You might want an umbrella."),
    53: ("Moderate Drizzle", "Drizzling outside. Keep dry!"),
    55: ("Dense Drizzle", "Heavy drizzle outside. Bring an umbrella."),
    61: ("Slight Rain", "Light rain falling. Don't forget your umbrella."),
    63: ("Moderate Rain", "Moderate rain outside. Stay dry!"),
    65: ("Heavy Rain", "Heavy rain pouring. Stay indoors if possible."),
    71: ("Slight Snow", "Light snowfall."),
    73: ("Moderate Snow", "Moderate snow falling."),
    75: ("Heavy Snow", "Heavy snowfall."),
    80: ("Rain Showers", "Passing rain showers today."),
    81: ("Moderate Rain Showers", "Moderate rain showers in the area."),
    82: ("Violent Rain Showers", "Torrential rain showers! Stay safe indoors."),
    95: ("Thunderstorms", "Thunderstorms detected in the area. Stay indoors away from windows."),
    96: ("Thunderstorm with Hail", "Thunderstorms with slight hail."),
    99: ("Severe Thunderstorm with Heavy Hail", "Severe thunderstorms with heavy hail. Take shelter!"),
}


class WeatherClient:
    """Accurate Open-Meteo weather client with geocoding and TTL caching."""

    def __init__(
        self,
        latitude: float = 14.2167,
        longitude: float = 120.9833,
        timezone: str = "Asia/Manila",
        city_name: str = "Silang, Cavite",
        cache_ttl_seconds: int = 600,
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.city_name = city_name
        self.cache_ttl = cache_ttl_seconds
        self._cached_data: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0.0

    def update_coordinates(self, lat: float, lon: float, tz: str, city: Optional[str] = None) -> None:
        self.latitude = lat
        self.longitude = lon
        self.timezone = tz
        if city:
            self.city_name = city
        self._cached_data = None

    def geocode_city(self, city_name: str) -> Optional[Tuple[float, float, str, str]]:
        """
        Geocode city name using Open-Meteo Geocoding API.
        Returns (latitude, longitude, timezone, formatted_name) or None.
        """
        try:
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(city_name)}&count=1&language=en&format=json"
            resp = requests.get(url, timeout=6)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if results:
                top = results[0]
                lat = top["latitude"]
                lon = top["longitude"]
                tz = top.get("timezone", self.timezone)
                name = f"{top.get('name')}, {top.get('country_code', '')}".strip(", ")
                logger.info(f"Geocoded '{city_name}' -> {name} ({lat}, {lon})")
                return lat, lon, tz, name
            return None
        except Exception as e:
            logger.warning(f"Geocoding error for '{city_name}': {e}")
            return None

    def fetch_weather(self) -> Dict[str, Any]:
        """
        Fetch rich, high-precision current weather metrics.
        Returns dictionary with temperature, feels_like, condition, humidity, cloud_cover, wind_speed, advice.
        """
        now = time.time()
        if self._cached_data and (now - self._cache_timestamp) < self.cache_ttl:
            return self._cached_data

        try:
            # Request current high-precision metrics
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={self.latitude}&longitude={self.longitude}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,weather_code,cloud_cover,wind_speed_10m"
                f"&timezone={self.timezone.replace('/', '%2F')}"
            )
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            data = resp.json()

            current = data.get("current", {})
            temp = current.get("temperature_2m", 25.0)
            feels_like = current.get("apparent_temperature", temp)
            humidity = current.get("relative_humidity_2m", 70)
            code = current.get("weather_code", 0)
            cloud_cover = current.get("cloud_cover", 0)
            is_day = current.get("is_day", 1)
            rain = current.get("rain", 0.0)
            wind_speed = current.get("wind_speed_10m", 0.0)

            # Determine human-friendly condition description
            cond_title, advice = WMO_CODES.get(code, ("Clear", "Have a great day."))

            # Fine-tune condition based on cloud cover & day/night
            if code in (0, 1, 2, 3):
                if rain > 0.1:
                    cond_title = "Light Rain Showers"
                    advice = "Passing rain in the area. Bring an umbrella."
                elif cloud_cover < 20:
                    cond_title = "Sunny & Clear" if is_day == 1 else "Clear & Starry Night"
                    advice = "Clear conditions outside." if is_day == 0 else "Sunny skies. Enjoy the day!"
                elif cloud_cover < 65:
                    cond_title = "Partly Cloudy"
                    advice = "Scattered clouds with pleasant conditions."
                else:
                    cond_title = "Overcast"
                    advice = "Cloudy skies. It might rain later."

            result = {
                "temperature": round(temp, 1),
                "feels_like": round(feels_like, 1),
                "humidity": humidity,
                "condition": cond_title,
                "cloud_cover": cloud_cover,
                "wind_speed": wind_speed,
                "is_day": bool(is_day),
                "advice": advice,
                "city": self.city_name,
            }

            self._cached_data = result
            self._cache_timestamp = now
            logger.info(f"Weather updated for {self.city_name}: {result['temperature']}°C, {result['condition']}")
            return result

        except requests.Timeout:
            logger.warning("Weather API request timed out")
            return {
                "temperature": 26.0,
                "feels_like": 26.0,
                "humidity": 65,
                "condition": "Partly Cloudy",
                "cloud_cover": 40,
                "wind_speed": 10.0,
                "is_day": True,
                "advice": "Weather service is temporarily slow.",
                "city": self.city_name,
            }
        except Exception as e:
            logger.warning(f"Weather API error: {e}")
            return {
                "temperature": 26.0,
                "feels_like": 26.0,
                "humidity": 65,
                "condition": "Fair",
                "cloud_cover": 30,
                "wind_speed": 8.0,
                "is_day": True,
                "advice": "Could not connect to weather service.",
                "city": self.city_name,
            }

    def get_voice_summary(self) -> str:
        """Generate conversational text summary for text-to-speech greeting."""
        data = self.fetch_weather()
        temp = data.get("temperature", 25)
        feels_like = data.get("feels_like", temp)
        condition = data.get("condition", "Partly Cloudy")
        advice = data.get("advice", "Have a wonderful day.")

        feels_msg = f", feeling like {round(feels_like)} degrees" if abs(feels_like - temp) >= 2 else ""
        return f"In {self.city_name}, it is currently {round(temp)} degrees Celsius{feels_msg}, with {condition.lower()}. {advice}"
