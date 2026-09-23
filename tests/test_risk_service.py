import pytest

from intelligence.services.risk_service import RiskService


@pytest.fixture
def risk_service():
    return RiskService()


def test_assess_shipment(risk_service):
    shipment = {
        "scheduled_days": 2,
        "market": "USCA",
        "order_region": "Western Europe",
        "order_country": "Francia",
        "item_count": 2,
        "total_quantity": 3,
        "avg_product_price": 45.0,
        "total_sales": 135.0,
        "avg_discount_rate": 0.10,
        "customer_segment": "Consumer",
    }

    result = risk_service.assess_shipment(shipment)

    assert 0.0 <= result["risk_probability"] <= 1.0
    assert result["threshold"] == 0.39
    assert isinstance(result["is_at_risk"], bool)