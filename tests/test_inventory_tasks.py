from loto.inventory import InventoryRecord, normalize_units, reorder_flags


def test_normalize_units() -> None:
    items = [
        InventoryRecord(
            description="M12x35 bolt 8.8",
            unit="L",
            qty_onhand=5,
            reorder_point=0,
        )
    ]
    mapping = {"M12x35 bolt 8.8": "ea"}
    normalised = normalize_units(items, mapping)
    assert normalised[0].unit == "ea"


def test_reorder_flags() -> None:
    items = [
        InventoryRecord(
            description="Nitrile gasket DN50",
            unit="ea",
            qty_onhand=0,
            reorder_point=10,
            site="PLANT-02",
        ),
        InventoryRecord(
            description="Widget",
            unit="ea",
            qty_onhand=5,
            reorder_point=2,
        ),
    ]
    flagged = reorder_flags(items)
    assert flagged == [items[0]]
