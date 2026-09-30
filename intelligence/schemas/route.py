from __future__ import annotations

from pydantic import BaseModel


class RouteContext(BaseModel):
    """Geographic context for a shipment route."""

    destination_city: str
    destination_country: str
    order_region: str
    shipping_mode: str


class RouteAlternative(BaseModel):
    """Structured alternative route candidate."""

    route_id: str
    route_name: str
    region: str
    destination_countries: list[str]
    shipping_modes: list[str]
    estimated_transit_days: int
    demo_reliability_score: float