from __future__ import annotations

from pathlib import Path

import pandas as pd

from intelligence.schemas.risk_features import RiskFeatures


DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "DataCoSupplyChainDataset.csv"
)


class RiskFeatureRepository:
    """Repository for reconstructing model-ready shipment features."""

    def __init__(self, data_path: Path = DATA_PATH) -> None:
        self.data_path = data_path
        self._data: pd.DataFrame | None = None

    def _load_data(self) -> pd.DataFrame:
        """Load the raw shipment dataset lazily."""

        if self._data is None:
            self._data = pd.read_csv(
                self.data_path,
                encoding="latin1",
            )

        return self._data

    def get_features(
        self,
        shipment_id: str,
    ) -> RiskFeatures | None:
        """Build model-ready features for an order."""

        data = self._load_data()

        rows = data[
            data["Order Id"].astype(str) == shipment_id
        ]

        if rows.empty:
            return None

        first_row = rows.iloc[0]

        return RiskFeatures(
            scheduled_days=int(
                first_row["Days for shipment (scheduled)"]
            ),
            market=str(first_row["Market"]),
            order_region=str(first_row["Order Region"]),
            order_country=str(first_row["Order Country"]),
            item_count=len(rows),
            total_quantity=int(
                rows["Order Item Quantity"].sum()
            ),
            avg_product_price=float(
                rows["Product Price"].mean()
            ),
            total_sales=float(
                rows["Sales"].sum()
            ),
            avg_discount_rate=float(
                rows["Order Item Discount Rate"].mean()
            ),
            customer_segment=str(
                first_row["Customer Segment"]
            ),
        )