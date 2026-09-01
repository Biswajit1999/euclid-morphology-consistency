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
(`results/default/summary.json`): the median VIS-NIR difference is
-0.00129, with a 95% bootstrap CI of [-0.00261, -0.00060] (2000
resamples, seeded) that excludes zero, and a Wilcoxon signed-rank test
against zero gives p=4.9e-14. So H0's "unbiased" part is, strictly,
**rejected** at the population level -- but the effect size is tiny: the
median difference is about 552x smaller than the per-object scatter
(MAD=0.713). H0's "tightly correlated" part also does not hold (Pearson
r=0.209): individual VIS and NIR Sersic-index measurements for the same
galaxy often disagree substantially, even though the *typical* direction
of disagreement is close to (but not exactly) zero. An earlier version of
this project reported only the median-diff point estimate and concluded
"no population-level bias" -- an external review (Codex) flagged that as
stronger than a point estimate alone supports; the CI and significance
test above let a reader judge "statistically real but practically tiny"
for themselves.

## Cross-method comparison

The parametric single-Sersic index (VIS) is compared against the
independently computed non-parametric CAS concentration statistic for the
same objects (Spearman r=0.424, p~0) -- a moderate, statistically
significant positive correlation, consistent with both statistics
capturing related (but not identical) information about light
concentration. This is reported as a correlation-and-residual-structure
result, not an agreement-to-tolerance result, because the two statistics
are not expected to be numerically equal (`docs/LIMITATIONS.md`).

## Position-dependent residuals

`position_dependent_residuals` bins the VIS-NIR index residual by sky
position, **within each deep field's own footprint separately**. An
earlier version binned ra/dec over the full combined range of all three
deep fields at once; since the fields are disjoint patches separated by
tens of degrees (not a continuous survey), that made nearly every one of
the requested bins fall in the empty sky between fields, collapsing the
check to one bin per field (checked directly: 3 of 36 bins populated on
the real sample). Binning per-field instead gives real sub-field spatial
resolution: on the default 20,000-object sample, 19 bins (of up to 108,
i.e. 3 fields x 36 cells) have >=20 objects. Most bins show a small
median residual consistent with the overall population-level result
above; a couple of the smallest bins (n~20-30) show a larger median
residual, plausibly ordinary small-sample scatter given ~19-object MAD of
order 1 -- see `results/figures/position_residuals_by_field.png` and
`docs/LIMITATIONS.md`.

## Quality-flag reporting

`quality_flag_summary` reports the fraction of fits with a high
(>2) reduced chi-squared (1.55% in the default run) and any
concentration values <0 (0% -- clean).

## What this project does not do

- Does not measure morphology itself; it audits consistency between
  measurements the official Euclid pipeline already produced.
- Does not compare against the disk+bulge two-component fit (unpopulated
  in this Q1 release -- `docs/DATA_SOURCES.md`).
- Does not investigate why the smallest position bins show a larger
  residual than the population median (`docs/LIMITATIONS.md`).
