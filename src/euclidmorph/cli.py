"""Command-line workflow for the Euclid Q1 morphology consistency audit."""
from __future__ import annotations

import json
from pathlib import Path

import click

from .analysis import (
    filter_consistency,
    method_correlation,
    position_dependent_residuals,
    quality_flag_summary,
)
from .data import CachePaths, audit_disk_sersic_null_fraction, load_morphology_sample


@click.group()
def main() -> None:
    """euclidmorph: Euclid Q1 galaxy-morphology consistency audit."""


@main.command("run")
@click.option("--cache-dir", default="data/cache", show_default=True)
@click.option("--out", "out_dir", default="results", show_default=True)
@click.option("--n", default=20000, show_default=True, help="Sample size to fetch from IRSA TAP.")
def run_cmd(cache_dir: str, out_dir: str, n: int) -> None:
    paths = CachePaths(cache_dir=Path(cache_dir))
    df = load_morphology_sample(paths, n=n)
    click.echo(f"Loaded {len(df)} real Euclid Q1 MER morphology rows (quality-flagged, concentration-populated).")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    filt = filter_consistency(df)
    method = method_correlation(df)
    quality = quality_flag_summary(df)
    summary = {"filter_consistency": filt, "method_correlation": method, "quality_flags": quality}
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    click.echo(json.dumps(summary, indent=2))

    position = position_dependent_residuals(df)
    position.to_csv(out / "position_residuals.csv", index=False)
    click.echo(f"Wrote {out/'position_residuals.csv'} ({len(position)} sky-position bins with >=20 objects)")


@main.command("audit-schema")
@click.option("--cache-dir", default="data/cache", show_default=True)
@click.option("--out", "out_dir", default="results", show_default=True)
@click.option("--force", is_flag=True, default=False)
def audit_schema_cmd(cache_dir: str, out_dir: str, force: bool) -> None:
    """Live, reproducible COUNT query answering whether the catalog's
    disk+bulge Sersic fit (``disk_sersic_*`` columns) is populated in the
    Q1 release -- committed with its exact ADQL, a checksum, and a
    timestamp, not just asserted in prose (see docs/VALIDATION.md)."""
    paths = CachePaths(cache_dir=Path(cache_dir))
    result = audit_disk_sersic_null_fraction(paths, force=force)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "disk_sersic_null_audit.json").write_text(json.dumps(result, indent=2))
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
