# VIS--NIR Sersic outlier audit

This follow-up investigates the per-object disagreement tail in the committed, real 20,000-row Euclid Q1 MER morphology sample. It does not label either filter as ground truth.

The primary definition is the top 1% of absolute VIS-minus-NIR Sersic-index residuals. Sensitivity is reported at the 95th, 97.5th, 99th and 99.5th percentiles so no conclusion rests on one arbitrary cut. The audit compares reduced fit chi-square, radius, axis-ratio disagreement and deep-field prevalence, and reports rank correlations between disagreement amplitude and fit/size diagnostics.

In this sample the 99th-percentile threshold is $|\Delta n|=5.199$ (200 objects). Tail objects have smaller median VIS radius (0.0505 versus 0.288 in catalogue radius units) and higher median reduced chi-square (0.159 versus 0.0705), but the full-sample rank correlations of disagreement with chi-square and log radius are consistent with zero. This combination cautions against turning the tail comparison into a monotonic causal claim.

The tail is an algorithmic audit stratum, not a new galaxy class. The input sample is quality-flagged and area-stratified across the three deep fields, but it is not a random sample of the full Q1 release. Catalogue uncertainties for the compared Sersic indices are not available in this table, so residuals are not converted to per-object significance.

Run `python scripts/audit_outliers.py` after the standard cached sample has been acquired.
