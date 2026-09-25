from __future__ import annotations

from intelligence.schemas.knowledge import KnowledgeResult


class KnowledgeService:
    """Interface between the investigation agent and the knowledge system."""

    def retrieve_procedures(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[KnowledgeResult]:
        """Return relevant operational procedures for an investigation."""

        return [
            KnowledgeResult(
                content=(
                    "Confirm the shipment status, review route conditions, "
                    "evaluate alternative routes and supplier options, "
                    "and escalate when the disruption could create "
                    "downstream inventory risk."
                ),
                source="disruption_response.md",
                relevance_score=0.95,
            )
        ][:top_k]