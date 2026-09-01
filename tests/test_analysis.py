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


def test_filter_consistency_ci_and_wilcoxon_flag_injected_bias():
    """Regression test for the 'no population-level bias' overclaim: a
    real injected bias should give a bootstrap CI that excludes zero and
    a significant (small-p) Wilcoxon signed-rank test, not just a
    point-estimate median near the injected value."""
    df = _synthetic_df(nir_bias=0.5, n=500, seed=2)
    result = filter_consistency(df)
    assert result["median_diff_ci95_low"] < result["median_diff_ci95_high"]
    assert result["median_diff_ci95_high"] < 0  # CI excludes zero (true diff is -0.5)
    assert result["wilcoxon_pvalue"] < 0.01


def test_filter_consistency_ci_includes_zero_when_no_bias_injected():
    df = _synthetic_df(nir_bias=0.0, n=500, seed=1)
    result = filter_consistency(df)
    assert result["median_diff_ci95_low"] < 0 < result["median_diff_ci95_high"]


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


def test_position_dependent_residuals_bins_within_each_field_separately():
    """Regression test: an earlier version binned ra/dec over the full
    combined range of all rows, so with real, widely-separated deep
    fields nearly every bin fell in the empty sky between fields and
    each field collapsed into a single bin -- checked directly against
    the real 20,000-row sample, which produced exactly 3 populated bins
    out of 36, one per field. Two synthetic fields, tens of degrees
    apart, each with real sub-field spatial spread, should each
    contribute multiple populated bins, not one bin apiece."""
    a = _synthetic_df(n=300, seed=10)
    a["ra"] = np.random.default_rng(10).uniform(60.0, 64.0, len(a))
    a["dec"] = np.random.default_rng(11).uniform(-48.0, -46.0, len(a))
    a["deep_field"] = "Field-A"

    b = _synthetic_df(n=300, seed=20)
    b["ra"] = np.random.default_rng(20).uniform(265.0, 269.0, len(b))
    b["dec"] = np.random.default_rng(21).uniform(65.0, 67.0, len(b))
    b["deep_field"] = "Field-B"

    df = pd.concat([a, b], ignore_index=True)
    result = position_dependent_residuals(df, n_ra_bins=4, n_dec_bins=4, min_per_bin=5)

    assert set(result["deep_field"].unique()) == {"Field-A", "Field-B"}
    assert (result[result["deep_field"] == "Field-A"].shape[0]) > 1
    assert (result[result["deep_field"] == "Field-B"].shape[0]) > 1


def test_quality_flag_summary_reports_expected_fields():
    df = _synthetic_df(seed=6)
    result = quality_flag_summary(df)
    assert result["n_rows"] == 500
    assert 0.0 <= result["frac_sersic_ext_chi2_above_2"] <= 1.0


def test_pairwise_analyses_drop_missing_values_and_report_denominator():
    df = _synthetic_df(n=20, seed=7)
    df.loc[0, "sersic_sersic_nir_index"] = np.nan
    df.loc[1, "concentration"] = np.nan
    filter_result = filter_consistency(df)
    method_result = method_correlation(df)
    assert filter_result["n_input"] == 20
    assert filter_result["n_dropped_missing"] == 1
    assert method_result["n_dropped_missing"] == 1
