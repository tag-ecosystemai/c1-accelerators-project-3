from intelligence.services.investigation_service import InvestigationService
from intelligence.schemas.weather import WeatherObservation

class FakeWeatherTools:
    """Test double for the weather service."""

    def get_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> WeatherObservation:
        return WeatherObservation(
            latitude=latitude,
            longitude=longitude,
            observed_at="2026-09-25T08:00:00",
            temperature_c=28.5,
            precipitation_mm=12.4,
            wind_speed_kmh=31.2,
            weather_code=61,
        )

def test_investigate_shipment():
    service = InvestigationService()

    result = service.investigate_shipment("77202")

    assert result["shipment"] is not None
    assert result["shipment"].shipment_id == "77202"

    assert result["route_context"] is not None
    assert result["route_context"].destination_country == "Indonesia"

    assert len(result["route_options"]) == 1
    assert result["route_options"][0].route_id == "ROUTE-002"


def test_investigate_missing_shipment():
    service = InvestigationService()

    try:
        service.investigate_shipment("does-not-exist")
    except ValueError as exc:
        assert "Shipment not found" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
    
def test_investigate_shipment_includes_weather():
    service = InvestigationService(
        weather_tools=FakeWeatherTools()
    )

    result = service.investigate_shipment(
        "77202",
        latitude=-6.2383,
        longitude=106.9756,
    )

    weather = result["weather"]

    assert weather is not None
    assert weather.temperature_c == 28.5
    assert weather.precipitation_mm == 12.4
    assert weather.wind_speed_kmh == 31.2
    
def test_investigate_shipment_includes_supplier_options():
    service = InvestigationService()

    result = service.investigate_shipment("77202")

    suppliers = result["supplier_options"]

    assert len(suppliers) == 0