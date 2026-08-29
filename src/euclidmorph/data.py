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

Sampling: Q1's real footprint is three disconnected deep fields (EDF
North, Fornax, South -- docs/DATA_SOURCES.md), not a continuous survey.
An earlier version of this module used a single unordered
``SELECT TOP {n}`` with no spatial constraint, which, empirically, drew
almost the entire sample from one field -- an external review (Codex)
found the committed sample occupied only 3 of 36 requested spatial bins.
Fixed: ``load_morphology_sample`` now queries each of the three known
deep fields separately with an explicit cone-search constraint,
splitting the requested sample size proportionally to each field's real
sky area, and concatenates the three real sub-samples.

Row order: an ``ORDER BY m.object_id`` was tried first (to make row
*order* deterministic, not just row *selection*), but measured directly
against the live service it made a ``TOP 70`` single-field query take
~235s versus ~8s without it -- IRSA's TAP engine has to fully evaluate
and sort every joined-and-filtered candidate before it can apply
``TOP N`` when an ``ORDER BY`` is present, whereas unordered ``TOP N``
can stop as soon as it has found N matches. That is too slow to run
synchronously (and multiplies by 3 deep fields per fetch). Two repeated
unordered fetches of the same query were checked directly and returned
the identical 70 object_ids in the identical order, so in practice this
static, frozen Q1 release does not exhibit row-order or row-selection
drift -- but the ADQL/TAP spec does not formally guarantee that absent
an explicit ``ORDER BY``. The fix keeps the fast unordered query and
sorts by ``object_id`` client-side after fetching, which guarantees
deterministic *output* row order regardless of the server's behavior;
combined with each field's sample being fetched once and then cached to
disk (below), the same object_ids and order are what every downstream
consumer of a given cache actually sees.

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

# Real Euclid Deep Field centers and areas (docs/DATA_SOURCES.md; verified
# against Euclid Consortium / Caltech IRSA field-coordinate pages,
# 2026-08-29). Search radius is generous relative to each field's
# circular-equivalent radius (r = sqrt(area/pi)) to ensure full coverage
# without needing the exact (non-circular) field footprint polygon.
DEEP_FIELDS = [
    {"name": "EDF-North", "ra_deg": 269.7329, "dec_deg": 66.0177, "area_deg2": 20.0, "search_radius_deg": 3.0},
    {"name": "EDF-South", "ra_deg": 61.2410, "dec_deg": -48.4230, "area_deg2": 23.0, "search_radius_deg": 3.2},
    {"name": "EDF-Fornax", "ra_deg": 52.9317, "dec_deg": -28.0885, "area_deg2": 10.0, "search_radius_deg": 2.2},
]

_MORPHOLOGY_COLUMNS = """
  m.object_id, c.ra, c.dec,
  m.sersic_sersic_vis_radius, m.sersic_sersic_vis_axis_ratio, m.sersic_sersic_vis_index,
  m.sersic_sersic_nir_radius, m.sersic_sersic_nir_axis_ratio, m.sersic_sersic_nir_index,
  m.sersic_ext_reduced_chi2, m.sersic_ext_flags,
  m.concentration, m.concentration_err, m.gini, m.asymmetry, m.smoothness
"""

FIELD_QUERY_TEMPLATE = """
SELECT TOP {n} {columns}
FROM euclid_q1_mer_morphology m
JOIN euclid_q1_mer_catalogue c ON m.object_id = c.object_id
WHERE m.sersic_ext_flags = 0 AND m.concentration IS NOT NULL
  AND CONTAINS(POINT('ICRS', c.ra, c.dec), CIRCLE('ICRS', {ra}, {dec}, {radius})) = 1
""".replace("{columns}", _MORPHOLOGY_COLUMNS)
# No server-side ORDER BY: see module docstring "Row order" -- it made this
# query ~30x slower on the live service. Row order is instead made
# deterministic client-side, in load_morphology_sample() below.

DISK_SERSIC_NULL_COUNT_QUERY = """
SELECT COUNT(*) AS n_total,
       COUNT(disk_sersic_disk_radius) AS n_disk_sersic_populated
FROM euclid_q1_mer_morphology
"""


@dataclass(frozen=True)
class CachePaths:
    cache_dir: Path

    @property
    def manifest(self) -> Path:
        return self.cache_dir / "manifest.json"


def _tap_fetch(query: str) -> bytes:
    url = IRSA_TAP_SYNC + "?" + urllib.parse.urlencode({"query": query, "format": "csv"})
    with urllib.request.urlopen(url, timeout=120) as resp:
        return resp.read()


def _record_manifest(name: str, query: str, raw: bytes, paths: CachePaths) -> None:
    entry = {
        "url": IRSA_TAP_SYNC, "query": query.strip(), "sha256": hashlib.sha256(raw).hexdigest(),
        "n_bytes": len(raw), "accessed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    manifest = json.loads(paths.manifest.read_text()) if paths.manifest.exists() else {}
    manifest[name] = entry
    paths.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def load_morphology_sample(paths: CachePaths, n: int = 20000, force: bool = False) -> pd.DataFrame:
    """Fetch (or read cached) a real Euclid Q1 MER morphology sample,
    stratified across the three real deep fields (see module docstring)
    rather than one unordered, spatially-unconstrained query."""
    cache_file = paths.cache_dir / f"morphology_sample_{n}.csv"
    if cache_file.exists() and not force:
        return pd.read_csv(cache_file)

    total_area = sum(f["area_deg2"] for f in DEEP_FIELDS)
    allocated = 0
    frames = []
    for i, field in enumerate(DEEP_FIELDS):
        if i == len(DEEP_FIELDS) - 1:
            n_field = n - allocated  # remainder, so the total requested is exact
        else:
            n_field = round(n * field["area_deg2"] / total_area)
            allocated += n_field
        query = FIELD_QUERY_TEMPLATE.format(
            n=n_field, ra=field["ra_deg"], dec=field["dec_deg"], radius=field["search_radius_deg"],
        )
        raw = _tap_fetch(query)
        _record_manifest(f"morphology_sample_{n}_{field['name']}.csv", query, raw, paths)
        df_field = pd.read_csv(io.BytesIO(raw))
        df_field = df_field.sort_values("object_id").reset_index(drop=True)
        df_field["deep_field"] = field["name"]
        frames.append(df_field)

    combined = pd.concat(frames, ignore_index=True)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(cache_file, index=False)
    return combined


def audit_disk_sersic_null_fraction(paths: CachePaths, force: bool = False) -> dict:
    """Live, reproducible COUNT query answering "is the disk+bulge Sersic
    fit populated in the Q1 release?" -- committed with its exact ADQL,
    a checksum, and a timestamp, not just asserted in prose (an external
    review, Codex, found the original version of this finding was only
    described in a docstring/markdown file with no committed result file,
    checksum, or reproducible command; see docs/VALIDATION.md)."""
    cache_file = paths.cache_dir / "disk_sersic_null_audit.json"
    if cache_file.exists() and not force:
        return json.loads(cache_file.read_text())

    raw = _tap_fetch(DISK_SERSIC_NULL_COUNT_QUERY)
    _record_manifest("disk_sersic_null_audit_raw.csv", DISK_SERSIC_NULL_COUNT_QUERY, raw, paths)
    df = pd.read_csv(io.BytesIO(raw))
    n_total = int(df["n_total"].iloc[0])
    n_populated = int(df["n_disk_sersic_populated"].iloc[0])
    result = {
        "query": DISK_SERSIC_NULL_COUNT_QUERY.strip(),
        "accessed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_total_rows": n_total,
        "n_disk_sersic_disk_radius_populated": n_populated,
        "frac_null": (n_total - n_populated) / n_total if n_total else None,
    }
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(result, indent=2))
    return result
