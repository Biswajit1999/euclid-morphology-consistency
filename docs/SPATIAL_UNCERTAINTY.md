# Euclid Q1: field-aware residual uncertainty

Three complementary diagnostics for the **existing cached real Q1 sample** (`data/cache/morphology_sample_20000.csv`):

1. Report VIS−NIR Sérsic-index median/MAD separately for each deep field, and compare the pooled median with the **area-weighted mean of field medians**. The latter is **not** a survey-wide estimator: quality cuts, spatial coverage, and selection probabilities are not corrected.
2. Test *within-field* spatial autocorrelation using a row-standardized k-nearest-neighbor Moran's I. Right ascension wraps correctly at 0/360°, each field is centered separately, and permutations are restricted within fields. A low permutation p-value signals spatial structure, **not** a demonstrated instrumental origin.
3. Use a within-field spatial-tile bootstrap to obtain a sensitivity interval for the pooled median. Tiles rather than objects are resampled to preserve local dependence; inference remains conditional on the sampled footprint and arbitrary tile size. Vary `n_tiles` before interpreting interval width.

Reproduce: `python scripts/analyze_spatial_uncertainty.py --seed 20261013`; inspect `results/spatial-uncertainty/summary.json`, `field_medians.csv`, `moran_null.csv` and `moran_permutation.png`. Offline tests: `PYTHONPATH=src pytest -q tests/test_spatial_uncertainty.py`. No results are committed until run against the actual cached catalogue; synthetic tests are never described as Euclid observations.
