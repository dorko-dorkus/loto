from __future__ import annotations

from dataclasses import dataclass

from .model import PriceSeries, normalize


@dataclass
class Hedge:
    """Blend market prices with a hedging curve via an exposure ``alpha``."""

    hedge: PriceSeries
    alpha: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")
        self.hedge = normalize(self.hedge)

    def blend(self, prices: PriceSeries) -> PriceSeries:
        """Return a series of hedged prices."""

        prices = normalize(prices)
        if not prices.index.equals(self.hedge.index):
            prices, hedge = prices.align(self.hedge, join="outer")
            prices = prices.ffill()
            hedge = hedge.ffill()
        else:
            hedge = self.hedge
        return (1.0 - self.alpha) * prices + self.alpha * hedge
