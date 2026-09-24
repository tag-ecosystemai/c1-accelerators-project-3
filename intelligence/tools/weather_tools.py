from __future__ import annotations

from datetime import datetime

import httpx

from intelligence.schemas.weather import WeatherObservation


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherTools:
    """Tools for retrieving weather conditions."""

    def get_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> WeatherObservation:
        """Retrieve current weather conditions for a location."""

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "precipitation,"
                "wind_speed_10m,"
                "weather_code"
            ),
            "timezone": "UTC",
        }

        try:
            response = httpx.get(
                OPEN_METEO_URL,
                params=params,
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Weather service request failed: {exc}"
            ) from exc

        data = response.json()
        current = data["current"]

        return WeatherObservation(
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            observed_at=datetime.fromisoformat(
                current["time"]
            ),
            temperature_c=float(current["temperature_2m"]),
            precipitation_mm=float(current["precipitation"]),
            wind_speed_kmh=float(current["wind_speed_10m"]),
            weather_code=int(current["weather_code"]),
        )