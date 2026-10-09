from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from intelligence.services.risk_service import RiskService
from intelligence.tools.news_tools import NewsTools
from intelligence.tools.route_tools import RouteTools
from intelligence.tools.weather_tools import WeatherTools

from backend.services.knowledge_service import KnowledgeService
from backend.services.risk_state import determine_risk_state


class SaaSInvestigationService:
    """
    Builds an evidence-grounded investigation for a persisted shipment.

    External signals are optional and fail gracefully. CatBoost is used
    only when the shipment genuinely contains every feature required by
    the trained model.
    """

    def __init__(
        self,
        weather_tools: WeatherTools | None = None,
        route_tools: RouteTools | None = None,
        news_tools: NewsTools | None = None,
        knowledge_service: KnowledgeService | None = None,
        risk_service: RiskService | None = None,
    ) -> None:
        self.weather_tools = weather_tools or WeatherTools()
        self.route_tools = route_tools or RouteTools()
        self.news_tools = news_tools or NewsTools()
        self.knowledge_service = (
            knowledge_service or KnowledgeService()
        )
        self.risk_service = risk_service or RiskService()

    @staticmethod
    def _build_model_features(shipment) -> dict[str, Any]:
        metadata = shipment.metadata_json or {}

        return {
            key: metadata[key]
            for key in RiskService.REQUIRED_FEATURES
            if key in metadata
        }

    @staticmethod
    def _shipment_context(shipment) -> dict[str, Any]:
        metadata = shipment.metadata_json or {}

        return {
            "shipment_id": shipment.shipment_id,
            "tracking_number": shipment.tracking_number,
            "carrier": shipment.carrier,
            "origin": shipment.origin,
            "destination": shipment.destination,
            "estimated_arrival": (
                shipment.estimated_arrival.isoformat()
                if shipment.estimated_arrival
                else None
            ),
            "current_status": shipment.current_status,
            "shipping_mode": shipment.shipping_mode,
            "supplier": metadata.get("supplier"),
            "product_category": metadata.get(
                "product_category"
            ),
            "priority": metadata.get("priority"),
            "shipment_value": metadata.get(
                "shipment_value"
            ),
        }

    @staticmethod
    def _coordinates_available(
        coordinates: dict[str, Any] | None,
    ) -> bool:
        return bool(
            coordinates
            and "latitude" in coordinates
            and "longitude" in coordinates
        )

    def _get_weather(
        self,
        shipment,
        evidence: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not self._coordinates_available(
            shipment.destination_coordinates
        ):
            return None

        try:
            coordinates = shipment.destination_coordinates

            weather = self.weather_tools.get_weather(
                latitude=float(coordinates["latitude"]),
                longitude=float(coordinates["longitude"]),
            )

            weather_data = (
                weather.model_dump()
                if hasattr(weather, "model_dump")
                else weather
            )

            evidence.append(
                {
                    "type": "weather",
                    "source": "open_meteo",
                    "value": weather_data,
                }
            )

            return weather_data

        except Exception:
            return None

    def _get_route_options(
        self,
        shipment,
        evidence: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not shipment.origin or not shipment.destination:
            return []

        try:
            routes = self.route_tools.find_real_routes(
                origin=shipment.origin,
                destination=shipment.destination,
            )

            if routes:
                evidence.append(
                    {
                        "type": "route_options",
                        "source": "openstreetmap_osrm",
                        "value": routes,
                    }
                )

            return routes

        except Exception:
            return []

    def _get_news(
        self,
        shipment,
        evidence: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        destination = shipment.destination or ""

        if not destination:
            return []

        country = destination.split(",")[-1].strip()

        if not country:
            return []

        try:
            articles = self.news_tools.find_disruption_news(
                country=country,
                keywords=[
                    "shipping",
                    "port",
                    "logistics",
                    "disruption",
                    "delay",
                ],
                timespan="7d",
                max_records=5,
            )

            news_data = [
                (
                    article.model_dump()
                    if hasattr(article, "model_dump")
                    else article
                )
                for article in articles
            ]

            if news_data:
                evidence.append(
                    {
                        "type": "external_news",
                        "source": "gdelt",
                        "value": news_data,
                    }
                )

            return news_data

        except Exception:
            return []

    @staticmethod
    def _get_supplier_options(
        shipment,
    ) -> list[dict[str, Any]]:
        """
        Return supplier alternatives only when supplier information was
        genuinely supplied in the shipment dataset.

        The demo dataset may contain an alternative_suppliers field as a
        list of supplier records. No suppliers are invented here.
        """
        metadata = shipment.metadata_json or {}

        alternatives = metadata.get("alternative_suppliers")

        if isinstance(alternatives, list):
            return [
                supplier
                for supplier in alternatives
                if isinstance(supplier, dict)
            ]

        return []

    def _retrieve_knowledge(
        self,
        shipment,
        operational_risk_state: str,
        company_id: int | None,
    ) -> list[dict[str, Any]]:
        knowledge_query = (
            f"Shipment investigation for a "
            f"{operational_risk_state} shipment. "
            f"Status: {shipment.current_status or 'unknown'}. "
            f"Carrier: {shipment.carrier or 'unknown'}. "
            f"Origin: {shipment.origin or 'unknown'}. "
            f"Destination: {shipment.destination or 'unknown'}. "
            f"Shipping mode: {shipment.shipping_mode or 'unknown'}. "
            "What operational procedures, escalation guidance, "
            "or recommended human review apply?"
        )

        try:
            return self.knowledge_service.retrieve(
                query=knowledge_query,
                company_id=company_id,
                top_k=5,
            )
        except Exception:
            return []

    def investigate(
        self,
        shipment,
        company_id: int | None = None,
    ) -> dict[str, Any]:
        operational_risk_state = determine_risk_state(
            current_status=shipment.current_status,
            estimated_arrival=shipment.estimated_arrival,
        )

        model_features = self._build_model_features(shipment)

        ml_risk = self.risk_service.assess_shipment(
            model_features
        )

        evidence: list[dict[str, Any]] = []

        evidence.append(
            {
                "type": "shipment_status",
                "source": "company_shipment_data",
                "value": shipment.current_status,
            }
        )

        if shipment.estimated_arrival:
            evidence.append(
                {
                    "type": "estimated_arrival",
                    "source": "company_shipment_data",
                    "value": shipment.estimated_arrival.isoformat(),
                }
            )

        if ml_risk["available"]:
            evidence.append(
                {
                    "type": "ml_risk_prediction",
                    "source": "sentinelai_catboost",
                    "value": {
                        "risk_probability": ml_risk[
                            "risk_probability"
                        ],
                        "threshold": ml_risk["threshold"],
                        "is_at_risk": ml_risk["is_at_risk"],
                    },
                }
            )
        else:
            evidence.append(
                {
                    "type": "ml_risk_prediction",
                    "source": "sentinelai_catboost",
                    "value": "unavailable",
                }
            )

        weather = self._get_weather(
            shipment=shipment,
            evidence=evidence,
        )

        route_options = self._get_route_options(
            shipment=shipment,
            evidence=evidence,
        )

        news_results = self._get_news(
            shipment=shipment,
            evidence=evidence,
        )

        supplier_options = self._get_supplier_options(
            shipment=shipment,
        )

        if supplier_options:
            evidence.append(
                {
                    "type": "supplier_options",
                    "source": "company_shipment_data",
                    "value": supplier_options,
                }
            )

        knowledge_results = self._retrieve_knowledge(
            shipment=shipment,
            operational_risk_state=operational_risk_state,
            company_id=company_id,
        )

        return {
            "shipment": self._shipment_context(shipment),
            "risk": {
                "state": operational_risk_state,
                "assessed_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "ml_available": ml_risk["available"],
                "ml_probability": ml_risk["risk_probability"],
                "ml_threshold": ml_risk["threshold"],
                "ml_is_at_risk": ml_risk["is_at_risk"],
                "ml_missing_features": ml_risk[
                    "missing_features"
                ],
            },
            "weather": weather,
            "route_options": route_options,
            "supplier_options": supplier_options,
            "news_results": news_results,
            "evidence": evidence,
            "knowledge_results": knowledge_results,
        }