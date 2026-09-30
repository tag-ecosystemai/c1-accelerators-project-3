from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from catboost import CatBoostClassifier


MODEL_DIR = Path(__file__).resolve().parent
MODEL_PATH = MODEL_DIR / "sentinelai_catboost.cbm"
METADATA_PATH = MODEL_DIR / "model_metadata.json"


class RiskModel:
    """Production inference wrapper for the SentinelAI risk model."""

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        metadata_path: Path = METADATA_PATH,
    ) -> None:
        self.model_path = model_path
        self.metadata_path = metadata_path

        self._validate_artifacts()

        self.metadata = self._load_metadata()
        self.model = self._load_model()

        self.features = self.metadata["features"]
        self.threshold = float(self.metadata["threshold"])

    def _validate_artifacts(self) -> None:
        """Ensure required model artifacts exist."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}"
            )

        if not self.metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata file not found: {self.metadata_path}"
            )

    def _load_metadata(self) -> dict[str, Any]:
        """Load model metadata from JSON."""
        with self.metadata_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _load_model(self) -> CatBoostClassifier:
        """Load the trained CatBoost model."""
        model = CatBoostClassifier()
        model.load_model(str(self.model_path))
        return model

    def predict(self, data: pd.DataFrame) -> dict[str, Any]:
        """
        Generate a late-delivery risk prediction.

        Returns:
            A dictionary containing probability, threshold, and risk flag.
        """
        missing_features = [
            feature for feature in self.features
            if feature not in data.columns
        ]

        if missing_features:
            raise ValueError(
                f"Missing required features: {missing_features}"
            )

        model_input = data[self.features].copy()

        probability = float(
            self.model.predict_proba(model_input)[0][1]
        )

        return {
            "risk_probability": probability,
            "threshold": self.threshold,
            "is_at_risk": probability >= self.threshold,
        }