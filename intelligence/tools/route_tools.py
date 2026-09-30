from __future__ import annotations

from intelligence.repositories.route_repository import RouteRepository
from intelligence.repositories.shipment_repository import ShipmentRepository
from intelligence.schemas.route import RouteAlternative, RouteContext


class RouteTools:
    """Tools for retrieving shipment route information."""

    def __init__(
        self,
        shipment_repository: ShipmentRepository | None = None,
        route_repository: RouteRepository | None = None,
    ) -> None:
        self.shipment_repository = (
            shipment_repository or ShipmentRepository()
        )
        self.route_repository = (
            route_repository or RouteRepository()
        )

    def get_route_context(
        self,
        shipment_id: str,
    ) -> RouteContext | None:
        """
        Retrieve geographic context for a shipment.

        Args:
            shipment_id: Unique shipment identifier.

        Returns:
            Route context if the shipment exists, otherwise None.
        """
        shipment = self.shipment_repository.get_shipment(shipment_id)

        if shipment is None:
            return None

        return RouteContext(
            destination_city=shipment.destination_city,
            destination_country=shipment.destination_country,
            order_region=shipment.order_region,
            shipping_mode=shipment.shipping_mode,
        )

    def find_alternative_route(
        self,
        shipment_id: str,
    ) -> list[RouteAlternative]:
        """
        Find alternative routes for a shipment.

        Args:
            shipment_id: Unique shipment identifier.

        Returns:
            Matching alternative routes.
        """
        shipment = self.shipment_repository.get_shipment(shipment_id)

        if shipment is None:
            return []

        return self.route_repository.find_alternatives(
            country=shipment.destination_country,
            region=shipment.order_region,
            shipping_mode=shipment.shipping_mode,
        )