from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from pandas import Series as PriceSeries

from .providers import _prepare_series

__all__ = ["PriceSeries", "normalize", "PriceModel"]


def normalize(series: pd.Series) -> PriceSeries:
    """Normalise ``series`` to the canonical :class:`PriceSeries`.

    The series is resampled to five‑minute buckets and converted to the
    ``Pacific/Auckland`` timezone, matching the conventions used by the pricing
    providers.
    """

    if not isinstance(series, pd.Series):
        raise ValueError("series must be a pandas Series")
    return _prepare_series(series.copy())


@dataclass
class PriceModel:
    """Simple price model holding low/med/high scenarios.

    The model can return a specific scenario by name or randomly sample one of
    the scenarios using an optional random number generator.
    """

    low: PriceSeries
    med: PriceSeries
    high: PriceSeries

    def __post_init__(self) -> None:
        self.low = normalize(self.low)
        self.med = normalize(self.med)
        self.high = normalize(self.high)

    def sample(
        self,
        level: str | None = None,
        *,
        rng: Optional[np.random.Generator] = None,
    ) -> PriceSeries:
        """Return a scenario series.

        If ``level`` is provided it must be ``"low"``, ``"med"`` or ``"high"``.
        Otherwise a scenario is chosen at random using ``rng``.
        """

        mapping = {"low": self.low, "med": self.med, "high": self.high}
        if level is not None:
            key = level.lower()
            if key not in mapping:
                raise ValueError("level must be one of 'low', 'med', or 'high'")
            return mapping[key].copy()

        if rng is None:
            rng = np.random.default_rng()
        key = rng.choice(["low", "med", "high"])
        return mapping[key].copy()
