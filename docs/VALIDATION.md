# Validation

| Check | Method | Test | Result (2026-08-28) |
|---|---|---|---|
| Real excerpt parses with expected columns and reflects the flags=0 filter | Real, verbatim excerpt fixture | `tests/test_data.py` | Pass |
| Live IRSA TAP fetch returns populated concentration and flags=0 rows | Live network query | `tests/test_data.py::test_live_fetch_returns_populated_concentration_column` | Pass |
| filter_consistency detects zero bias on unbiased synthetic data | Synthetic construction with known truth | `tests/test_analysis.py::test_filter_consistency_detects_zero_bias_when_none_injected` | Pass |
| filter_consistency detects an injected 0.5 bias | Synthetic construction with known truth | `tests/test_analysis.py::test_filter_consistency_detects_injected_bias` | Recovered bias within 0.1 |
| method_correlation detects a positive correlation on correlated synthetic data | Synthetic construction with known truth | `tests/test_analysis.py::test_method_correlation_is_positive_for_correlated_synthetic_data` | Spearman r > 0.3, p < 0.01 |
| position_dependent_residuals respects the min-per-bin filter | Direct check | `tests/test_analysis.py::test_position_dependent_residuals_respects_min_per_bin` | Pass |
| Real, full-catalog COUNT confirms the disk+bulge fit is unpopulated | Live network COUNT query, no WHERE-clause selection bias | Manual query, 2026-08-28 (see `docs/DATA_SOURCES.md`) | 0/29,953,430 rows populated |

## Real result caught and acted on, not worked around

Discovering the disk+bulge fit's complete non-population (above) changed
this project's cross-method comparison design mid-development -- the
original plan (single-Sersic vs. disk+bulge) was abandoned in favor of
single-Sersic vs. CAS concentration once the live data showed the planned
comparison was not possible. This is recorded here and in
`docs/DATA_SOURCES.md` rather than silently substituted.

## Reproducing these checks

```bash
pytest -q                 # 9 tests, fixture-based, no network, < 3 s
pytest -q -m network        # + 1 live IRSA TAP fetch
```

## Explicitly not yet validated

- No cross-check of the Pearson/Spearman correlation computations against
  an independently implemented statistics library (scipy is used
  directly and trusted here, unlike the custom-implemented statistics
  elsewhere in this programme).
- No spatially stratified re-run to properly resolve the position-
  dependence question (`docs/LIMITATIONS.md`).
