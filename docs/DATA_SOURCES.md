# Data Sources

## Euclid Quick Release 1 (Q1)

- **Provider**: Euclid Consortium / ESA, mirrored at NASA/IPAC IRSA.
- **Released**: 2025-03-19 (found via web search 2026-08-28; Caltech/IRSA
  and Euclid Consortium pages).
- **Coverage**: 63.1 deg^2 across the Euclid Deep Fields (North, Fornax,
  South); ~26 million detections overall.
- **Access used by this project**: IRSA TAP service,
  `https://irsa.ipac.caltech.edu/TAP`, no authentication required.
  Tables used: `euclid_q1_mer_morphology` (per-object Sersic fits and
  CAS-style non-parametric statistics; confirmed 29,953,430 rows via a
  live `COUNT(*)` query, 2026-08-28) and `euclid_q1_mer_catalogue`
  (per-object positions), joined on `object_id`.
- **Licence**: Euclid Q1 data are public; IRSA distributes them under its
  standard open-data terms. This project queries live rather than
  redistributing the catalog; a small, real, verbatim excerpt is embedded
  as an offline test fixture (`tests/test_data.py`), consistent with fair
  use of a small sample for software testing.

## Known Q1-release caveat found during this project (not silently worked around)

The catalog schema defines a two-component bulge+disk Sersic fit
(`disk_sersic_*` columns in `euclid_q1_mer_morphology`). A live query
(2026-08-28) found `disk_sersic_disk_radius` is **NULL for all
29,953,430 rows** in the full Q1 morphology table -- i.e. this fit is
entirely unpopulated in the Q1 release, for every object, not just a
filtered subset. This project's original plan (comparing the single-
Sersic fit against the disk+bulge fit as two parametric methods) was
revised because of this finding; it now compares the single-Sersic fit
against the independently computed non-parametric CAS statistics
(concentration, asymmetry, smoothness, Gini) instead, which are populated
for ~22.3M of the 29.8M quality-flagged rows (~75%). See
`docs/METHODS.md`.

## Companion repositories (not duplicated here)

- `euclid-star-shapes`: point-source PSF FWHM/ellipticity and
  Gaia-relative astrometry audit on real Euclid Q1 VIS cutouts.
- `euclid-spectra-quality`: NISP spectral-contamination-flag reliability
  audit on a real Euclid Q1 grism tile.

This project covers the distinct, non-overlapping question of
extended-source galaxy morphology consistency across filters and
measurement methods.
