from __future__ import annotations

from intelligence.tools.route_tools import RouteTools
from intelligence.tools.shipment_tools import ShipmentTools
from intelligence.tools.weather_tools import WeatherTools
from intelligence.tools.supplier_tools import SupplierTools


class InvestigationService:
    """Orchestrates deterministic shipment investigation tools."""

    def __init__(
        self,
        shipment_tools: ShipmentTools | None = None,
        route_tools: RouteTools | None = None,
        weather_tools: WeatherTools | None = None,
        supplier_tools: SupplierTools | None = None,
    ) -> None:
        self.shipment_tools = shipment_tools or ShipmentTools()
        self.route_tools = route_tools or RouteTools()
        self.weather_tools = weather_tools or WeatherTools()
        self.supplier_tools = supplier_tools or SupplierTools()

    def investigate_shipment(
        self,
        shipment_id: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> dict:
        """Collect core operational evidence for a shipment."""
        shipment = self.shipment_tools.get_shipment_status(shipment_id)

        if shipment is None:
            raise ValueError(
                f"Shipment not found: {shipment_id}"
            )

        route_context = self.route_tools.get_route_context(
            shipment_id
        )

        route_options = self.route_tools.find_alternative_route(
            shipment_id
        )
        
        product_category = (
            shipment.product_categories[0]
           if shipment.product_categories
            else None
        )

        supplier_options = []

        if product_category:
            supplier_options = self.supplier_tools.find_alternative_suppliers(
                country=shipment.destination_country,
                product_category=product_category,
            )

        weather = None

        if latitude is not None and longitude is not None:
            weather = self.weather_tools.get_weather(
                latitude,
                longitude,
            )

        return {
            "shipment": shipment,
            "route_context": route_context,
            "route_options": route_options,
            "supplier_options": supplier_options,
            "weather": weather, 
        }
        
