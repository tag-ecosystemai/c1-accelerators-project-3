from intelligence.repositories.risk_feature_repository import RiskFeatureRepository


def test_get_features_for_known_shipment():
    repository = RiskFeatureRepository()

    features = repository.get_features("77202")

    assert features is not None
    assert features.scheduled_days == 4
    assert features.market == "Pacific Asia"
    assert features.order_region == "Southeast Asia"
    assert features.order_country == "Indonesia"
    assert features.item_count == 1
    assert features.total_quantity == 1
    assert features.avg_product_price == 327.75
    assert features.total_sales == 327.75
    assert features.avg_discount_rate == 0.039999999
    assert features.customer_segment == "Consumer"


def test_missing_shipment_returns_none():
    repository = RiskFeatureRepository()

    features = repository.get_features("does-not-exist")

    assert features is None