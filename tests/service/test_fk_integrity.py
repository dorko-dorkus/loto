from typing import cast

import pytest

from loto.integrations._errors import AdapterRequestError
from loto.integrations.maximo_adapter import MaximoAdapter
from loto.service.blueprints import validate_fk_integrity


class DummyAdapter:
    def __init__(self, *, assets=None, locations=None):
        self.assets = assets or set()
        self.locations = locations or set()
        self.base_url = "http://maximo"

    def get_asset(self, asset_id: str):
        if asset_id not in self.assets:
            raise AdapterRequestError(status_code=404, retry_after=None)
        return {"id": asset_id}

    def _get(self, path: str, params=None):  # pragma: no cover - params unused
        location_id = path.split("/")[-1]
        if location_id not in self.locations:
            raise AdapterRequestError(status_code=404, retry_after=None)
        return {"id": location_id}


def test_valid_ids() -> None:
    adapter = cast(MaximoAdapter, DummyAdapter(assets={"A1"}, locations={"L1"}))
    validate_fk_integrity("A1", "L1", adapter=adapter)


def test_invalid_asset() -> None:
    adapter = cast(MaximoAdapter, DummyAdapter(locations={"L1"}))
    with pytest.raises(ValueError, match="Unknown asset 'A1'"):
        validate_fk_integrity("A1", "L1", adapter=adapter)


def test_invalid_location() -> None:
    adapter = cast(MaximoAdapter, DummyAdapter(assets={"A1"}))
    with pytest.raises(ValueError, match="Unknown location 'L1'"):
        validate_fk_integrity("A1", "L1", adapter=adapter)
