from __future__ import annotations

from pydantic import BaseModel


class RiskFeatures(BaseModel):
    """Model-ready features for SentinelAI risk prediction."""

    scheduled_days: int
    market: str
    order_region: str
    order_country: str

    item_count: int
    total_quantity: int

    avg_product_price: float
    total_sales: float
    avg_discount_rate: float

    customer_segment: str