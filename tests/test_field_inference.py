import numpy as np
import pandas as pd
import pytest

from euclidmorph.field_inference import (
    conditional_field_heterogeneity,
    pairwise_field_contrasts,
    wilson_field_intervals,
)


def fixture():
    return pd.DataFrame({"deep_field": ["A", "B", "C"],
                         "n": [100, 200, 300], "n_outlier": [0, 10, 20]})


def test_wilson_bounds_and_zero_count():
    result = wilson_field_intervals(fixture())
    assert result.loc[0, "wilson_low"] == 0
    assert result.loc[0, "wilson_high"] > 0
    assert (result.wilson_low <= result.rate).all()
    assert (result.rate <= result.wilson_high).all()


def test_wilson_confidence_width_monotonic():
    lo = wilson_field_intervals(fixture(), confidence=0.90)
    hi = wilson_field_intervals(fixture(), confidence=0.99)
    assert ((hi.wilson_high - hi.wilson_low) > (lo.wilson_high - lo.wilson_low)).all()


def test_conditional_expected_counts_and_reproducibility():
    a = conditional_field_heterogeneity(fixture(), simulations=2000, seed=42)
    b = conditional_field_heterogeneity(fixture(), simulations=2000, seed=42)
    assert a == b
    assert sum(a["expected_outliers"]) == pytest.approx(30)
    assert 0 < a["conditional_mc_p"] <= 1


def test_perfectly_balanced_counts_have_p_one():
    f = pd.DataFrame({"deep_field": ["A", "B"], "n": [100, 100],
                      "n_outlier": [10, 10]})
    result = conditional_field_heterogeneity(f, simulations=1000)
    assert result["chi_square"] == pytest.approx(0)
    assert result["conditional_mc_p"] == 1


def test_pairwise_bh_correction():
    result = pairwise_field_contrasts(fixture())
    assert len(result) == 3
    assert np.all(result.bh_q >= result.fisher_p)
    assert np.all((result.bh_q >= 0) & (result.bh_q <= 1))


@pytest.mark.parametrize("mutate", [
    lambda d: d.assign(n=[0, 200, 300]),
    lambda d: d.assign(n_outlier=[101, 10, 20]),
    lambda d: d.assign(deep_field=["A", "A", "C"]),
    lambda d: d.assign(n_outlier=[0.5, 10, 20]),
])
def test_reject_bad_inputs(mutate):
    with pytest.raises(ValueError):
        wilson_field_intervals(mutate(fixture()))


def test_reject_invalid_confidence():
    with pytest.raises(ValueError):
        wilson_field_intervals(fixture(), confidence=1)
