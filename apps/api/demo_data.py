from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).with_name("demo_data")


class DemoDataSource:
    """Load demo data from JSON files on startup."""

    def __init__(self) -> None:
        self.work_orders: List[Dict[str, Any]] = self._load_list("workorders.json")
        self.assets: List[Dict[str, Any]] = self._load_list("assets.json")
        self.locations: List[Dict[str, Any]] = self._load_list("locations.json")
        self.inventory: List[Dict[str, Any]] = self._load_list("inventory.json")
        self.blueprints: Dict[str, Dict[str, Any]] = self._load_dict("blueprints.json")
        self._work_orders_by_id = {wo["id"]: wo for wo in self.work_orders}

    def _load_list(self, filename: str) -> List[Dict[str, Any]]:
        path = DATA_DIR / filename
        if path.exists():
            return json.loads(path.read_text())
        return []

    def _load_dict(self, filename: str) -> Dict[str, Dict[str, Any]]:
        path = DATA_DIR / filename
        if path.exists():
            return json.loads(path.read_text())
        return {}

    def list_work_orders(self) -> List[Dict[str, Any]]:
        return list(self._work_orders_by_id.values())

    def get_work_order(self, work_order_id: str) -> Dict[str, Any]:
        return self._work_orders_by_id[work_order_id]

    def get_blueprint(self, work_order_id: str) -> Dict[str, Any] | None:
        return self.blueprints.get(work_order_id)


demo_data = DemoDataSource()
