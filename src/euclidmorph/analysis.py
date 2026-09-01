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


def filter_consistency(df: pd.DataFrame, seed: int = 0) -> dict:
    """Cross-filter (VIS vs NIR Sersic index) consistency, with a
    bootstrap confidence interval and a signed-rank significance test on
    the median difference -- not just the point estimate. An earlier
    version of this function reported only the median diff, and README
    prose concluded "no population-level bias" from that point estimate
    alone with no uncertainty interval or significance test -- an
    external review (Codex) flagged this as stronger than the analysis
    supported. A statistically significant median difference from zero
    is still fully consistent with "no *practically meaningful* bias" if
    the effect size (median diff, CI width) is small relative to the
    measurement's own scatter (`mad_diff`) -- both are reported so a
    reader can judge that distinction themselves, not just a p-value.
    """
    complete = df.dropna(subset=["sersic_sersic_vis_index", "sersic_sersic_nir_index"])
    if len(complete) < 2:
        raise ValueError("at least two complete VIS/NIR Sersic-index pairs are required")
    vis = complete["sersic_sersic_vis_index"].to_numpy()
    nir = complete["sersic_sersic_nir_index"].to_numpy()
    diff = vis - nir
    r, p = stats.pearsonr(vis, nir)

    rng = np.random.default_rng(seed)
    boot = stats.bootstrap(
        (diff,), np.median, confidence_level=0.95, n_resamples=2000,
        random_state=rng, method="percentile",
    )
    wilcoxon_stat, wilcoxon_p = stats.wilcoxon(diff)

    return {
        "n_input": len(df), "n": len(complete), "n_dropped_missing": len(df) - len(complete),
        "pearson_r": float(r), "pearson_p": float(p),
        "median_diff_vis_minus_nir": float(np.median(diff)),
        "median_diff_ci95_low": float(boot.confidence_interval.low),
        "median_diff_ci95_high": float(boot.confidence_interval.high),
        "mad_diff": float(stats.median_abs_deviation(diff)),
        "wilcoxon_statistic": float(wilcoxon_stat),
        "wilcoxon_pvalue": float(wilcoxon_p),
    }


def method_correlation(df: pd.DataFrame) -> dict:
    complete = df.dropna(subset=["sersic_sersic_vis_index", "concentration"])
    if len(complete) < 2:
        raise ValueError("at least two complete Sersic/concentration pairs are required")
    sersic_n = complete["sersic_sersic_vis_index"].to_numpy()
    conc = complete["concentration"].to_numpy()
    r, p = stats.spearmanr(sersic_n, conc)  # Spearman: monotonic, not linear, relationship expected
    return {"n_input": len(df), "n": len(complete), "n_dropped_missing": len(df) - len(complete),
            "spearman_r": float(r), "spearman_p": float(p)}


def position_dependent_residuals(
    df: pd.DataFrame, n_ra_bins: int = 6, n_dec_bins: int = 6, min_per_bin: int = 20
) -> pd.DataFrame:
    """Bin the VIS-NIR Sersic-index residual by sky position and report
    the median residual and count per bin -- a direct check for
    position-dependent systematics.

    Bins are computed *within* each deep field separately when a
    ``deep_field`` column is present. An earlier version binned ra/dec
    over the full combined range of all rows at once; since Q1's real
    footprint is three disjoint deep fields separated by tens of degrees
    (not a continuous survey -- see data.py), that made nearly every one
    of the ``n_ra_bins x n_dec_bins`` grid cells fall in the empty sky
    between fields, and each field (which only spans a few degrees) fell
    entirely inside a single cell -- collapsing this from a check for
    *sub-field* spatial systematics down to, in effect, a per-field
    comparison. Checked directly against the real 20,000-row sample: the
    old binning produced exactly 3 populated bins out of 36, one per
    field. Binning within each field's own footprint restores real
    sub-field spatial resolution.
    """
    work = df.copy()
    work["resid"] = work["sersic_sersic_vis_index"] - work["sersic_sersic_nir_index"]

    group_col = "deep_field" if "deep_field" in work.columns else None
    groups = work.groupby(group_col, observed=True) if group_col else [(None, work)]

    parts = []
    for field_name, sub in groups:
        sub = sub.copy()
        sub["ra_bin"] = pd.cut(sub["ra"], bins=n_ra_bins)
        sub["dec_bin"] = pd.cut(sub["dec"], bins=n_dec_bins)
        grouped = sub.groupby(["ra_bin", "dec_bin"], observed=True).agg(
            n=("resid", "size"), median_resid=("resid", "median"), std_resid=("resid", "std"),
        ).reset_index()
        if group_col:
            grouped.insert(0, group_col, field_name)
        parts.append(grouped)

    combined = pd.concat(parts, ignore_index=True)
    return combined[combined["n"] >= min_per_bin].reset_index(drop=True)


def quality_flag_summary(df: pd.DataFrame) -> dict:
    return {
        "n_rows": len(df),
        "frac_sersic_ext_chi2_above_2": float((df["sersic_ext_reduced_chi2"] > 2.0).mean()),
        "frac_concentration_negative": float((df["concentration"] < 0).mean()),
    }
