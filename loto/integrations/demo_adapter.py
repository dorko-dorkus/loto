from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List

from . import IntegrationAdapter

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from ..isolation_planner import IsolationPlan
    from ..models import SimReport


class DemoIntegrationAdapter(IntegrationAdapter):
    """Demo adapter that fabricates responses and writes artifacts to disk."""

    def fetch_work_order(self, work_order_id: str) -> Dict[str, Any]:
        """Return fixture information about a work order."""
        return {
            "id": work_order_id,
            "description": f"Demo work order {work_order_id}",
            "asset_id": "ASSET-DEMO",
        }

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
        """Write artifacts to ``out/doclinks`` relative to the CWD."""
        output_dir = Path("out") / "doclinks"
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / f"{parent_object_id}.json"
        pdf_path = output_dir / f"{parent_object_id}.pdf"
        json_path.write_text(json.dumps(as_json))
        pdf_path.write_bytes(pdf_bytes)
