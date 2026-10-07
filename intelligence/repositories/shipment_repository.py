from __future__ import annotations

from pathlib import Path

import pandas as pd

from intelligence.schemas.shipment import Shipment


DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "shipment_features.csv"
)


class ShipmentRepository:
    """Repository for accessing processed shipment data."""

    def __init__(self, data_path: Path = DATA_PATH) -> None:
        self.data_path = data_path
        self._data: pd.DataFrame | None = None

    def _load_data(self) -> pd.DataFrame:
        """Load processed shipment data lazily."""
        if self._data is None:
            self._data = pd.read_csv(
                self.data_path,
            )

        return self._data

    def get_shipment(self, shipment_id: str) -> Shipment | None:
        """Return a shipment by its Order Id."""

        data = self._load_data()

        rows = data[
            data["shipment_id"].astype(str) == shipment_id
        ]

        if rows.empty:
            return None

        row = rows.iloc[0]

        product_categories = []

        if pd.notna(row["product_categories"]):
            product_categories = (
                __import__("json").loads(
                    row["product_categories"]
                )
            )

        order_date = pd.to_datetime(
            row["order_date"],
            errors="coerce",
        )

        shipping_date = pd.to_datetime(
            row["shipping_date"],
            errors="coerce",
        )

        return Shipment(
            shipment_id=str(row["shipment_id"]),
            status=self._map_status(row["status"]),
            destination_city=str(row["destination_city"]),
            destination_country=str(row["destination_country"]),
            order_region=str(row["order_region"]),
            shipping_mode=str(row["shipping_mode"]),
            product_categories=product_categories,
            order_date=order_date.to_pydatetime(),
            scheduled_shipping_days=int(
                row["scheduled_shipping_days"]
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