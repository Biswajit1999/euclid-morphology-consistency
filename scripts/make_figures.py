"""Regenerate results/figures/*.png from the committed results/ CSVs and
JSON -- not from any uncommitted per-object cache. An external review
(Codex) found this repo declared ``matplotlib`` as a dependency but never
imported it anywhere, and had a committed figure with no script that
reproduced it. Run: ``python scripts/make_figures.py``.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "default"
FIGURES = ROOT / "results" / "figures"

_FIELD_COLORS = {"EDF-North": "#4477AA", "EDF-South": "#CC6677", "EDF-Fornax": "#DDCC77"}


def plot_position_residuals_by_field() -> Path:
    """Per-bin median VIS-NIR Sersic-index residual, one point per
    sky-position bin (docs/METHODS.md), grouped by deep field. Built
    directly from the committed ``position_residuals.csv`` -- see
    analysis.py's ``position_dependent_residuals`` docstring for why
    binning is done within each field's own footprint."""
    df = pd.read_csv(RESULTS / "position_residuals.csv")
    df = df.sort_values(["deep_field", "median_resid"]).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(df))
    colors = [_FIELD_COLORS.get(f, "#888888") for f in df["deep_field"]]
    sizes = 8 + 40 * (df["n"] / df["n"].max())
    ax.scatter(x, df["median_resid"], c=colors, s=sizes, alpha=0.85, edgecolors="none")
    ax.axhline(0.0, color="black", linewidth=0.8, linestyle="--")

    for field, color in _FIELD_COLORS.items():
        if field in df["deep_field"].values:
            ax.scatter([], [], c=color, label=field)
    ax.legend(title="deep field", frameon=False)

    ax.set_xlabel("sky-position bin (sorted within field, point size ~ n objects)")
    ax.set_ylabel("median VIS - NIR Sersic-index residual")
    ax.set_title(f"Position-dependent residual by sub-field bin (n={len(df)} bins, min 20 objects each)")
    fig.tight_layout()

    out = FIGURES / "position_residuals_by_field.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_filter_vs_method_consistency() -> Path:
    """Two summary bars from the committed ``summary.json``: the
    cross-filter (VIS vs NIR Sersic index) bootstrap CI on the median
    residual, and the cross-method (Sersic index vs concentration)
    Spearman correlation -- the two headline numbers in README.md."""
    summary = json.loads((RESULTS / "summary.json").read_text())
    filt = summary["filter_consistency"]
    method = summary["method_correlation"]

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))

    ax = axes[0]
    low, high = filt["median_diff_ci95_low"], filt["median_diff_ci95_high"]
    mid = filt["median_diff_vis_minus_nir"]
    ax.errorbar([0], [mid], yerr=[[mid - low], [high - mid]], fmt="o", capsize=6, color="#4477AA")
    ax.axhline(0.0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlim(-1, 1)
    ax.set_xticks([])
    ax.set_ylabel("median VIS - NIR Sersic-index residual")
    ax.set_title(f"Cross-filter median diff, 95% CI\n(n={filt['n']})")

    ax = axes[1]
    ax.bar([0], [method["spearman_r"]], color="#CC6677", width=0.5)
    ax.set_ylim(0, 1)
    ax.set_xlim(-1, 1)
    ax.set_xticks([])
    ax.set_ylabel("Spearman r")
    ax.set_title(f"Sersic index vs concentration\n(n={method['n']}, p={method['spearman_p']:.2g})")

    fig.tight_layout()
    out = FIGURES / "filter_and_method_consistency.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    for path in (plot_position_residuals_by_field(), plot_filter_vs_method_consistency()):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
