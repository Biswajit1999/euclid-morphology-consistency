"""Adapter for the real, official Euclid Q1 MER morphology and merged
catalogs, queried live from the IRSA TAP service
(https://irsa.ipac.caltech.edu/TAP), no authentication required.

Tables (confirmed live 2026-08-28 via TAP_SCHEMA.tables query):
  - ``euclid_q1_mer_morphology``: per-object single-Sersic fits (VIS and
    NIR bands) and non-parametric CAS-style statistics (concentration,
    asymmetry, smoothness, Gini), ~30 million rows total for the Q1
    release.
  - ``euclid_q1_mer_catalogue``: per-object positions (ra, dec) and
    photometry, joined here on ``object_id``.

Note: the catalog also defines a two-component bulge+disk Sersic fit
(``disk_sersic_*`` columns), which this project initially planned to use
as a second parametric model for cross-model comparison. A live COUNT
query (2026-08-28) found ``disk_sersic_disk_radius`` is NULL for all
29,953,430 rows in the full Q1 morphology table -- that fit is entirely
unpopulated in this release. This project therefore compares the
single-Sersic model against the independently computed non-parametric CAS
statistics instead (see docs/METHODS.md); the disk+bulge-fit finding
itself is recorded as a genuine Q1-release caveat in
docs/DATA_SOURCES.md, not silently worked around.

See docs/DATA_SOURCES.md for full provenance, release details, and
licence terms.
"""
from __future__ import annotations

import hashlib
import io
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

IRSA_TAP_SYNC = "https://irsa.ipac.caltech.edu/TAP/sync"

QUERY_TEMPLATE = """
SELECT TOP {n}
  m.object_id, c.ra, c.dec,
  m.sersic_sersic_vis_radius, m.sersic_sersic_vis_axis_ratio, m.sersic_sersic_vis_index,
  m.sersic_sersic_nir_radius, m.sersic_sersic_nir_axis_ratio, m.sersic_sersic_nir_index,
  m.sersic_ext_reduced_chi2, m.sersic_ext_flags,
  m.concentration, m.concentration_err, m.gini, m.asymmetry, m.smoothness
FROM euclid_q1_mer_morphology m
JOIN euclid_q1_mer_catalogue c ON m.object_id = c.object_id
WHERE m.sersic_ext_flags = 0 AND m.concentration IS NOT NULL
"""


@dataclass(frozen=True)
class CachePaths:
    cache_dir: Path

    @property
    def manifest(self) -> Path:
        return self.cache_dir / "manifest.json"


def load_morphology_sample(paths: CachePaths, n: int = 20000, force: bool = False) -> pd.DataFrame:
    """Fetch (or read cached) a real Euclid Q1 MER morphology sample."""
    cache_file = paths.cache_dir / f"morphology_sample_{n}.csv"
    if cache_file.exists() and not force:
        return pd.read_csv(cache_file)

    query = QUERY_TEMPLATE.format(n=n)
    url = IRSA_TAP_SYNC + "?" + urllib.parse.urlencode({"query": query, "format": "csv"})
    with urllib.request.urlopen(url, timeout=120) as resp:
        raw = resp.read()

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(raw)
    entry = {
        "url": IRSA_TAP_SYNC, "query": query.strip(), "sha256": hashlib.sha256(raw).hexdigest(),
        "n_bytes": len(raw), "accessed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    manifest = json.loads(paths.manifest.read_text()) if paths.manifest.exists() else {}
    manifest[cache_file.name] = entry
    paths.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True))

    return pd.read_csv(io.BytesIO(raw))
