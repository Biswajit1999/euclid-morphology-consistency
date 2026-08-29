# Validation

| Check | Method | Test | Result |
|---|---|---|---|
| Real excerpt parses with expected columns and reflects the flags=0 filter | Real, verbatim excerpt fixture | `tests/test_data.py` | Pass |
| Real excerpt's coordinates fall within the deep field they claim (angular separation, not a box bound) | Real, verbatim excerpt fixture | `tests/test_data.py::test_real_excerpt_ra_dec_are_in_the_q1_deep_field_range` | Pass |
| Live IRSA TAP fetch returns populated concentration and flags=0 rows | Live network query | `tests/test_data.py::test_live_fetch_returns_populated_concentration_column` | Pass, 2026-08-29 |
| Live fetch covers all three deep fields, not just one | Live network query | `tests/test_data.py::test_live_fetch_covers_multiple_deep_fields` | Pass, 2026-08-29: 3/3 fields |
| Disk-Sersic null audit is reproducible and writes a committed JSON | Live network COUNT query | `tests/test_data.py::test_disk_sersic_null_audit_is_reproducible_and_committed` | Pass, 2026-08-29 |
| filter_consistency detects zero bias on unbiased synthetic data | Synthetic construction with known truth | `tests/test_analysis.py::test_filter_consistency_detects_zero_bias_when_none_injected` | Pass |
| filter_consistency detects an injected 0.5 bias | Synthetic construction with known truth | `tests/test_analysis.py::test_filter_consistency_detects_injected_bias` | Recovered bias within 0.1 |
| filter_consistency's bootstrap CI and Wilcoxon test flag an injected bias | Synthetic construction with known truth | `tests/test_analysis.py::test_filter_consistency_ci_and_wilcoxon_flag_injected_bias` | CI excludes zero, p < 0.01 |
| filter_consistency's bootstrap CI includes zero when no bias is injected | Synthetic construction with known truth | `tests/test_analysis.py::test_filter_consistency_ci_includes_zero_when_no_bias_injected` | CI includes zero |
| method_correlation detects a positive correlation on correlated synthetic data | Synthetic construction with known truth | `tests/test_analysis.py::test_method_correlation_is_positive_for_correlated_synthetic_data` | Spearman r > 0.3, p < 0.01 |
| position_dependent_residuals respects the min-per-bin filter | Direct check | `tests/test_analysis.py::test_position_dependent_residuals_respects_min_per_bin` | Pass |
| position_dependent_residuals bins within each field separately, not the combined range | Synthetic two-field construction, tens of degrees apart | `tests/test_analysis.py::test_position_dependent_residuals_bins_within_each_field_separately` | Pass, both fields multiply-binned |
| Real, full-catalog COUNT confirms the disk+bulge fit is unpopulated | Live network COUNT query, no WHERE-clause selection bias | `audit-schema` CLI command, 2026-08-29 | 0/29,953,430 rows populated |

## Real results caught and acted on, not worked around

- Discovering the disk+bulge fit's complete non-population (above)
  changed this project's cross-method comparison design mid-development
  -- the original plan (single-Sersic vs. disk+bulge) was abandoned in
  favor of single-Sersic vs. CAS concentration once the live data showed
  the planned comparison was not possible. Recorded here and in
  `docs/DATA_SOURCES.md` rather than silently substituted.
- Adding a server-side `ORDER BY` to make row order deterministic was
  measured directly against the live service to be ~30x slower (~235s vs
  ~8s for one field's `TOP 70`), which is why row order is instead made
  deterministic client-side (`docs/LIMITATIONS.md`, `src/euclidmorph/data.py`).
- Running `position_dependent_residuals` on the real, correctly
  stratified 20,000-object sample surfaced that it was binning ra/dec
  over the combined range of all three (widely separated) deep fields at
  once, collapsing the check to one bin per field -- fixed to bin within
  each field's own footprint (`docs/METHODS.md`).

## Reproducing these checks

```bash
pytest -q                   # 12 tests, fixture- and synthetic-data-based, no network, < 3 s
pytest -q -m network        # + 3 live IRSA TAP checks
```

## Explicitly not yet validated

- No cross-check of the Pearson/Spearman correlation computations against
  an independently implemented statistics library (scipy is used
  directly and trusted here, unlike the custom-implemented statistics
  elsewhere in this programme).
- No investigation of why a couple of the smallest position bins
  (n~20-30) show a larger median residual than the population as a whole
  (`docs/LIMITATIONS.md`).
