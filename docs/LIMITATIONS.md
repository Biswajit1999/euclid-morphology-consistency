# Limitations and Known Failure Modes

## Sample is spatially concentrated, not stratified

`load_morphology_sample` uses an unordered ADQL `TOP N` query, which
returns whatever rows the database happens to return first -- in practice
a narrow sky region, not a representative sample of the full Q1 footprint
(63.1 deg^2 across three deep fields). The default 20,000-object run
yields only 3 usable position-bins (`docs/METHODS.md`), which means the
"position-dependent" half of the research question is only weakly
addressed by this version. A spatially stratified or random sample (e.g.
ORDER BY a hash of object_id, or explicit per-field queries) is a real,
tractable fix, tracked as a repository issue.

## Disk+bulge fit is unpopulated in this Q1 release

As documented in `docs/DATA_SOURCES.md`, the catalog's two-component
bulge+disk Sersic fit is NULL for every one of the 29,953,430 rows in the
full Q1 morphology table. This is a genuine, catalog-wide finding, not a
bug in this project's query -- confirmed via a plain `COUNT(*)` /
`COUNT(disk_sersic_disk_radius)` comparison with no WHERE-clause
selection. This project's cross-method comparison uses the non-parametric
CAS statistics instead.

## Cross-method comparison is correlation, not agreement

The Sersic index and CAS concentration are different measurement
approaches to related but distinct physical quantities (profile shape vs.
light-curve-of-growth concentration). A moderate correlation
(Spearman r=0.41) is the expected, physically sensible result; it should
not be read as either statistic being "wrong" or the two being
interchangeable.

## Only VIS-vs-NIR filter pair tested

The catalog provides VIS and NIR (via NISP Y/J/H stacked) Sersic fits;
this project compares VIS against a single combined NIR fit, not the
individual NISP bands separately.

## No independent re-measurement

This project audits consistency *between* official-pipeline outputs; it
does not independently re-measure any galaxy's morphology from the raw
imaging, so it cannot determine which of two disagreeing measurements (if
either) is closer to the truth -- only that they disagree, and by how
much.

## Known pipeline-version caveat

Per the programme's requirement to flag pipeline-version caveats
explicitly: this project analyzes the **Q1** (Quick Release 1) processing
only. Later Euclid data releases (e.g. DR1) may use different pipeline
versions with different morphology-fitting behavior; no claim here
extends to any release beyond Q1.
