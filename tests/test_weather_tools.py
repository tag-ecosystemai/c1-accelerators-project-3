import httpx
import pytest

from intelligence.tools.weather_tools import WeatherTools


def test_get_weather():
    tools = WeatherTools()

    weather = tools.get_weather(
        latitude=-6.2383,
        longitude=106.9756,
    )

    assert weather.latitude != 0
    assert weather.longitude != 0
    assert weather.observed_at is not None
    assert isinstance(weather.temperature_c, float)
    assert isinstance(weather.precipitation_mm, float)
    assert isinstance(weather.wind_speed_kmh, float)
    assert isinstance(weather.weather_code, int)


def test_get_weather_api_failure(monkeypatch):
    def mock_get(*args, **kwargs):
        raise httpx.ConnectError("Connection failed")

    monkeypatch.setattr(httpx, "get", mock_get)

    tools = WeatherTools()

    with pytest.raises(RuntimeError, match="Weather service request failed"):
        tools.get_weather(
            latitude=-6.2383,
            longitude=106.9756,
        )