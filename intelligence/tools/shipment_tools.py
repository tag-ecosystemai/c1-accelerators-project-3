from __future__ import annotations

from intelligence.repositories.shipment_repository import ShipmentRepository
from intelligence.schemas.shipment import Shipment


class ShipmentTools:
    """Tools that provide shipment information to the agent."""

    def __init__(
        self,
        repository: ShipmentRepository | None = None,
    ) -> None:
        self.repository = repository or ShipmentRepository()

    def get_shipment_status(
        self,
        shipment_id: str,
    ) -> Shipment | None:
        """
        Retrieve factual shipment information.

        Args:
            shipment_id: Unique shipment identifier.

        Returns:
            Shipment data if the shipment exists, otherwise None.
        """
        return self.repository.get_shipment(shipment_id)