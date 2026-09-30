from __future__ import annotations

from intelligence.repositories.supplier_repository import SupplierRepository
from intelligence.schemas.supplier import Supplier


class SupplierTools:
    """Tools for finding alternative suppliers."""

    def __init__(
        self,
        repository: SupplierRepository | None = None,
    ) -> None:
        self.repository = repository or SupplierRepository()

    def find_alternative_suppliers(
        self,
        country: str,
        product_category: str,
        exclude_supplier_id: str | None = None,
    ) -> list[Supplier]:
        """
        Find suppliers serving a destination country and product category.

        Args:
            country: Destination country.
            product_category: Required product category.
            exclude_supplier_id: Supplier to exclude from results.

        Returns:
            Matching suppliers ordered by reliability score.
        """
        return self.repository.find_alternatives(
            country=country,
            product_category=product_category,
            exclude_supplier_id=exclude_supplier_id,
        )