from intelligence.tools.route_tools import RouteTools


def test_get_route_context():
    tools = RouteTools()

    route = tools.get_route_context("77202")

    assert route is not None
    assert route.destination_city == "Bekasi"
    assert route.destination_country == "Indonesia"
    assert route.order_region == "Southeast Asia"
    assert route.shipping_mode == "Standard Class"


def test_find_alternative_routes():
    tools = RouteTools()

    routes = tools.find_alternative_route("77202")

    assert len(routes) == 1

    alternative = routes[0]

    assert alternative.route_id == "ROUTE-002"
    assert alternative.route_name == "Southeast Asia Express Route"
    assert alternative.demo_reliability_score == 0.93
    assert "Standard Class" not in alternative.shipping_modes


def test_missing_shipment_returns_no_routes():
    tools = RouteTools()

    routes = tools.find_alternative_route("does-not-exist")

    assert routes == []