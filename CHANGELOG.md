# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/).

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
