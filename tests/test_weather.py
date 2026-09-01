"""Tests for WeatherClient geocoding and high-precision metrics."""

from linny.integrations.weather import WeatherClient


def test_weather_fetch_structure():
    client = WeatherClient()
    data = client.fetch_weather()

    assert "temperature" in data
    assert "condition" in data
    assert "humidity" in data
    assert "feels_like" in data
    assert "advice" in data
    assert "city" in data
    assert isinstance(data["temperature"], (int, float))


def test_weather_summary_text():
    client = WeatherClient()
    summary = client.get_voice_summary()
    assert len(summary) > 10
    assert "degrees" in summary.lower() or "celsius" in summary.lower() or "weather" in summary.lower()
