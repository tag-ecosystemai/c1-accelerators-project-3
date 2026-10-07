from __future__ import annotations

from pathlib import Path

import pandas as pd

from intelligence.schemas.risk_features import RiskFeatures


DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "shipment_features.csv"
)


class RiskFeatureRepository:
    """Repository for accessing model-ready shipment features."""

    def __init__(self, data_path: Path = DATA_PATH) -> None:
        self.data_path = data_path
        self._data: pd.DataFrame | None = None

    def _load_data(self) -> pd.DataFrame:
        """Load processed shipment features lazily."""

        if self._data is None:
            self._data = pd.read_csv(
                self.data_path,
            )

        return self._data

    def get_features(
        self,
        shipment_id: str,
    ) -> RiskFeatures | None:
        """Return model-ready features for an order."""

        data = self._load_data()

        rows = data[
            data["shipment_id"].astype(str) == shipment_id
        ]

        if rows.empty:
            return None

        row = rows.iloc[0]

        return RiskFeatures(
            scheduled_days=int(
                row["scheduled_shipping_days"]
            ),
            market=str(row["market"]),
            order_region=str(row["order_region"]),
            order_country=str(row["destination_country"]),
            item_count=int(row["item_count"]),
            total_quantity=int(row["total_quantity"]),
            avg_product_price=float(
                row["avg_product_price"]
            ),
            total_sales=float(
                row["total_sales"]
            ),
            avg_discount_rate=float(
                row["avg_discount_rate"]
            ),
            customer_segment=str(
                row["customer_segment"]
            ),
        )