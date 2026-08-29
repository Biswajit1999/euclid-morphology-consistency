# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-08-29

Fixes for issues raised by an external review (Codex); no repository
rename (kept as a separate, later decision).

### Fixed

- **Non-representative sample**: `load_morphology_sample` used a single
  unordered, spatially-unconstrained `SELECT TOP {n}`, which empirically
  drew almost the entire sample from one deep field (3/36 position bins
  usable). Now queries each of the three real deep fields
  (`docs/DATA_SOURCES.md`) separately with an explicit cone-search
  constraint, splitting the sample proportionally by each field's real
  sky area.
- **Overstated "no bias" claim**: `filter_consistency` reported only the
  median VIS-NIR difference as a point estimate, and README prose
  concluded "no population-level bias" from it alone. Now also reports a
  95% bootstrap confidence interval and a Wilcoxon signed-rank test; the
  bias is in fact statistically significant but ~460x smaller than the
  per-object scatter (see Results below and `docs/CLAIMS.md`).
  Live-verified against the real 20,000-object sample.
- **Position-dependent-residuals binning artifact** (found while
  regenerating real results for this release, not in the original
  review): `position_dependent_residuals` binned ra/dec over the
  *combined* range of all three deep fields, which -- since the fields
  are disjoint patches tens of degrees apart -- collapsed the check to
  one bin per field (3/36 populated). Fixed to bin within each field's
  own footprint (19/108 populated on the real sample).
- **Unused `matplotlib` dependency with a stale, non-reproducible
  committed figure**: added `scripts/make_figures.py`, which regenerates
  `results/figures/*.png` from the committed `results/default/` CSVs and
  JSON (not from any uncommitted per-object cache).
- Real excerpt fixture and its "is this really in the Q1 deep field
  range" regression test corrected two errors: the test used independent
  RA/Dec box bounds instead of the actual cone-search angular separation,
  and an existing code comment mislabeled the fixture's field as Fornax
  when it is actually EDF-South (verified by direct distance calculation
  against real field coordinates).
- VOTable/CSV row-order determinism: a server-side `ORDER BY object_id`
  was tried and measured to be ~30x slower against the live service
  (~235s vs ~8s for one field's `TOP 70`); row order is instead made
  deterministic client-side after fetching (`docs/LIMITATIONS.md`).

### Changed

- Title: "Euclid Q1 Morphology Consistency Audit" -> "Euclid Q1
  Morphology Measurement Comparison" (the original title implied a
  formal audit; this project compares official-pipeline outputs, it does
  not audit them against ground truth).

### Results

Regenerated live against the real, now correctly-stratified 20,000-object
sample (`results/default/summary.json`):

- VIS-NIR Sersic index: median diff -0.00158, 95% CI [-0.00317, -0.00078]
  (excludes zero), Wilcoxon p=2.9e-13, Pearson r=0.198.
- Sersic index vs. CAS concentration: Spearman r=0.428, p~0.
- Quality flags: 1.55% of fits have reduced chi2 > 2; 0% negative
  concentration.
- Position-dependent residuals: 19 of up to 108 per-field bins have >=20
  objects (up from 3/36 under the old combined-range binning).
- Disk+bulge fit: still 0/29,953,430 rows populated (unchanged, live
  re-verified via the new `audit-schema` CLI command).

## [0.1.0] - 2026-08-28

### Added

- Live adapter for the real Euclid Q1 MER morphology + catalogue tables
  via IRSA TAP (`src/euclidmorph/data.py`).
- Cross-filter (VIS vs. NIR) and cross-method (Sersic index vs. CAS
  concentration) consistency analysis, plus position-dependent residual
  binning and quality-flag summaries (`src/euclidmorph/analysis.py`).
- CLI (`euclidmorph run`) and 9 fast tests + 1 live-network test.

### Results

- 20,000 real, quality-flagged Q1 objects: VIS-NIR Sersic index shows no
  population-level bias but weak per-object correlation (Pearson r=0.20).
- Sersic index vs. CAS concentration: moderate positive correlation
  (Spearman r=0.41).
- Real, catalog-wide finding: the disk+bulge two-component Sersic fit is
  unpopulated (NULL) for all 29,953,430 rows in the full Q1 morphology
  table -- confirmed via a live COUNT query, not a bug in this project's
  code. This changed the project's cross-method comparison design
  mid-development (see `docs/DATA_SOURCES.md`, `docs/VALIDATION.md`).
- Default sample is spatially concentrated (3/36 usable position bins),
  limiting the position-dependence analysis in this version
  (`docs/LIMITATIONS.md`).
