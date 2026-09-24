from __future__ import annotations

import json
from pathlib import Path

from intelligence.schemas.route import RouteAlternative


DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "routes.json"
)


class RouteRepository:
    """Repository for structured route alternatives."""

    def __init__(self, data_path: Path = DATA_PATH) -> None:
        self.data_path = data_path
        self._routes: list[RouteAlternative] | None = None

    def _load_routes(self) -> list[RouteAlternative]:
        """Load and validate route alternatives."""
        if self._routes is None:
            with self.data_path.open("r", encoding="utf-8") as file:
                records = json.load(file)

            self._routes = [
                RouteAlternative(**record)
                for record in records
            ]

        return self._routes

    def find_alternatives(
        self,
        country: str,
        region: str,
        shipping_mode: str,
    ) -> list[RouteAlternative]:
        """Find alternative routes using a different shipping mode."""

        routes = self._load_routes()

        matches = [
            route
            for route in routes
            if country in route.destination_countries
            and region == route.region
            and shipping_mode not in route.shipping_modes
        ]

        return sorted(
            matches,
            key=lambda route: route.demo_reliability_score,
            reverse=True,
        )