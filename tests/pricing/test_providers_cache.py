from __future__ import annotations

import pandas as pd

from loto.pricing.providers import CsvProvider, Em6Provider


def _write_csv(path, idx, values) -> None:
    pd.DataFrame({"ts": idx, "price": values}).to_csv(path, index=False)


def test_csv_provider_caches_and_normalizes(tmp_path):
    path = tmp_path / "curve.csv"
    idx = pd.date_range("2024-01-01 00:00", periods=2, freq="10min")
    _write_csv(path, idx, [1.0, 2.0])

    provider = CsvProvider(path)
    s1 = provider.load()

    expected_idx = pd.date_range(idx[0], periods=3, freq="5min", tz="Pacific/Auckland")
    assert list(s1.index) == list(expected_idx)

    # modifying the returned series should not affect the cache
    s1.iloc[0] = 99.0

    # changing the underlying file should have no effect after caching
    _write_csv(path, idx, [5.0, 6.0])

    s2 = provider.load()
    assert list(s2.index) == list(expected_idx)
    assert s2.iloc[0] == 1.0


def test_em6_provider_caches_and_normalizes(tmp_path):
    Em6Provider._cache.clear()

    path = tmp_path / "A.csv"
    idx = pd.date_range("2024-01-01 00:00", periods=2, freq="10min", tz="UTC")
    _write_csv(path, idx, [1.0, 2.0])

    provider = Em6Provider(region="A", cache_dir=tmp_path)
    s1 = provider.load()

    start = idx[0].tz_convert("Pacific/Auckland")
    expected_idx = pd.date_range(start, periods=3, freq="5min", tz="Pacific/Auckland")
    assert list(s1.index) == list(expected_idx)

    # modify returned series and file; cached value should stay the same
    s1.iloc[-1] = 123.0
    _write_csv(path, idx, [7.0, 8.0])

    s2 = provider.load()
    assert list(s2.index) == list(expected_idx)
    assert s2.iloc[-1] == 2.0
