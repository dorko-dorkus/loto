from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

# Timezone used for all price series
TZ = "Pacific/Auckland"
FREQ = "5min"  # five minute buckets


def _prepare_series(series: pd.Series) -> pd.Series:
    """Return series resampled to 5-minute buckets in the target timezone.

    The input index must be datetime-like. If the index lacks timezone
    information it is assumed to be naive and will be localized to the
    target timezone. Existing timezones are converted.
    """

    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError("Series index must be datetime like")

    idx = series.index
    if idx.tz is None:
        idx = idx.tz_localize(TZ)
    else:
        idx = idx.tz_convert(TZ)
    series.index = idx
    series = series.sort_index()

    # Forward fill within 5 minute resampling buckets
    series = series.resample(FREQ).ffill()
    return series


@dataclass
class CsvProvider:
    """Load and cache a price series from a CSV file.

    The CSV is expected to have at least two columns: timestamp and value. The
    first column is parsed as datetimes and the second as the price value. The
    loaded series is normalized to :data:`TZ` and resampled to five minute
    buckets. Results are cached after the first load and copies are returned on
    subsequent calls.
    """

    path: Path
    _cache: Optional[pd.Series] = None

    def load(self) -> pd.Series:
        """Return the cached price series.

        The CSV file is read only once. Subsequent calls return a copy of the
        cached, timezone-normalized and resampled series.
        """

        if self._cache is None:
            path = Path(self.path)
            if not path.exists():
                raise FileNotFoundError(f"CSV file not found: {path}")

            df = pd.read_csv(path)
            if df.shape[1] < 2:
                raise ValueError("CSV must have at least two columns")

            try:
                ts = pd.to_datetime(df.iloc[:, 0])
            except Exception as exc:  # pragma: no cover - defensive
                raise ValueError("Invalid timestamp column") from exc

            series = pd.Series(df.iloc[:, 1].values, index=ts)
            self._cache = _prepare_series(series)

        return self._cache.copy()


class Em6Provider:
    """Stubbed EM6 provider reading from a CSV cache on disk.

    Parameters
    ----------
    region, node:
        Exactly one of ``region`` or ``node`` must be provided to identify the
        dataset to load.
    cache_dir:
        Directory containing the CSV cache files. The provider reads from this
        directory once and caches the resulting series in memory.
    """

    _cache: dict[str, pd.Series] = {}

    def __init__(
        self,
        *,
        region: str | None = None,
        node: str | None = None,
        cache_dir: Path | str = Path("."),
    ) -> None:
        if (region is None and node is None) or (
            region is not None and node is not None
        ):
            raise ValueError("Provide exactly one of region or node")
        self.region = region
        self.node = node
        self.cache_dir = Path(cache_dir)

    def _cache_key(self) -> str:
        return f"region:{self.region}" if self.region else f"node:{self.node}"

    def load(self) -> pd.Series:
        """Return the cached price series for the configured region or node.

        The CSV file located in :attr:`cache_dir` is parsed, normalized to the
        target timezone and resampled to five minute buckets. Loaded data is
        cached in a class-level dictionary and copies are returned on each call.
        """

        key = self._cache_key()
        if key in self._cache:
            return self._cache[key].copy()

        filename = f"{self.region}.csv" if self.region else f"{self.node}.csv"
        path = self.cache_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Cached data not found for {key}: {path}")

        df = pd.read_csv(path)
        if df.shape[1] < 2:
            raise ValueError("CSV must have at least two columns")

        try:
            ts = pd.to_datetime(df.iloc[:, 0])
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError("Invalid timestamp column") from exc

        series = pd.Series(df.iloc[:, 1].values, index=ts)
        series = _prepare_series(series)
        self._cache[key] = series
        return series.copy()


@dataclass
class StaticCurveProvider:
    """Return a static curve provided as a pandas Series."""

    curve: pd.Series

    def load(self) -> pd.Series:
        if not isinstance(self.curve, pd.Series):
            raise ValueError("curve must be a pandas Series")
        return _prepare_series(self.curve.copy())
