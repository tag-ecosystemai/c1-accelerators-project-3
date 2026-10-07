from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from intelligence.agents.state import AgentState
from intelligence.repositories.risk_feature_repository import (
    RiskFeatureRepository,
)
from intelligence.services.investigation_service import InvestigationService
from intelligence.services.knowledge_service import KnowledgeService
from intelligence.services.llm_service import LLMService
from intelligence.services.risk_service import RiskService


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
    """Route the workflow based on the model's risk assessment."""
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
    state["route_options"] = result["route_options"]
    state["supplier_options"] = result["supplier_options"]

    if result.get("weather") is not None:
        state["weather"] = result["weather"]

    if result.get("news") is not None:
        state["news"] = result["news"]

    return state


def retrieve_knowledge(
    state: AgentState,
    knowledge_service: KnowledgeService,
) -> AgentState:
    """Retrieve relevant operational procedures."""
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
        "What operational procedures apply to investigating the "
        "disruption, evaluating mitigation options, and escalating "
        "potential inventory risk?"
    )

    results = knowledge_service.retrieve_procedures(
        query=query,
        top_k=3,
    )

    state["knowledge_results"] = results

    return state


def generate_briefing(
    state: AgentState,
    llm_service: LLMService,
) -> AgentState:
    """Generate an evidence-grounded operational briefing."""
    shipment = state.get("shipment")

    if shipment is None:
        raise ValueError(
            "Shipment information is required before briefing generation."
        )

    risk_assessment = state.get("risk_assessment")

    if risk_assessment is None:
        raise ValueError(
            "Risk assessment is required before briefing generation."
        )

    shipment_data = (
        shipment.model_dump()
        if hasattr(shipment, "model_dump")
        else shipment
    )

    route_context = state.get("route_context")
    route_context_data = (
        route_context.model_dump()
        if hasattr(route_context, "model_dump")
        else route_context
    )

    weather = state.get("weather")
    weather_data = (
        weather.model_dump()
        if hasattr(weather, "model_dump")
        else weather
    )

    route_options = [
        item.model_dump()
        if hasattr(item, "model_dump")
        else item
        for item in state.get("route_options", [])
    ]

    supplier_options = [
        item.model_dump()
        if hasattr(item, "model_dump")
        else item
        for item in state.get("supplier_options", [])
    ]

    news = [
        item.model_dump()
        if hasattr(item, "model_dump")
        else item
        for item in state.get("news", [])
    ]

    knowledge_results = [
        item.model_dump()
        if hasattr(item, "model_dump")
        else item
        for item in state.get("knowledge_results", [])
    ]

    briefing = llm_service.generate_briefing(
        shipment=shipment_data,
        risk_assessment=risk_assessment,
        weather=weather_data,
        route_context=route_context_data,
        route_options=route_options,
        supplier_options=supplier_options,
        news=news,
        knowledge_results=knowledge_results,
        investigation_findings=state.get(
            "investigation_findings",
            [],
        ),
    )

    state["briefing"] = briefing

    return state


def finish(state: AgentState) -> AgentState:
    """Finish the SentinelAI workflow."""
    return state


def build_graph(
    risk_feature_repository: RiskFeatureRepository | None = None,
    risk_service: RiskService | None = None,
    investigation_service: InvestigationService | None = None,
    knowledge_service: KnowledgeService | None = None,
    llm_service: LLMService | None = None,
):
    """Build and compile the SentinelAI investigation graph."""

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

    llm_service = llm_service or LLMService()

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

    graph.add_node(
        "retrieve_knowledge",
        lambda state: retrieve_knowledge(
            state,
            knowledge_service,
        ),
    )

    graph.add_node(
        "generate_briefing",
        lambda state: generate_briefing(
            state,
            llm_service,
        ),
    )

    graph.add_node("finish", finish)

    graph.add_edge(
        START,
        "assess_risk",
    )

    graph.add_conditional_edges(
        "assess_risk",
        route_by_risk,
        {
            "investigate": "investigate",
            "finish": "finish",
        },
    )

    graph.add_edge(
        "investigate",
        "retrieve_knowledge",
    )

    graph.add_edge(
        "retrieve_knowledge",
        "generate_briefing",
    )

    graph.add_edge(
        "generate_briefing",
        "finish",
    )

    graph.add_edge(
        "finish",
        END,
    )

    return graph.compile()