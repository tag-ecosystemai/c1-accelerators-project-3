from __future__ import annotations

import json
from pathlib import Path

from intelligence.schemas.supplier import Supplier


DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "suppliers.json"
)


class SupplierRepository:
    """Repository for structured supplier profiles."""

    def __init__(self, data_path: Path = DATA_PATH) -> None:
        self.data_path = data_path
        self._suppliers: list[Supplier] | None = None

    def _load_suppliers(self) -> list[Supplier]:
        """Load and validate supplier profiles."""
        if self._suppliers is None:
            with self.data_path.open("r", encoding="utf-8") as file:
                records = json.load(file)

            self._suppliers = [
                Supplier(**record)
                for record in records
            ]

        return self._suppliers

    def find_alternatives(
        self,
        country: str,
        product_category: str,
        exclude_supplier_id: str | None = None,
    ) -> list[Supplier]:
        """Find suppliers serving a country and product category."""

        suppliers = self._load_suppliers()

        matches = [
            supplier
            for supplier in suppliers
            if country in supplier.countries_served
            and product_category in supplier.product_categories
            and supplier.supplier_id != exclude_supplier_id
        ]

        return sorted(
            matches,
            key=lambda supplier: supplier.reliability_score,
            reverse=True,
        )