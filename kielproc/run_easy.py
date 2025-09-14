"""Utilities for simplified Kiel processing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd


def run_easy(
    beta: float,
    r: float,
    q_s_mean: Optional[float],
    df_ts: Optional[pd.DataFrame] = None,
    per_port: Optional[pd.DataFrame] = None,
    data_csv: Optional[Path] = None,
    C_f: Optional[float] = None,
    piccolo_fit: Any = None,
    summary_path: Path | str = "summary.json",
) -> dict[str, Any]:
    """Run simplified processing and write a summary file.

    Parameters
    ----------
    beta: float
        The beta value.
    r: float
        Radius term.
    q_s_mean: Optional[float]
        Mean of the qs series.
    df_ts: Optional[pd.DataFrame]
        Timeseries data with column "VP_pa" representing qs values.
    per_port: Optional[pd.DataFrame]
        Alternative per-port dataframe with column "q_s_pa".
    data_csv: Optional[Path]
        CSV file containing overlay delta pressure data.
    C_f: Optional[float]
        Friction coefficient.
    piccolo_fit: Any
        Optional piccolo fit data.
    summary_path: Path | str
        Where to write ``summary.json``.
    """

    # ---------------- Reconciliation (works with or without overlay) ----------------
    dp_geom_mbar = (
        float(((1.0 - beta**4) * (r**2) * q_s_mean) / 100.0)
        if (beta and r and (q_s_mean is not None) and np.isfinite(q_s_mean))
        else None
    )
    p5 = p50 = p95 = None
    C_f_star = None
    dp_corr_mbar = None
    # --- predicted band from qs series (if any) ---
    pred_band_geom = None
    try:
        # Prefer timeseries qs; fallback to per_port means if needed
        qs_series = None
        if df_ts is not None and "VP_pa" in df_ts.columns:
            qs_series = pd.to_numeric(df_ts["VP_pa"], errors="coerce").to_numpy()
        elif per_port is not None and "q_s_pa" in per_port.columns:
            qs_series = pd.to_numeric(per_port["q_s_pa"], errors="coerce").to_numpy()
        if qs_series is not None:
            qs_series = qs_series[np.isfinite(qs_series) & (qs_series > 0)]
            if qs_series.size:
                # DP_geom = (1-β^4) r^2 * qs / 100
                k = (1.0 - beta**4) * (r**2) / 100.0
                g5, g95 = np.percentile(k * qs_series, [5, 95])
                pred_band_geom = [float(g5), float(g95)]
    except Exception:
        pass
    reconcile = {
        "dp_overlay_p5_mbar": None,
        "dp_overlay_p50_mbar": None,
        "dp_overlay_p95_mbar": None,
        "dp_pred_geom_mbar": dp_geom_mbar,
        "dp_pred_corr_mbar": None,
        "dp_error_geom_mbar": None,
        "dp_error_corr_mbar": None,
        "dp_error_geom_pct_vs_p50": None,
        "dp_error_corr_pct_vs_p50": None,
        "C_f": C_f,
        "C_f_fit": None,
        "piccolo_fit": piccolo_fit,
        "pred_band_geom_mbar": pred_band_geom,
        "pred_band_corr_mbar": None,
    }

    if data_csv is not None and Path(data_csv).exists():
        df_overlay = pd.read_csv(data_csv)
        col = "data_DP_mbar" if "data_DP_mbar" in df_overlay.columns else None
        if col is not None:
            dp = pd.to_numeric(df_overlay[col], errors="coerce").dropna().to_numpy()
            if dp.size:
                p5, p50, p95 = np.percentile(dp, [5, 50, 95])
                reconcile["dp_overlay_p5_mbar"] = float(p5)
                reconcile["dp_overlay_p50_mbar"] = float(p50)
                reconcile["dp_overlay_p95_mbar"] = float(p95)
                if dp_geom_mbar is not None and p50 is not None and dp_geom_mbar > 0:
                    C_f_star = float(p50 / dp_geom_mbar)
                    dp_corr_mbar = C_f_star * dp_geom_mbar
                    reconcile["dp_pred_corr_mbar"] = float(dp_corr_mbar)
                    reconcile["C_f_fit"] = float(C_f_star)
                    reconcile["dp_error_corr_mbar"] = float(dp_corr_mbar - p50)
                    reconcile["dp_error_corr_pct_vs_p50"] = (
                        float(100.0 * (dp_corr_mbar - p50) / p50) if p50 else None
                    )
                # If we have a fitted C_f and a predicted geom band, also provide a reconciled band
                if C_f_star is not None and pred_band_geom:
                    reconcile["pred_band_corr_mbar"] = [
                        float(C_f_star * pred_band_geom[0]),
                        float(C_f_star * pred_band_geom[1]),
                    ]
        if dp_geom_mbar is not None:
            reconcile["dp_error_geom_mbar"] = float(
                dp_geom_mbar - (p50 if p50 is not None else dp_geom_mbar)
            )
            reconcile["dp_error_geom_pct_vs_p50"] = (
                float(100.0 * (dp_geom_mbar - p50) / p50) if p50 else None
            )

    summary = {"reconcile": reconcile}
    summary_path = Path(summary_path)
    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2)
    return summary


__all__ = ["run_easy"]
