# Limitations and Known Failure Modes

## Position bins remain narrow within each field

`load_morphology_sample` now queries each of the three real deep fields
separately (an earlier version's single unordered `TOP N` query drew
almost the entire sample from one field -- superseded, see
`docs/CLAIMS.md`), and `position_dependent_residuals` bins within each
field's own footprint. This resolves the *cross-field* representativeness
problem, but each field's cone-search radius (2.2-3.2 deg,
`src/euclidmorph/data.py`) is itself narrow, so the 19 populated bins in
the default run are still a modest sample of each field's true sky
extent, not a fine-grained systematics map. A few of the smallest bins
(n~20-30) show a larger median residual than the population as a whole;
this project has not determined whether that reflects a real localized
effect or ordinary small-sample scatter (`docs/METHODS.md`) -- treat
individual small bins with caution, and prefer the population-level
result for any decision that matters.

## Server-side ORDER BY was found to be prohibitively slow

An `ORDER BY object_id` was tried in the live ADQL query, specifically to
make row *order* (not just row *selection*) deterministic. Measured
directly against the live IRSA TAP service, adding it made a single-field
`TOP 70` query take ~235s versus ~8s without it -- the service apparently
must fully evaluate and sort the entire joined-and-filtered candidate set
before it can apply `TOP N` when sorting is requested, rather than
stopping early once N matches are found. That is too slow to run
synchronously (and it multiplies across 3 deep-field queries per fetch).
The unordered query was checked directly and returned the identical row
set and order across two repeated live fetches, so this static, frozen Q1
release does not exhibit observable drift in practice -- but the
ADQL/TAP specification does not formally guarantee that absent an
explicit `ORDER BY`. Row order is instead made deterministic
client-side, by sorting on `object_id` after fetching
(`src/euclidmorph/data.py`).

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
(Spearman r=0.428) is the expected, physically sensible result; it should
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
