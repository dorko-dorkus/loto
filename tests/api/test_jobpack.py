import csv
import hashlib
import io
import json
from datetime import date, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import RULE_PACK_HASH, RULE_PACK_ID, RULE_PACK_VERSION, app


def test_jobpack_endpoint() -> None:
    client = TestClient(app)
    wo_id = "123"
    res = client.get(f"/workorders/{wo_id}/jobpack")
    assert res.status_code == 200
    data = res.json()
    assert "csv" in data and "json" in data
    assert data["rulepack_sha256"] == RULE_PACK_HASH
    assert data["rulepack_id"] == RULE_PACK_ID
    assert data["rulepack_version"] == RULE_PACK_VERSION
    assert data["seed"] == "0"

    csv_info = data["csv"]
    json_info = data["json"]

    # filenames derived from content hash
    csv_content = csv_info["content"]
    csv_hash = hashlib.sha256(csv_content.encode()).hexdigest()
    assert csv_info["filename"].startswith(csv_hash)

    json_content = json_info["content"]
    json_hash = hashlib.sha256(
        json.dumps(json_content, sort_keys=True).encode()
    ).hexdigest()
    assert json_info["filename"].startswith(json_hash)
    assert json_content["maximo_wo"] == wo_id
    assert json_content["rulepack_sha256"] == RULE_PACK_HASH
    assert json_content["rulepack_id"] == RULE_PACK_ID
    assert json_content["rulepack_version"] == RULE_PACK_VERSION
    assert json_content["seed"] == "0"

    # pick_by is permit_start minus two days
    permit_start = date.fromisoformat(json_content["permit_start"])
    pick_by = date.fromisoformat(json_content["pick_by"])
    assert permit_start - pick_by == timedelta(days=2)

    # CSV has storeroom and bin columns
    reader = csv.DictReader(io.StringIO(csv_content))
    row = next(reader)
    assert "storeroom" in row and "bin" in row

    out_dir = Path("out/jobpacks") / f"WO-{wo_id}"
    assert (out_dir / csv_info["filename"]).exists()
    assert (out_dir / json_info["filename"]).exists()
