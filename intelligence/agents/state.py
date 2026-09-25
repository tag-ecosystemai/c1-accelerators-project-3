from __future__ import annotations

from typing import TypedDict

from intelligence.schemas.news import NewsArticle
from intelligence.schemas.route import RouteAlternative, RouteContext
from intelligence.schemas.shipment import Shipment
from intelligence.schemas.supplier import Supplier
from intelligence.schemas.weather import WeatherObservation
from intelligence.schemas.knowledge import KnowledgeResult

class RiskAssessment(TypedDict):
    probability: float
    threshold: float
    is_at_risk: bool


class AgentState(TypedDict, total=False):
    """State carried through a SentinelAI shipment investigation."""

    shipment_id: str

    shipment: Shipment
    risk_assessment: RiskAssessment

    route_context: RouteContext
    weather: WeatherObservation

    route_options: list[RouteAlternative]
    supplier_options: list[Supplier]
    news: list[NewsArticle]
    knowledge_results: list[KnowledgeResult]

    retrieved_procedures: list[str]

    investigation_findings: list[str]
    recommended_actions: list[str]

    briefing: str