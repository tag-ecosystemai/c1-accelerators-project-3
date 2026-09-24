from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WeatherObservation(BaseModel):
    """Current weather conditions for a location."""

    latitude: float
    longitude: float
    observed_at: datetime

    temperature_c: float
    precipitation_mm: float
    wind_speed_kmh: float
    weather_code: int