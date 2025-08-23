import importlib

from fastapi.testclient import TestClient


def test_admin_validate_reports_missing_refs():
    import apps.api.main as main

    importlib.reload(main)

    client = TestClient(main.app)

    res = client.post("/admin/validate")
    assert res.status_code == 200
    assert res.json() == {"missing_assets": [], "missing_locations": []}

    bad_asset = {
        "id": "WO-X",
        "description": "",
        "status": "",
        "assetnum": "BAD",
        "location": "L-1",
    }
    bad_location = {
        "id": "WO-Y",
        "description": "",
        "status": "",
        "assetnum": "A-1",
        "location": "BADLOC",
    }
    main.demo_data.work_orders.extend([bad_asset, bad_location])
    main.demo_data._work_orders_by_id[bad_asset["id"]] = bad_asset
    main.demo_data._work_orders_by_id[bad_location["id"]] = bad_location

    res = client.post("/admin/validate")
    assert res.status_code == 400
    data = res.json()
    assert data["missing_assets"] == [{"workorder": "WO-X", "assetnum": "BAD"}]
    assert data["missing_locations"] == [{"workorder": "WO-Y", "location": "BADLOC"}]
    import apps.api.demo_data as demo_module

    importlib.reload(demo_module)
    importlib.reload(main)
