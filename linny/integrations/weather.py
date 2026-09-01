"""
Weather Client using Open-Meteo API with caching and contextual recommendations.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

import requests

from ..core.logger import get_logger

logger = get_logger("weather")

# WMO Weather interpretation codes
WMO_CODES = {
    0: ("clear sky", "It is bright and sunny outside. Wear sunscreen if heading out."),
    1: ("mainly clear", "Weather is nice and pleasant today."),
    2: ("partly cloudy", "Partly cloudy conditions."),
    3: ("overcast", "It's overcast today. It might rain later, so consider bringing an umbrella."),
    45: ("foggy", "Foggy morning. Drive carefully as visibility is reduced."),
    48: ("depositing rime fog", "Foggy conditions."),
    51: ("light drizzle", "Light drizzle outside. Bring an umbrella."),
    53: ("moderate drizzle", "Drizzling outside. Keep dry."),
    55: ("dense drizzle", "Heavy drizzle outside. Bring an umbrella."),
    61: ("slight rain", "Light rain expected. Don't forget your umbrella."),
    63: ("moderate rain", "Moderate rain outside. Stay dry!"),
    65: ("heavy rain", "Heavy rain pouring. Stay indoors if possible."),
    80: ("rain showers", "Scattered rain showers today."),
    81: ("moderate rain showers", "Passing rain showers today."),
    82: ("violent rain showers", "Torrential rain showers. Stay safe indoors."),
    95: ("thunderstorm", "Thunderstorms detected. Stay indoors away from windows."),
    96: ("thunderstorm with slight hail", "Severe thunderstorms with hail."),
    99: ("thunderstorm with heavy hail", "Severe thunderstorms with heavy hail."),
}


class WeatherClient:
    """Open-Meteo weather client with TTL caching."""

    def __init__(
        self,
        latitude: float = 14.2167,
        longitude: float = 120.9833,
        timezone: str = "Asia/Manila",
        cache_ttl_seconds: int = 900,
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.cache_ttl = cache_ttl_seconds
        self._cached_data: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0.0

    def update_coordinates(self, lat: float, lon: float, tz: str) -> None:
        self.latitude = lat
        self.longitude = lon
        self.timezone = tz
        self._cached_data = None

    def fetch_weather(self) -> Tuple[Optional[float], str, str]:
        """
        Fetch current weather metrics.
        Returns (temperature_celsius, condition_text, advice_text).
        """
        now = time.time()
        if self._cached_data and (now - self._cache_timestamp) < self.cache_ttl:
            cw = self._cached_data.get("current_weather", {})
            temp = cw.get("temperature")
            code = cw.get("weathercode", 0)
            condition, advice = WMO_CODES.get(code, ("cloudy", "Have a great day."))
            return temp, condition, advice

        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={self.latitude}&longitude={self.longitude}"
                f"&current_weather=true&timezone={self.timezone.replace('/', '%2F')}"
            )
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            data = resp.json()

            self._cached_data = data
            self._cache_timestamp = now

            cw = data.get("current_weather", {})
            temp = cw.get("temperature")
            code = cw.get("weathercode", 0)
            condition, advice = WMO_CODES.get(code, ("cloudy", "Have a great day."))
            logger.info(f"Weather updated: {temp}°C, {condition}")
            return temp, condition, advice

        except requests.Timeout:
            logger.warning("Weather API request timed out")
            return None, "unavailable", "Weather service is temporarily slow."
        except Exception as e:
            logger.warning(f"Weather API error: {e}")
            return None, "unavailable", "Could not reach weather service."

    def get_voice_summary(self) -> str:
        """Generate conversational text summary for text-to-speech greeting."""
        temp, condition, advice = self.fetch_weather()
        if temp is None:
            return "Weather information is currently unavailable."
        return f"It is currently {round(temp)} degrees Celsius with {condition}. {advice}"
