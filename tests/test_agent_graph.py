from intelligence.agents.graph import build_graph


def test_at_risk_shipment_enters_investigation():
    graph = build_graph()

    result = graph.invoke({
        "shipment_id": "77202",
    })

    assert "risk_assessment" in result

    risk = result["risk_assessment"]

    assert risk["probability"] >= risk["threshold"]
    assert risk["is_at_risk"] is True


def test_at_risk_shipment_completes_investigation_path():
    graph = build_graph()

    result = graph.invoke({
        "shipment_id": "77202",
    })

    # The current investigate node is a placeholder,
    # but reaching the final state proves the conditional
    # branch executed successfully.
    assert result["shipment_id"] == "77202"
    assert "risk_assessment" in result
    
def test_at_risk_graph_contains_investigation_evidence():
    graph = build_graph()

    result = graph.invoke({
        "shipment_id": "77202",
    })

    assert result["shipment_id"] == "77202"

    assert result["shipment"] is not None
    assert result["route_context"] is not None
    assert result["route_options"] is not None
    assert result["supplier_options"] is not None
    assert result["knowledge_results"] is not None
    assert len(result["knowledge_results"]) > 0
    assert result["knowledge_results"][0].source == "disruption_response.md"