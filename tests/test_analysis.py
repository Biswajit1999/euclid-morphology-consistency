import numpy as np
import pandas as pd
import pytest

from euclidmorph.analysis import (
    filter_consistency,
    method_correlation,
    position_dependent_residuals,
    quality_flag_summary,
)


def _synthetic_df(n=500, seed=0, nir_bias=0.0, nir_noise=0.1):
    """A synthetic DataFrame with known statistical structure, used to
    validate the analysis functions' math -- not presented as real data."""
    rng = np.random.default_rng(seed)
    vis_index = rng.uniform(0.5, 5.0, n)
    nir_index = vis_index + nir_bias + rng.normal(0, nir_noise, n)
    concentration = 0.5 * vis_index + rng.normal(0, 0.3, n)  # correlated but not identical
    return pd.DataFrame({
        "ra": rng.uniform(60, 70, n), "dec": rng.uniform(-49, -45, n),
        "sersic_sersic_vis_index": vis_index, "sersic_sersic_nir_index": nir_index,
        "sersic_ext_reduced_chi2": rng.uniform(0.05, 1.5, n),
        "concentration": concentration,
    })


def test_filter_consistency_detects_zero_bias_when_none_injected():
    df = _synthetic_df(nir_bias=0.0, seed=1)
    result = filter_consistency(df)
    assert abs(result["median_diff_vis_minus_nir"]) < 0.05
    assert result["pearson_r"] > 0.9


def test_filter_consistency_detects_injected_bias():
    df = _synthetic_df(nir_bias=0.5, seed=2)
    result = filter_consistency(df)
    assert result["median_diff_vis_minus_nir"] == pytest.approx(-0.5, abs=0.1)


def test_method_correlation_is_positive_for_correlated_synthetic_data():
    df = _synthetic_df(seed=3)
    result = method_correlation(df)
    assert result["spearman_r"] > 0.3
    assert result["spearman_p"] < 0.01


def test_position_dependent_residuals_respects_min_per_bin():
    df = _synthetic_df(n=200, seed=4)
    result = position_dependent_residuals(df, n_ra_bins=10, n_dec_bins=10, min_per_bin=5)
    assert (result["n"] >= 5).all()
    assert "median_resid" in result.columns


def test_position_dependent_residuals_empty_when_bins_too_fine():
    df = _synthetic_df(n=50, seed=5)
    result = position_dependent_residuals(df, n_ra_bins=20, n_dec_bins=20, min_per_bin=100)
    assert len(result) == 0


def test_quality_flag_summary_reports_expected_fields():
    df = _synthetic_df(seed=6)
    result = quality_flag_summary(df)
    assert result["n_rows"] == 500
    assert 0.0 <= result["frac_sersic_ext_chi2_above_2"] <= 1.0
