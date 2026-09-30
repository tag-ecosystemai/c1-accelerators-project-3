from intelligence.tools.shipment_tools import ShipmentTools


def test_get_shipment_status():
    tools = ShipmentTools()

    shipment = tools.get_shipment_status("77202")

    assert shipment is not None
    assert shipment.shipment_id == "77202"
    assert shipment.status == "advance_shipping"
    assert shipment.destination_city == "Bekasi"
    assert shipment.destination_country == "Indonesia"
    assert shipment.shipping_mode == "Standard Class"


def test_get_shipment_status_missing():
    tools = ShipmentTools()

    shipment = tools.get_shipment_status("does-not-exist")

    assert shipment is None