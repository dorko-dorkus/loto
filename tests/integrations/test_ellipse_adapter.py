from loto.integrations.ellipse_adapter import DemoEllipseAdapter


def test_demo_adapter_returns_work_order_and_permit() -> None:
    adapter = DemoEllipseAdapter()
    wo = adapter.fetch_work_order("WO-1")
    permit = adapter.fetch_permit("WO-1")
    assert wo["id"] == "WO-1"
    assert permit == {
        "id": "PRM-1",
        "status": "Active",
        "applied_isolations": ["ISO-1", "ISO-2"],
    }
