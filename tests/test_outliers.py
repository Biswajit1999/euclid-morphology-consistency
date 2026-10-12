import numpy as np
import pandas as pd

from euclidmorph.outliers import field_rates, robust_outlier_table, threshold_sensitivity


def fixture(n=100):
    return pd.DataFrame(
        {
            "sersic_sersic_vis_index": np.arange(n, dtype=float),
            "sersic_sersic_nir_index": np.zeros(n),
            "sersic_ext_reduced_chi2": np.linspace(1, 2, n),
            "sersic_sersic_vis_radius": np.ones(n),
            "sersic_sersic_nir_radius": np.ones(n),
            "sersic_sersic_vis_axis_ratio": np.full(n, 0.8),
            "sersic_sersic_nir_axis_ratio": np.full(n, 0.7),
            "deep_field": ["A"] * 50 + ["B"] * 50,
        }
    )


def test_quantile_tail_selects_largest_residual():
    work = robust_outlier_table(fixture(), quantile=0.99)
    assert work.is_outlier.sum() == 1
    assert work.loc[work.is_outlier, "absolute_residual"].iloc[0] == 99


def test_sensitivity_and_field_rates_conserve_rows():
    data = fixture()
    assert len(threshold_sensitivity(data)) == 4
    rates = field_rates(robust_outlier_table(data))
    assert rates.n.sum() == len(data)
