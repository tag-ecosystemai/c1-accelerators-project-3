from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.services.briefing_service import SaaSBriefingService
from backend.services.investigation_service import (
    SaaSInvestigationService,
)


class SaaSAgentState(TypedDict, total=False):
    shipment: Any
    company_id: int | None
    investigation: dict[str, Any]
    briefing: str


def investigate_shipment(
    state: SaaSAgentState,
    investigation_service: SaaSInvestigationService,
) -> SaaSAgentState:
    """Run the evidence-gathering investigation tools."""

    shipment = state.get("shipment")

    if shipment is None:
        raise ValueError(
            "Shipment is required for SaaS investigation."
        )

    state["investigation"] = investigation_service.investigate(
        shipment=shipment,
        company_id=state.get("company_id"),
    )

    return state


def generate_briefing(
    state: SaaSAgentState,
    briefing_service: SaaSBriefingService,
) -> SaaSAgentState:
    """Generate the final evidence-grounded operations briefing."""

    investigation = state.get("investigation")

    if investigation is None:
        raise ValueError(
            "Investigation results are required before briefing generation."
        )

    state["briefing"] = briefing_service.generate(
        investigation
    )

    return state


class SaaSAgentService:
    """
    LangGraph orchestration for the canonical SentinelAI SaaS workflow.

    The graph coordinates the investigation tools and briefing stage.
    Individual tools remain responsible for their own external data
    retrieval and graceful handling of unavailable evidence.
    """

    def __init__(
        self,
        investigation_service: SaaSInvestigationService | None = None,
        briefing_service: SaaSBriefingService | None = None,
    ) -> None:
        self.investigation_service = (
            investigation_service
            or SaaSInvestigationService()
        )

        self.briefing_service = (
            briefing_service
            or SaaSBriefingService()
        )

        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(SaaSAgentState)

        workflow.add_node(
            "investigate",
            lambda state: investigate_shipment(
                state,
                self.investigation_service,
            ),
        )

        workflow.add_node(
            "generate_briefing",
            lambda state: generate_briefing(
                state,
                self.briefing_service,
            ),
        )

        workflow.add_edge(
            START,
            "investigate",
        )

        workflow.add_edge(
            "investigate",
            "generate_briefing",
        )

        workflow.add_edge(
            "generate_briefing",
            END,
        )

        return workflow.compile()

    def run(
        self,
        shipment,
        company_id: int | None = None,
    ) -> dict[str, Any]:
        """Run the SaaS investigation agent."""

        result = self.graph.invoke(
            {
                "shipment": shipment,
                "company_id": company_id,
            }
        )

        investigation = result.get(
            "investigation",
            {},
        )

        return {
            **investigation,
            "briefing": result.get(
                "briefing",
                "",
            ),
        }