import pandas as pd

from intelligence.models.risk_model import RiskModel


def test_risk_model_prediction():
    model = RiskModel()

    shipment = pd.DataFrame([
        {
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
    ])

    result = model.predict(shipment)

    assert "risk_probability" in result
    assert "threshold" in result
    assert "is_at_risk" in result

    assert 0.0 <= result["risk_probability"] <= 1.0
    assert result["threshold"] == 0.39
    assert isinstance(result["is_at_risk"], bool)