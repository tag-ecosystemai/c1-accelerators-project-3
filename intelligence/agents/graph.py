from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from intelligence.agents.state import AgentState
from intelligence.repositories.risk_feature_repository import RiskFeatureRepository
from intelligence.services.investigation_service import InvestigationService
from intelligence.services.risk_service import RiskService
from intelligence.services.knowledge_service import KnowledgeService


def assess_risk(
    state: AgentState,
    risk_feature_repository: RiskFeatureRepository,
    risk_service: RiskService,
) -> AgentState:
    """Assess shipment risk using the trained ML model."""
    shipment_id = state.get("shipment_id")

    if not shipment_id:
        raise ValueError("Shipment ID is required for risk assessment.")

    features = risk_feature_repository.get_features(shipment_id)

    if features is None:
        raise ValueError(
            f"Risk features not found for shipment: {shipment_id}"
        )

    prediction = risk_service.assess_shipment(
        features.model_dump()
    )

    state["risk_assessment"] = {
        "probability": prediction["risk_probability"],
        "threshold": prediction["threshold"],
        "is_at_risk": prediction["is_at_risk"],
    }

    return state


def route_by_risk(
    state: AgentState,
) -> Literal["investigate", "finish"]:
    """Route the investigation based on shipment risk."""
    risk = state.get("risk_assessment")

    if not risk:
        raise ValueError("Risk assessment is required before routing.")

    if risk["is_at_risk"]:
        return "investigate"

    return "finish"


def investigate(
    state: AgentState,
    investigation_service: InvestigationService,
) -> AgentState:
    """Collect deterministic evidence for an at-risk shipment."""
    shipment_id = state.get("shipment_id")

    if not shipment_id:
        raise ValueError("Shipment ID is required for investigation.")

    result = investigation_service.investigate_shipment(
        shipment_id
    )

    state["shipment"] = result["shipment"]
    state["route_context"] = result["route_context"]
    state["route_options"] = result["route_options"]#
    state["supplier_options"] = result["supplier_options"]

    if result["weather"] is not None:
        state["weather"] = result["weather"]

    return state


def finish(state: AgentState) -> AgentState:
    """Finish the investigation workflow."""
    return state

def retrieve_knowledge(
    state: AgentState,
    knowledge_service: KnowledgeService,
) -> AgentState:
    """Retrieve relevant operational procedures for the investigation."""

    shipment_id = state.get("shipment_id")

    if not shipment_id:
        raise ValueError(
            "Shipment ID is required for knowledge retrieval."
        )

    risk = state.get("risk_assessment")

    if not risk:
        raise ValueError(
            "Risk assessment is required before knowledge retrieval."
        )

    query = (
        f"Shipment {shipment_id} has elevated late-delivery risk. "
        "What operational procedures apply to investigating the disruption, "
        "evaluating mitigation options, and escalating potential inventory risk?"
    )

    results = knowledge_service.retrieve_procedures(
        query=query,
        top_k=3,
    )

    state["knowledge_results"] = results

    return state


def build_graph(
    risk_feature_repository: RiskFeatureRepository | None = None,
    risk_service: RiskService | None = None,
    investigation_service: InvestigationService | None = None,
    knowledge_service: KnowledgeService | None = None,
):
    """Build the SentinelAI investigation graph."""

    risk_feature_repository = (
        risk_feature_repository or RiskFeatureRepository()
    )

    risk_service = risk_service or RiskService()

    investigation_service = (
        investigation_service or InvestigationService()
    )

    knowledge_service = (
        knowledge_service or KnowledgeService()
    )

    graph = StateGraph(AgentState)

    graph.add_node(
        "assess_risk",
        lambda state: assess_risk(
            state,
            risk_feature_repository,
            risk_service,
        ),
    )

    graph.add_node(
        "investigate",
        lambda state: investigate(
            state,
            investigation_service,
        ),
    )

    # 3.3 — ADD THIS NODE
    graph.add_node(
        "retrieve_knowledge",
        lambda state: retrieve_knowledge(
            state,
            knowledge_service,
        ),
    )

    graph.add_node("finish", finish)

    graph.add_edge(START, "assess_risk")

    graph.add_conditional_edges(
        "assess_risk",
        route_by_risk,
        {
            "investigate": "investigate",
            "finish": "finish",
        },
    )

    # CHANGE THE EXISTING INVESTIGATE → FINISH EDGE
    graph.add_edge("investigate", "retrieve_knowledge")

    # ADD THIS
    graph.add_edge("retrieve_knowledge", "finish")

    graph.add_edge("finish", END)

    return graph.compile()