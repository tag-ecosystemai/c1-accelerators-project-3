from functools import lru_cache
from pathlib import Path
from typing import Optional
import pandas as pd

from app.schemas.shipment import Shipment

# backend/app/ingestion/dataco.py -> parents[3] is the project root
DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "raw" / "DataCoSupplyChainDataset.csv"


def load_orders() -> pd.DataFrame:
    """Read the raw CSV and collapse item rows into one row per order."""
    df = pd.read_csv(DATA_PATH, encoding="latin-1")
    df["order_date"] = pd.to_datetime(df["order date (DateOrders)"], format="%m/%d/%Y %H:%M")

    # Highest-value item first, so "first" below means "the biggest item"
    df = df.sort_values("Order Item Total", ascending=False)

    orders = df.groupby("Order Id").agg(
        order_date=("order_date", "first"),
        scheduled_days=("Days for shipment (scheduled)", "first"),
        shipping_mode=("Shipping Mode", "first"),
        category=("Category Name", "first"),
        department=("Department Name", "first"),
        market=("Market", "first"),
        region=("Order Region", "first"),
        country=("Order Country", "first"),
        city=("Order City", "first"),
        lat=("Latitude", "first"),
        lon=("Longitude", "first"),
        quantity=("Order Item Quantity", "sum"),
        order_total=("Order Item Total", "sum"),
        late=("Late_delivery_risk", "first"),   # the label: for training only
    ).reset_index()

    orders["scheduled_arrival"] = orders["order_date"] + pd.to_timedelta(
        orders["scheduled_days"], unit="D"
    )
    return orders


@lru_cache(maxsize=1)
def _orders() -> pd.DataFrame:
    return load_orders()   # loaded once, then reused


def _to_shipment(row) -> Shipment:
    return Shipment(
        id=str(row["Order Id"]),
        order_date=row["order_date"].to_pydatetime(),
        scheduled_days=int(row["scheduled_days"]),
        scheduled_arrival=row["scheduled_arrival"].to_pydatetime(),
        shipping_mode=row["shipping_mode"],
        category=row["category"],
        department=row["department"],
        market=row["market"],
        region=row["region"],
        country=row["country"],
        city=row["city"],
        lat=float(row["lat"]),
        lon=float(row["lon"]),
        quantity=int(row["quantity"]),
        order_total=float(row["order_total"]),
    )


def get_shipment(order_id: str) -> Optional[Shipment]:
    df = _orders()
    match = df[df["Order Id"] == int(order_id)]
    if match.empty:
        return None
    return _to_shipment(match.iloc[0])


def all_shipment_ids() -> list[str]:
    return [str(i) for i in _orders()["Order Id"]]