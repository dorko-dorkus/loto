from pathlib import Path

import pandas as pd
import pytest

from loto.pricing.providers import CsvProvider, Em6Provider, StaticCurveProvider


def _write_sample(path):
    idx = pd.date_range("2024-01-01", periods=3, freq="15min", tz="UTC")
    df = pd.DataFrame({"ts": idx, "price": [1.0, 2.0, 3.0]})
    df.to_csv(path, index=False)


def test_csv_provider(tmp_path):
    path = tmp_path / "curve.csv"
    _write_sample(path)

    provider = CsvProvider(path)
    series = provider.load()

    assert series.index.tz.zone == "Pacific/Auckland"
    assert (series.index[1] - series.index[0]).seconds == 300
    # first three buckets all carry initial value due to ffill
    assert series.iloc[0] == series.iloc[1] == series.iloc[2]


def test_static_curve_provider():
    idx = pd.date_range("2024-01-01", periods=2, freq="15min", tz="UTC")
    curve = pd.Series([10.0, 20.0], index=idx)

    provider = StaticCurveProvider(curve)
    series = provider.load()

    assert series.index.tz.zone == "Pacific/Auckland"
    assert (series.index[1] - series.index[0]).seconds == 300


def test_em6_provider_cache(monkeypatch, tmp_path):
    path = tmp_path / "A.csv"
    _write_sample(path)

    provider = Em6Provider(region="A", cache_dir=tmp_path)

    calls: list[str] = []
    original = pd.read_csv

    def spy(p, *args, **kwargs):
        calls.append(Path(p).name)
        return original(p, *args, **kwargs)

    monkeypatch.setattr(pd, "read_csv", spy)

    s1 = provider.load()
    s2 = provider.load()

    assert s1.equals(s2)
    # only one read
    assert calls == ["A.csv"]


def test_bad_input_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        CsvProvider(tmp_path / "missing.csv").load()

    with pytest.raises(ValueError):
        Em6Provider(region="A", node="B")

    with pytest.raises(ValueError):
        StaticCurveProvider([1, 2, 3]).load()
