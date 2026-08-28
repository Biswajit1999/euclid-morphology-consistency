# Methods

## Research question

How consistent are Euclid Q1 galaxy morphology measurements across
filters and measurement methods, and where should users trust or distrust
them?

(Scoped from the programme's original "PSF and Morphology Auditor"
question: PSF consistency is already covered by this author's
`euclid-star-shapes` repository; this project covers the non-overlapping
extended-source morphology-consistency question -- see
`docs/DATA_SOURCES.md`.)

## Null hypothesis

H0: The VIS-band and NIR-band single-Sersic index measurements for the
same real object are numerically consistent (unbiased, tightly
correlated).

Tested on 20,000 real, quality-flagged Q1 objects
(`results/default/summary.json`): the population-level median difference
is consistent with zero (no systematic filter bias), but the per-object
correlation is weak (Pearson r=0.20) with substantial scatter (MAD=0.74).
H0's "unbiased" part holds; its "tightly correlated" part does not --
individual VIS and NIR Sersic-index measurements for the same galaxy
often disagree substantially even though there is no population-level
bias between them.

## Cross-method comparison

The parametric single-Sersic index (VIS) is compared against the
independently computed non-parametric CAS concentration statistic for the
same objects (Spearman r=0.41, p<<0.001) -- a moderate, statistically
significant positive correlation, consistent with both statistics
capturing related (but not identical) information about light
concentration. This is reported as a correlation-and-residual-structure
result, not an agreement-to-tolerance result, because the two statistics
are not expected to be numerically equal (`docs/LIMITATIONS.md`).

## Position-dependent residuals

`position_dependent_residuals` bins the VIS-NIR index residual by sky
position. In the default 20,000-object sample, only 3 of 36 requested
bins have >=20 objects -- the sample (drawn via an unordered SQL `TOP N`
query, not a spatially stratified one) is concentrated in a narrow sky
region rather than spread across the full Q1 footprint. This is reported
honestly as a sampling limitation (`docs/LIMITATIONS.md`), not glossed
over; the position-dependence question is only weakly addressed by this
v0.1's default sample.

## Quality-flag reporting

`quality_flag_summary` reports the fraction of fits with a high
(>2) reduced chi-squared (1.95% in the default run) and any
concentration values <0 (0% -- clean).

## What this project does not do

- Does not measure morphology itself; it audits consistency between
  measurements the official Euclid pipeline already produced.
- Does not compare against the disk+bulge two-component fit (unpopulated
  in this Q1 release -- `docs/DATA_SOURCES.md`).
- Does not yet resolve the position-dependence question with adequate
  sky coverage (`docs/LIMITATIONS.md`).
