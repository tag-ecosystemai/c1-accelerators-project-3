from __future__ import annotations

from typing import Any

import httpx

from intelligence.repositories.route_repository import RouteRepository
from intelligence.repositories.shipment_repository import ShipmentRepository
from intelligence.schemas.route import RouteAlternative, RouteContext


class RouteTools:
    """Tools for DataCo route intelligence and real SaaS routing."""

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

    HEADERS = {
        "User-Agent": "SentinelAI/1.0 (supply-chain-disruption-agent)"
    }

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
        Retrieve geographic context for a DataCo shipment.
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
        Find DataCo/demo alternative routes.

        Kept for compatibility with the existing DataCo agent.
        """
        shipment = self.shipment_repository.get_shipment(shipment_id)

        if shipment is None:
            return []

        return self.route_repository.find_alternatives(
            country=shipment.destination_country,
            region=shipment.order_region,
            shipping_mode=shipment.shipping_mode,
        )

    def _geocode(
        self,
        location: str,
    ) -> tuple[float, float] | None:
        """Resolve a place name to longitude and latitude."""
        if not location:
            return None

        try:
            response = httpx.get(
                self.NOMINATIM_URL,
                params={
                    "q": location,
                    "format": "json",
                    "limit": 1,
                },
                headers=self.HEADERS,
                timeout=10.0,
            )
            response.raise_for_status()

            results = response.json()

            if not results:
                return None

            return (
                float(results[0]["lon"]),
                float(results[0]["lat"]),
            )

        except (
            httpx.HTTPError,
            KeyError,
            TypeError,
            ValueError,
        ):
            return None

    def find_real_routes(
        self,
        origin: str,
        destination: str,
    ) -> list[dict[str, Any]]:
        """
        Calculate real road routes between two locations.

        Uses OpenStreetMap Nominatim for geocoding and OSRM for routing.
        Returns no route when the locations cannot be resolved or the
        routing service fails.
        """
        if not origin or not destination:
            return []

        origin_coordinates = self._geocode(origin)
        destination_coordinates = self._geocode(destination)

        if not origin_coordinates or not destination_coordinates:
            return []

        origin_lon, origin_lat = origin_coordinates
        destination_lon, destination_lat = destination_coordinates

        coordinates = (
            f"{origin_lon},{origin_lat};"
            f"{destination_lon},{destination_lat}"
        )

        try:
            response = httpx.get(
                f"{self.OSRM_URL}/{coordinates}",
                params={
                    "alternatives": "true",
                    "overview": "false",
                    "steps": "false",
                },
                headers=self.HEADERS,
                timeout=15.0,
            )
            response.raise_for_status()

            payload = response.json()

            if payload.get("code") != "Ok":
                return []

            routes = payload.get("routes", [])

            return [
                {
                    "route_id": index + 1,
                    "source": "openstreetmap_osrm",
                    "distance_km": round(
                        float(route["distance"]) / 1000,
                        2,
                    ),
                    "duration_minutes": round(
                        float(route["duration"]) / 60,
                        1,
                    ),
                    "recommendation": (
                        "Primary route"
                        if index == 0
                        else "Alternative route"
                    ),
                }
                for index, route in enumerate(routes)
            ]

        except (
            httpx.HTTPError,
            KeyError,
            TypeError,
            ValueError,
        ):
            return []