import pandas as pd
import pandas.testing as pdt

from loto.pricing.hedge import Hedge
from loto.pricing.model import PriceModel, normalize


def _series(values):
    idx = pd.date_range("2024-01-01", periods=len(values), freq="5min")
    return pd.Series(values, index=idx)


def test_sampler_and_hedge():
    low = _series([10, 10, 10])
    med = _series([20, 20, 20])
    high = _series([30, 30, 30])

    model = PriceModel(low=low, med=med, high=high)
    # Explicit scenario selection
    high_sample = model.sample(level="high")

    assert high_sample.index.tz.zone == "Pacific/Auckland"
    pdt.assert_series_equal(high_sample, model.high)

    hedge = _series([5, 5, 5])
    hedger = Hedge(hedge=hedge, alpha=0.25)
    blended = hedger.blend(high_sample)

    expected = 0.75 * model.high + 0.25 * normalize(hedge)
    pdt.assert_series_equal(blended, expected)
