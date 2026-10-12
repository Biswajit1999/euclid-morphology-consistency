"""Robust diagnostics for real Euclid VIS--NIR Sersic disagreements."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def robust_outlier_table(df: pd.DataFrame, quantile: float = 0.99) -> pd.DataFrame:
    """Return the high absolute-residual tail using a sample-defined quantile."""
    work = df.copy()
    work["sersic_residual"] = work.sersic_sersic_vis_index - work.sersic_sersic_nir_index
    work["absolute_residual"] = work.sersic_residual.abs()
    threshold = float(work.absolute_residual.quantile(quantile))
    work["is_outlier"] = work.absolute_residual >= threshold
    work["outlier_quantile"] = quantile
    work["outlier_threshold"] = threshold
    return work


def outlier_summary(work: pd.DataFrame) -> dict:
    """Compare tail and central populations without treating either band as truth."""
    tail = work[work.is_outlier]
    core = work[~work.is_outlier]
    rho_chi2, p_chi2 = stats.spearmanr(work.absolute_residual, work.sersic_ext_reduced_chi2)
    rho_radius, p_radius = stats.spearmanr(
        work.absolute_residual,
        np.log10(np.sqrt(work.sersic_sersic_vis_radius * work.sersic_sersic_nir_radius)),
    )
    return {
        "n": len(work),
        "n_outlier": len(tail),
        "threshold_absolute_sersic_index": float(tail.outlier_threshold.iloc[0]),
        "median_chi2_outlier": float(tail.sersic_ext_reduced_chi2.median()),
        "median_chi2_core": float(core.sersic_ext_reduced_chi2.median()),
        "median_vis_radius_outlier": float(tail.sersic_sersic_vis_radius.median()),
        "median_vis_radius_core": float(core.sersic_sersic_vis_radius.median()),
        "spearman_abs_residual_vs_chi2": float(rho_chi2),
        "spearman_abs_residual_vs_chi2_p": float(p_chi2),
        "spearman_abs_residual_vs_log_radius": float(rho_radius),
        "spearman_abs_residual_vs_log_radius_p": float(p_radius),
    }


def threshold_sensitivity(df: pd.DataFrame, quantiles=(0.95, 0.975, 0.99, 0.995)) -> pd.DataFrame:
    """Measure how population conclusions change with the tail definition."""
    rows = []
    for quantile in quantiles:
        work = robust_outlier_table(df, quantile)
        tail = work[work.is_outlier]
        rows.append(
            {
                "quantile": quantile,
                "threshold_absolute_sersic_index": tail.outlier_threshold.iloc[0],
                "n_outlier": len(tail),
                "median_reduced_chi2": tail.sersic_ext_reduced_chi2.median(),
                "median_vis_radius": tail.sersic_sersic_vis_radius.median(),
                "median_axis_ratio_difference": (
                    tail.sersic_sersic_vis_axis_ratio - tail.sersic_sersic_nir_axis_ratio
                )
                .abs()
                .median(),
            }
        )
    return pd.DataFrame(rows)


def field_rates(work: pd.DataFrame) -> pd.DataFrame:
    """Report outlier prevalence by real Euclid deep field."""
    return (
        work.groupby("deep_field", observed=True)
        .agg(n=("is_outlier", "size"), n_outlier=("is_outlier", "sum"), rate=("is_outlier", "mean"))
        .reset_index()
    )
