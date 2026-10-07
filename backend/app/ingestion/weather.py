from typing import Optional

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(lat: float, lon: float) -> Optional[dict]:
    """Return a small weather summary for the next 72 hours, or None if unavailable."""
    try:
        response = httpx.get(
            OPEN_METEO_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "precipitation,wind_speed_10m",
                "forecast_days": 3,
            },
            timeout=5,
        )
        response.raise_for_status()
        hourly = response.json()["hourly"]
        return {
            "max_precip_mm_h": max(hourly["precipitation"]),
            "max_wind_kmh": max(hourly["wind_speed_10m"]),
            "horizon_hours": len(hourly["precipitation"]),
        }
    except (httpx.HTTPError, KeyError, ValueError):
        return None