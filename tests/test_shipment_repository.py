from intelligence.repositories.shipment_repository import ShipmentRepository


def test_get_existing_shipment():
    repository = ShipmentRepository()

    shipment = repository.get_shipment("77202")

    assert shipment is not None
    assert shipment.shipment_id == "77202"
    assert shipment.status == "advance_shipping"
    assert shipment.destination_city == "Bekasi"
    assert shipment.destination_country == "Indonesia"
    assert shipment.order_region == "Southeast Asia"
    assert shipment.shipping_mode == "Standard Class"
    assert shipment.scheduled_shipping_days == 4


def test_get_missing_shipment():
    repository = ShipmentRepository()

    shipment = repository.get_shipment("does-not-exist")

    assert shipment is None