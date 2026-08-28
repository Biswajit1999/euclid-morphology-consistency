"""euclidmorph: cross-model and cross-filter consistency audit of real
Euclid Q1 galaxy morphology measurements.

Uses the official Euclid Q1 MER morphology catalog (queried live from the
IRSA TAP service, no authentication required) to compare two independently
fit models the official pipeline already provides for the same real
objects -- a single-Sersic fit (VIS and NIR bands) and a two-component
bulge+disk fit -- rather than reimplementing a shape-measurement algorithm
from scratch. This is a companion, non-duplicative audit alongside this
author's existing `euclid-star-shapes` (point-source PSF/astrometry) and
`euclid-spectra-quality` (NISP spectral-contamination) repositories: this
one focuses specifically on extended-source galaxy morphology consistency
across models and filters, not PSF or spectroscopy.
"""

__version__ = "0.1.0"
