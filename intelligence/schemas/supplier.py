from __future__ import annotations

from pydantic import BaseModel


class Supplier(BaseModel):
    """Structured supplier profile."""

    supplier_id: str
    supplier_name: str
    region: str
    countries_served: list[str]
    product_categories: list[str]
    reliability_score: float