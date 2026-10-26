# Field-stratified tail inference (2026-10-26)

This optional audit reuses **committed, real Euclid Q1-derived counts** in
`results/outlier-audit/field_rates.csv`; it does not retrieve, alter or invent
catalogue measurements. The 99th-percentile tail was selected *globally* from a
quality-filtered, spatially stratified 20,000-object sample, so its pooled 1%
prevalence is imposed by construction and is **not** a measured survey-wide
outlier fraction.

Three complementary diagnostics are computed:

1. **Wilson 95% field-rate intervals** summarize binomial sampling variation,
   but ignore within-field clustering and the original selection design.
2. **Conditional allocation test** fixes the observed 200 tail labels and the
   three field sizes. A multivariate hypergeometric Monte Carlo null tests
   exchangeability of tail membership across fields, reporting a finite-MC
   p-value and Monte Carlo standard error. It does not infer causality.
3. **Pairwise two-sided Fisher exact contrasts**, with Benjamini-Hochberg
   correction across the three comparisons, describe where any heterogeneity
   may lie. These tests share observations and are exploratory.

Run `python scripts/audit_field_inference.py` from the repository root after
`pip install -e '.[dev]'`. Outputs are CSV/JSON under `results/field-inference/`.
Use `--simulations` and `--seed` to reproduce the conditional null. No claims
about photometric blending, NIR detection limits or morphology failures are
supported without image cutouts, fit flags and source-level uncertainties.

The inference deliberately **does not close issue #5**: per-object physical
failure-mode validation and cutout inspection remain outstanding.

The optional `python scripts/plot_field_inference.py` renders a labelled
field-rate diagnostic plot; Matplotlib is already in this project's dependencies.
The CSV and JSON outputs under `results/field-inference/` were generated from
the repository's committed `field_rates.csv` using 20,000 seeded allocations.
