from __future__ import annotations

from intelligence.services.llm_service import LLMService


class SaaSBriefingService:
    """
    Generates an evidence-grounded briefing from a SaaS investigation.

    This service intentionally uses the canonical SaaS investigation
    context rather than the DataCo-specific agent graph.
    """

    def __init__(
        self,
        llm_service: LLMService | None = None,
    ) -> None:
        self.llm_service = llm_service or LLMService()

    def generate(self, investigation: dict) -> str:
        return self.llm_service.generate_saas_briefing(
            shipment=investigation["shipment"],
            risk=investigation["risk"],
            weather=investigation.get("weather"),
            route_options=investigation.get(
                "route_options",
                [],
            ),
            supplier_options=investigation.get(
                "supplier_options",
                [],
            ),
            news_results=investigation.get(
                "news_results",
                [],
            ),
            evidence=investigation.get(
                "evidence",
                [],
            ),
            knowledge_results=investigation.get(
                "knowledge_results",
                [],
            ),
        )