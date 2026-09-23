from __future__ import annotations

from typing import Any

import pandas as pd

from intelligence.models.risk_model import RiskModel


class RiskService:
    """Application service for shipment risk prediction."""

    def __init__(self, model: RiskModel | None = None) -> None:
        self.model = model or RiskModel()

    def assess_shipment(
        self,
        shipment_features: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Assess a shipment's historical late-delivery risk.

        Args:
            shipment_features: Model-ready shipment features.

        Returns:
            Risk assessment containing probability, threshold,
            and risk classification.
        """
        data = pd.DataFrame([shipment_features])

        prediction = self.model.predict(data)

        return {
            "risk_probability": prediction["risk_probability"],
            "threshold": prediction["threshold"],
            "is_at_risk": prediction["is_at_risk"],
        }