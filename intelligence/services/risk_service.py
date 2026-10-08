from __future__ import annotations

from typing import Any

import pandas as pd

from intelligence.models.risk_model import RiskModel


class RiskService:
    """Application service for honest shipment risk prediction."""

    REQUIRED_FEATURES = {
        "scheduled_days",
        "market",
        "order_region",
        "order_country",
        "item_count",
        "total_quantity",
        "avg_product_price",
        "total_sales",
        "avg_discount_rate",
        "customer_segment",
    }

    def __init__(self, model: RiskModel | None = None) -> None:
        self.model = model or RiskModel()

    @classmethod
    def has_model_ready_features(
        cls,
        shipment_features: dict[str, Any],
    ) -> bool:
        """
        Return True only when every feature required by the trained
        CatBoost model is genuinely available.
        """
        return cls.REQUIRED_FEATURES.issubset(shipment_features.keys())

    @classmethod
    def missing_model_features(
        cls,
        shipment_features: dict[str, Any],
    ) -> list[str]:
        """Return required CatBoost features that were not supplied."""
        return sorted(
            cls.REQUIRED_FEATURES.difference(shipment_features.keys())
        )

    def assess_shipment(
        self,
        shipment_features: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Run the CatBoost model for a shipment with genuine model-ready data.

        The service never invents or derives missing DataCo features.
        """
        missing_features = self.missing_model_features(shipment_features)

        if missing_features:
            return {
                "available": False,
                "reason": (
                    "CatBoost prediction unavailable because required "
                    "model features were not supplied."
                ),
                "missing_features": missing_features,
                "risk_probability": None,
                "threshold": None,
                "is_at_risk": None,
            }

        data = pd.DataFrame([shipment_features])

        prediction = self.model.predict(data)

        return {
            "available": True,
            "reason": None,
            "missing_features": [],
            "risk_probability": prediction["risk_probability"],
            "threshold": prediction["threshold"],
            "is_at_risk": prediction["is_at_risk"],
        }