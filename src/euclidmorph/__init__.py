"""euclidmorph: cross-filter and cross-method consistency audit of real
Euclid Q1 galaxy morphology measurements.

Uses the official Euclid Q1 MER morphology catalog (queried live from the
IRSA TAP service, no authentication required) to compare measurements the
official pipeline already provides for the same real objects -- a
single-Sersic fit in the VIS and NIR bands, and the parametric Sersic
index against the independently computed non-parametric CAS concentration
statistic -- rather than reimplementing a shape-measurement algorithm from
scratch. (The catalog's two-component bulge+disk Sersic fit was found to
be entirely unpopulated in this Q1 release -- docs/DATA_SOURCES.md -- so
it is not part of this comparison.) This is a companion, non-duplicative
audit alongside this author's existing `euclid-star-shapes` (point-source
PSF/astrometry) and `euclid-spectra-quality` (NISP spectral-contamination)
repositories: this one focuses specifically on extended-source galaxy
morphology consistency across filters and methods, not PSF or
spectroscopy.
"""

__version__ = "0.3.0"
