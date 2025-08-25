from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, TypedDict, cast

import structlog
import yaml

from ..constants import DOC_CATEGORY_DIR
from . import IntegrationAdapter

logger = structlog.get_logger()

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from ..models import IsolationPlan, SimReport


DEMO_DIR = Path(__file__).resolve().parents[2] / "demo"


class WorkOrder(TypedDict):
    """Shape of a work order returned by the adapter."""

    id: str
    description: str
    asset_id: str


class Asset(TypedDict):
    """Shape of an asset returned by the adapter."""

    id: str
    description: str
    location: str


class DemoIntegrationAdapter(IntegrationAdapter):
    """Demo adapter that reads fixture data and writes artifacts to disk."""

    def __init__(self) -> None:
        self._work_orders_raw = {
            row["id"]: row for row in self._load_records("work_orders")
        }
        self._assets = {row["id"]: row for row in self._load_records("assets")}

    # internal helpers
    def _load_records(self, name: str) -> List[Dict[str, Any]]:
        stem = DEMO_DIR / name
        csv_path = stem.with_suffix(".csv")
        yaml_path = stem.with_suffix(".yaml")
        yml_path = stem.with_suffix(".yml")
        if csv_path.exists():
            with csv_path.open(newline="") as fh:
                return list(csv.DictReader(fh))
        if yaml_path.exists():
            return yaml.safe_load(yaml_path.read_text()) or []
        if yml_path.exists():
            return yaml.safe_load(yml_path.read_text()) or []
        return []

    def get_work_order(self, work_order_id: str) -> WorkOrder:
        row = self._work_orders_raw[work_order_id]
        return {
            "id": row["id"],
            "description": row.get("description", ""),
            "asset_id": row.get("asset_id", ""),
        }

    def list_open_work_orders(self, window: int) -> List[WorkOrder]:
        return [
            self.get_work_order(row["id"])
            for row in self._work_orders_raw.values()
            if row.get("status", "").upper() == "OPEN"
        ]

    def get_asset(self, asset_id: str) -> Asset:
        row = self._assets[asset_id]
        return {
            "id": row["id"],
            "description": row.get("description", ""),
            "location": row.get("location", ""),
        }

    def fetch_work_order(self, work_order_id: str) -> Dict[str, Any]:
        """Return fixture information about a work order."""
        return cast(Dict[str, Any], self.get_work_order(work_order_id))

    def create_child_work_orders(
        self, parent_work_order_id: str, plan: IsolationPlan
    ) -> List[str]:
        """Return fabricated child work order identifiers."""
        count = len(plan.actions) + len(plan.verifications)
        return [f"{parent_work_order_id}-{uuid.uuid4().hex[:8]}" for _ in range(count)]

    def attach_artifacts(
        self,
        parent_object_id: str,
        plan: IsolationPlan,
        sim_report: SimReport,
        as_json: Dict[str, Any],
        pdf_bytes: bytes,
    ) -> None:
        """Write artifacts to ``out/doclinks/<category>`` relative to the CWD."""
        output_dir = Path("out") / "doclinks" / DOC_CATEGORY_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / f"{parent_object_id}.json"
        pdf_path = output_dir / f"{parent_object_id}.pdf"
        json_path.write_text(json.dumps(as_json))
        pdf_path.write_bytes(pdf_bytes)
        logger.info(
            "artifacts_attached",
            parent_id=parent_object_id,
            json_path=str(json_path),
            pdf_path=str(pdf_path),
        )
