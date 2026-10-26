"""Field-stratified inference for an already selected Euclid morphology tail.

All methods condition on the committed sample and its sample-defined outlier count;
no field is interpreted as an unbiased draw from the complete Euclid Q1 footprint.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact, norm


def _checked(fields: pd.DataFrame) -> pd.DataFrame:
    required = {"deep_field", "n", "n_outlier"}
    if not required.issubset(fields.columns):
        raise ValueError(f"missing columns: {sorted(required - set(fields.columns))}")
    out = fields.loc[:, ["deep_field", "n", "n_outlier"]].copy()
    if out.empty or out.deep_field.isna().any() or out.deep_field.duplicated().any():
        raise ValueError("field labels must be nonempty and unique")
    for col in ("n", "n_outlier"):
        values = pd.to_numeric(out[col], errors="coerce").to_numpy(dtype=float)
        if not np.all(np.isfinite(values)) or not np.all(values == np.floor(values)):
            raise ValueError(f"{col} must contain finite integers")
        out[col] = values.astype(int)
    if (out.n <= 0).any() or (out.n_outlier < 0).any() or (out.n_outlier > out.n).any():
        raise ValueError("require 0 <= n_outlier <= n and n > 0")
    if not 0 < out.n_outlier.sum() < out.n.sum():
        raise ValueError("conditional test requires both outliers and non-outliers")
    return out.reset_index(drop=True)


def wilson_field_intervals(fields: pd.DataFrame, confidence: float = 0.95) -> pd.DataFrame:
    """Wilson score intervals for observed sample-specific tail rates.

    Descriptive binomial intervals; selection and spatial clustering are *not* modeled.
    """
    if not 0 < confidence < 1:
        raise ValueError("confidence must lie strictly between zero and one")
    out = _checked(fields)
    z = norm.ppf(0.5 + confidence / 2)
    n = out.n.to_numpy(float)
    p = out.n_outlier.to_numpy(float) / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    out["rate"] = p
    out["wilson_low"] = np.where(p == 0, 0.0, np.maximum(0, centre - half))
    out["wilson_high"] = np.where(p == 1, 1.0, np.minimum(1, centre + half))
    return out


def conditional_field_heterogeneity(
    fields: pd.DataFrame, *, simulations: int = 20000, seed: int = 20261026
) -> dict[str, object]:
    """Conditional Monte Carlo field-allocation null, fixing total tail count.

    Multivariate hypergeometric draws randomly assign the observed tail labels
    across fixed field sizes; this is an *exchangeability* null, not an inference
    about the full survey. Monte Carlo p uses a +1 numerator/denominator correction.
    """
    f = _checked(fields)
    if len(f) < 2 or simulations < 100:
        raise ValueError("need >=2 fields and >=100 simulations")
    counts = f.n_outlier.to_numpy(int)
    sizes = f.n.to_numpy(int)
    total = int(counts.sum())
    expected = sizes * (total / sizes.sum())
    # Pearson two-column chi-square, with non-tail expectations included.
    table = np.column_stack([counts, sizes - counts])
    chi2, asymptotic_p, _, _ = chi2_contingency(table, correction=False)
    rng = np.random.default_rng(seed)
    sampled = rng.multivariate_hypergeometric(sizes, total, size=simulations)
    expected_non = sizes - expected
    simulated_stat = (((sampled - expected) ** 2 / expected)
                      + ((sampled - expected) ** 2 / expected_non)).sum(axis=1)
    exceed = int(np.count_nonzero(simulated_stat >= chi2 - 1e-12))
    return {
        "fields": f.deep_field.tolist(),
        "observed_outliers": counts.tolist(),
        "expected_outliers": expected.tolist(),
        "chi_square": float(chi2),
        "asymptotic_p": float(asymptotic_p),
        "conditional_mc_p": (exceed + 1) / (simulations + 1),
        "mc_exceedances": exceed,
        "mc_simulations": simulations,
        "mc_standard_error": float(np.sqrt((exceed + 1) / (simulations + 1)
                                           * (1 - (exceed + 1) / (simulations + 1))
                                           / (simulations + 1))),
        "seed": seed,
    }


def pairwise_field_contrasts(fields: pd.DataFrame) -> pd.DataFrame:
    """Two-sided Fisher tests with Benjamini-Hochberg adjustment across pairs."""
    f = _checked(fields)
    rows = []
    for a, b in combinations(f.itertuples(index=False), 2):
        odds, p = fisher_exact(
            [[a.n_outlier, a.n - a.n_outlier],
             [b.n_outlier, b.n - b.n_outlier]], alternative="two-sided"
        )
        rows.append({"field_a": a.deep_field, "field_b": b.deep_field,
                     "rate_difference_a_minus_b": a.n_outlier / a.n - b.n_outlier / b.n,
                     "odds_ratio_a_over_b": float(odds), "fisher_p": float(p)})
    if not rows:
        return pd.DataFrame(columns=["field_a", "field_b", "rate_difference_a_minus_b",
                                     "odds_ratio_a_over_b", "fisher_p", "bh_q"])
    out = pd.DataFrame(rows)
    pvals = out.fisher_p.to_numpy()
    order = np.argsort(pvals)
    ranks = np.arange(1, len(pvals) + 1)
    adjusted_sorted = np.minimum.accumulate((pvals[order] * len(pvals) / ranks)[::-1])[::-1]
    adjusted = np.empty(len(pvals))
    adjusted[order] = np.minimum(1, adjusted_sorted)
    out["bh_q"] = adjusted
    return out
