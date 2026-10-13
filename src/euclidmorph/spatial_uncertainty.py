"""Field-aware VIS/NIR morphology uncertainty and spatial-dependence checks.

Statistics are conditional on the supplied sample, not Euclid-wide estimates.
The existing IRSA TAP sample is quality-selected and not probability sampled.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    columns = ["deep_field", "ra", "dec", "sersic_sersic_vis_index", "sersic_sersic_nir_index"]
    if not set(columns).issubset(df.columns):
        raise ValueError(f"required columns: {columns}")
    data = df[columns].copy()
    numeric = columns[1:]
    if any(not pd.api.types.is_numeric_dtype(data[c]) for c in numeric):
        raise ValueError("coordinates and Sersic indices must be numeric")
    data = data.replace([np.inf, -np.inf], np.nan).dropna(subset=columns)
    if data.empty or not data.dec.between(-90, 90).all():
        raise ValueError("no valid finite coordinates and Sersic indices")
    data["residual"] = data.sersic_sersic_vis_index - data.sersic_sersic_nir_index
    return data


def _project(ra: np.ndarray, dec: np.ndarray) -> np.ndarray:
    """Small-field tangent approximation, wrapping RA across 0/360 degrees."""
    ra = np.asarray(ra, dtype=float)
    dec = np.asarray(dec, dtype=float)
    center_ra = np.arctan2(np.sin(np.deg2rad(ra)).mean(),
                           np.cos(np.deg2rad(ra)).mean())
    east = np.rad2deg(np.angle(np.exp(1j * (np.deg2rad(ra) - center_ra))))
    east *= np.cos(np.deg2rad(dec.mean()))
    return np.column_stack((east, dec - dec.mean()))


def field_median_diagnostics(df: pd.DataFrame, field_areas_deg2: dict[str, float]) -> dict:
    """Compare pooled median with area-weighted *mean of field medians*.

    Area weights are descriptive, not inverse-selection-probability weights.
    """
    data = _clean(df)
    fields = []
    for name, group in data.groupby("deep_field", sort=True):
        if (
            name not in field_areas_deg2 or not np.isfinite(field_areas_deg2[name])
            or field_areas_deg2[name] <= 0
        ):
            raise ValueError(f"missing or invalid field area: {name}")
        fields.append({"deep_field": name, "n": len(group),
                       "median_residual": float(group.residual.median()),
                       "mad_residual": float(
                           np.median(np.abs(group.residual - group.residual.median()))
                       ),
                       "area_deg2": float(field_areas_deg2[name])})
    area = np.array([f["area_deg2"] for f in fields])
    medians = np.array([f["median_residual"] for f in fields])
    return {"n": len(data), "pooled_median": float(data.residual.median()),
            "area_weighted_mean_field_medians": float(np.average(medians, weights=area)),
            "fields": fields}


def moran_permutation(df: pd.DataFrame, k: int = 6, permutations: int = 499,
                      seed: int = 20261013) -> dict:
    """Within-field kNN Moran's I with a within-field permutation null.

    Residuals are centered per field; cross-field neighbors are prohibited.
    The p-value is a two-sided permutation test around the simulated null
    mean (not an analytic independent-sample significance claim).
    """
    data = _clean(df)
    if k < 1 or permutations < 19:
        raise ValueError("k >= 1 and permutations >= 19 required")
    centered = []
    neighbors = []
    groups = []
    offset = 0
    for _, sub in data.groupby("deep_field", sort=True):
        if len(sub) <= k:
            raise ValueError("each field needs at least k+1 valid objects")
        xy = _project(sub.ra.to_numpy(), sub.dec.to_numpy())
        indices = cKDTree(xy).query(xy, k=k + 1)[1][:, 1:]
        z = sub.residual.to_numpy(dtype=float)
        z -= z.mean()
        centered.append(z)
        neighbors.append(indices + offset)
        groups.append(np.arange(offset, offset + len(z)))
        offset += len(z)
    values = np.concatenate(centered)
    adjacency = np.vstack(neighbors)
    denom = float(values @ values)
    if np.allclose(values, 0, rtol=0, atol=1e-12):
        raise ValueError("constant within-field residuals make Moran's I undefined")
    def statistic(z: np.ndarray) -> float:
        return float(np.sum(z[:, None] * z[adjacency]) / (k * denom))
    observed = statistic(values)
    rng = np.random.default_rng(seed)
    null = np.empty(permutations)
    for b in range(permutations):
        permuted = values.copy()
        for idx in groups:
            permuted[idx] = rng.permutation(values[idx])
        null[b] = statistic(permuted)
    center = float(null.mean())
    pvalue = (1 + np.sum(np.abs(null - center) >= abs(observed - center))) / (permutations + 1)
    return {"n": len(values), "n_fields": len(groups), "k": k,
            "moran_i": observed, "null_mean": center,
            "null_std": float(null.std(ddof=1)), "permutation_p_two_sided": float(pvalue),
            "null_statistics": null}


def spatial_block_bootstrap(df: pd.DataFrame, n_tiles: int = 4,
                            replicates: int = 1000, seed: int = 20261013) -> dict:
    """Resample spatial tiles *within each field* to estimate median uncertainty.

    Fixed square grid in locally projected degrees. Tiles are sampled with
    replacement, not individual objects. Empty tiles are excluded.
    """
    data = _clean(df)
    if n_tiles < 2 or replicates < 100:
        raise ValueError("n_tiles >= 2 and replicates >= 100 required")
    groups = []
    for _, sub in data.groupby("deep_field", sort=True):
        xy = _project(sub.ra.to_numpy(), sub.dec.to_numpy())
        ranges = np.ptp(xy, axis=0)
        if np.any(ranges <= 0):
            raise ValueError("each field needs a two-dimensional spatial footprint")
        cell = np.minimum((n_tiles * (xy - xy.min(axis=0)) / ranges).astype(int), n_tiles - 1)
        labels = cell[:, 0] * n_tiles + cell[:, 1]
        residual = sub.residual.to_numpy(dtype=float)
        blocks = [residual[labels == key] for key in np.unique(labels)]
        if len(blocks) < 3:
            raise ValueError("each field needs at least three occupied tiles")
        groups.append(blocks)
    rng = np.random.default_rng(seed)
    boot = np.empty(replicates)
    for b in range(replicates):
        sampled = []
        for blocks in groups:
            picks = rng.integers(0, len(blocks), size=len(blocks))
            sampled.extend(blocks[i] for i in picks)
        boot[b] = np.median(np.concatenate(sampled))
    return {"n": len(data), "n_fields": len(groups),
            "n_occupied_tiles": int(sum(map(len, groups))),
            "median": float(data.residual.median()),
            "ci95_low": float(np.quantile(boot, 0.025)),
            "ci95_high": float(np.quantile(boot, 0.975)),
            "bootstrap_std": float(boot.std(ddof=1))}
