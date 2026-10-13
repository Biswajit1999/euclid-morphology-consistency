import numpy as np
import pandas as pd
import pytest

from euclidmorph.spatial_uncertainty import (
    field_median_diagnostics, moran_permutation, spatial_block_bootstrap,
)


def sample(seed=5, n=240):
    rng = np.random.default_rng(seed)
    field = np.repeat(["North", "South"], n // 2)
    x = np.r_[rng.uniform(359.6, 360, n // 4), rng.uniform(0, 0.4, n // 4),
              rng.uniform(40, 41, n // 2)]
    y = np.r_[rng.uniform(65, 66, n // 2), rng.uniform(-48, -47, n // 2)]
    residual = np.r_[np.full(n // 2, 0.2), np.full(n // 2, -0.4)] + rng.normal(0, 0.1, n)
    return pd.DataFrame({"deep_field": field, "ra": x, "dec": y,
                         "sersic_sersic_vis_index": 2 + residual,
                         "sersic_sersic_nir_index": np.full(n, 2.)})


def test_field_medians_and_area_weights_are_not_pooled_estimator():
    result = field_median_diagnostics(sample(), {"North": 20, "South": 10})
    assert result["n"] == 240
    assert len(result["fields"]) == 2
    expected = sum(f["median_residual"] * f["area_deg2"] for f in result["fields"]) / 30
    assert result["area_weighted_mean_field_medians"] == pytest.approx(expected)


def test_missing_field_area_rejected():
    with pytest.raises(ValueError):
        field_median_diagnostics(sample(), {"North": 20})


def test_ra_wrap_does_not_break_nearest_neighbor_graph():
    result = moran_permutation(sample(), k=4, permutations=99, seed=3)
    assert result["n_fields"] == 2
    assert np.isfinite(result["moran_i"])
    assert 0 < result["permutation_p_two_sided"] <= 1


def test_permutation_null_reproducible():
    one = moran_permutation(sample(), k=4, permutations=99, seed=11)
    two = moran_permutation(sample(), k=4, permutations=99, seed=11)
    np.testing.assert_array_equal(one["null_statistics"], two["null_statistics"])


def test_spatial_signal_detected_without_cross_field_edges():
    data = sample()
    # Introduce within-field gradient; field means alone must not drive I.
    data["sersic_sersic_vis_index"] += 0.8 * np.sin(np.deg2rad(data.ra) * 5)
    result = moran_permutation(data, k=6, permutations=199)
    assert result["moran_i"] > result["null_mean"]


def test_block_bootstrap_finite_and_reproducible():
    one = spatial_block_bootstrap(sample(), n_tiles=4, replicates=200, seed=1)
    two = spatial_block_bootstrap(sample(), n_tiles=4, replicates=200, seed=1)
    assert one == two
    assert one["ci95_low"] <= one["median"] <= one["ci95_high"]


def test_invalid_bootstrap_resolution_rejected():
    with pytest.raises(ValueError):
        spatial_block_bootstrap(sample(), n_tiles=1)


def test_moran_rejects_constant_within_field_residuals():
    data = sample()
    data.loc[data.deep_field == "North", "sersic_sersic_vis_index"] = 2.2
    data.loc[data.deep_field == "South", "sersic_sersic_vis_index"] = 1.6
    with pytest.raises(ValueError):
        moran_permutation(data, k=3, permutations=19)


def test_moran_requires_enough_rows_per_field():
    with pytest.raises(ValueError):
        moran_permutation(sample().iloc[:3], k=4, permutations=19)
