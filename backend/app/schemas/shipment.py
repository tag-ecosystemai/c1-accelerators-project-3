from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class Shipment(BaseModel):
    id: str                      # from "Order Id"
    order_date: datetime         # from "order date (DateOrders)"
    scheduled_days: int          # from "Days for shipment (scheduled)"
    scheduled_arrival: datetime  # computed: order_date + scheduled_days
    shipping_mode: str           # from "Shipping Mode"
    category: str                # from "Category Name"
    department: str              # from "Department Name" (our supplier stand-in)
    market: str                  # from "Market"
    region: str                  # from "Order Region"
    country: str                 # from "Order Country"
    city: str                    # from "Order City"
    lat: Optional[float] = None
    lon: Optional[float] = None    # from "Longitude"
    quantity: int                # from "Order Item Quantity"
    order_total: float           # from "Order Item Total"