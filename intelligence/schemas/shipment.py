from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


ShipmentStatus = Literal[
    "advance_shipping",
    "late_delivery",
    "shipping_on_time",
    "shipping_cancelled",
]


class Shipment(BaseModel):
    """Historical shipment representation derived from DataCo."""

    shipment_id: str
    status: ShipmentStatus

    destination_city: str
    destination_country: str
    order_region: str

    shipping_mode: str
    product_categories: list[str]

    order_date: datetime
    scheduled_shipping_days: int
    shipping_date: datetime | None = None