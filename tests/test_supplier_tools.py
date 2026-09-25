from intelligence.tools.supplier_tools import SupplierTools


def test_find_alternative_suppliers():
    tools = SupplierTools()

    suppliers = tools.find_alternative_suppliers(
        country="Indonesia",
        product_category="Electronics",
    )

    assert len(suppliers) == 1
    assert suppliers[0].supplier_id == "SUP-001"
    assert suppliers[0].supplier_name == "Nexa Electronics Supply"
    assert suppliers[0].reliability_score == 0.91


def test_no_matching_supplier():
    tools = SupplierTools()

    suppliers = tools.find_alternative_suppliers(
        country="Indonesia",
        product_category="Sporting Goods",
    )

    assert suppliers == []


def test_exclude_supplier():
    tools = SupplierTools()

    suppliers = tools.find_alternative_suppliers(
        country="Indonesia",
        product_category="Electronics",
        exclude_supplier_id="SUP-001",
    )

    assert suppliers == []