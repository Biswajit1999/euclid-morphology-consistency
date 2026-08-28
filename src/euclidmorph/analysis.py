"""Cross-filter and cross-method morphology consistency analysis on real
Euclid Q1 MER catalog measurements.

Two independent-measurement comparisons are made on the *same* real
objects, both computed by the official Euclid pipeline (not by this
project):

1. **Cross-filter**: single-Sersic index fit independently in the VIS and
   NIR bands (``sersic_sersic_vis_index`` vs ``sersic_sersic_nir_index``).
2. **Cross-method**: the parametric single-Sersic index (profile-shape
   fit) vs. the non-parametric CAS concentration statistic
   (``concentration``) -- two different measurement approaches to
   morphological concentration. These are not expected to be numerically
   identical (they quantify related but distinct things -- Sersic index
   parametrizes the light-profile shape; C quantifies light concentration
   between two curve-of-growth apertures) so this reports their
   *correlation and residual structure*, not agreement to a tolerance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def filter_consistency(df: pd.DataFrame) -> dict:
    vis = df["sersic_sersic_vis_index"].to_numpy()
    nir = df["sersic_sersic_nir_index"].to_numpy()
    diff = vis - nir
    r, p = stats.pearsonr(vis, nir)
    return {
        "n": len(df), "pearson_r": float(r), "pearson_p": float(p),
        "median_diff_vis_minus_nir": float(np.median(diff)),
        "mad_diff": float(stats.median_abs_deviation(diff)),
    }


def method_correlation(df: pd.DataFrame) -> dict:
    sersic_n = df["sersic_sersic_vis_index"].to_numpy()
    conc = df["concentration"].to_numpy()
    r, p = stats.spearmanr(sersic_n, conc)  # Spearman: monotonic, not linear, relationship expected
    return {"n": len(df), "spearman_r": float(r), "spearman_p": float(p)}


def position_dependent_residuals(
    df: pd.DataFrame, n_ra_bins: int = 6, n_dec_bins: int = 6, min_per_bin: int = 20
) -> pd.DataFrame:
    """Bin the VIS-NIR Sersic-index residual by sky position and report
    the median residual and count per bin -- a direct check for
    position-dependent systematics."""
    work = df.copy()
    work["resid"] = work["sersic_sersic_vis_index"] - work["sersic_sersic_nir_index"]
    work["ra_bin"] = pd.cut(work["ra"], bins=n_ra_bins)
    work["dec_bin"] = pd.cut(work["dec"], bins=n_dec_bins)

    grouped = work.groupby(["ra_bin", "dec_bin"], observed=True).agg(
        n=("resid", "size"), median_resid=("resid", "median"), std_resid=("resid", "std"),
    ).reset_index()
    return grouped[grouped["n"] >= min_per_bin]


def quality_flag_summary(df: pd.DataFrame) -> dict:
    return {
        "n_rows": len(df),
        "frac_sersic_ext_chi2_above_2": float((df["sersic_ext_reduced_chi2"] > 2.0).mean()),
        "frac_concentration_negative": float((df["concentration"] < 0).mean()),
    }
