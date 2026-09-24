from __future__ import annotations

from pathlib import Path

import pandas as pd

from intelligence.schemas.shipment import Shipment


DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "DataCoSupplyChainDataset.csv"
)


class ShipmentRepository:
    """Repository for accessing historical shipment data."""

    def __init__(self, data_path: Path = DATA_PATH) -> None:
        self.data_path = data_path
        self._data: pd.DataFrame | None = None

    def _load_data(self) -> pd.DataFrame:
        """Load shipment data lazily from the CSV file."""
        if self._data is None:
            self._data = pd.read_csv(
                self.data_path,
                encoding="latin1",
            )

        return self._data

    def get_shipment(self, shipment_id: str) -> Shipment | None:
        """Return a shipment by its Order Id."""
        data = self._load_data()

        rows = data[data["Order Id"].astype(str) == shipment_id]

        if rows.empty:
            return None

        row = rows.iloc[0]

        product_categories = (
            rows["Category Name"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        shipping_date = pd.to_datetime(
            row["shipping date (DateOrders)"],
            errors="coerce",
        )

        return Shipment(
            shipment_id=str(row["Order Id"]),
            status=self._map_status(row["Delivery Status"]),
            destination_city=str(row["Order City"]),
            destination_country=str(row["Order Country"]),
            order_region=str(row["Order Region"]),
            shipping_mode=str(row["Shipping Mode"]),
            product_categories=product_categories,
            order_date=pd.to_datetime(
                row["order date (DateOrders)"]
            ).to_pydatetime(),
            scheduled_shipping_days=int(
                row["Days for shipment (scheduled)"]
            ),
            shipping_date=(
                shipping_date.to_pydatetime()
                if not pd.isna(shipping_date)
                else None
            ),
        )

    @staticmethod
    def _map_status(status: str) -> str:
        """Map DataCo delivery statuses to SentinelAI statuses."""
        status_mapping = {
            "Advance shipping": "advance_shipping",
            "Late delivery": "late_delivery",
            "Shipping on time": "shipping_on_time",
            "Shipping canceled": "shipping_cancelled",
        }

        try:
            return status_mapping[status]
        except KeyError as exc:
            raise ValueError(
                f"Unknown shipment status: {status}"
            ) from exc