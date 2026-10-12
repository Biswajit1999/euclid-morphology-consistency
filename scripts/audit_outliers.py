"""Generate the real Euclid VIS--NIR Sersic outlier audit."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import scienceplots  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from euclidmorph.outliers import (  # noqa: E402
    field_rates,
    outlier_summary,
    robust_outlier_table,
    threshold_sensitivity,
)


def main() -> None:
    data = pd.read_csv(ROOT / "data/cache/morphology_sample_20000.csv")
    work = robust_outlier_table(data)
    summary = outlier_summary(work)
    sensitivity = threshold_sensitivity(data)
    fields = field_rates(work)
    out = ROOT / "results/outlier-audit"
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(
            {
                "data_kind": "real Euclid Q1 MER catalogue measurements",
                **summary,
                "limitations": (
                    "The 99th-percentile tail is an audit definition, not a physical class. "
                    "The sample is quality-flagged and spatially stratified but not a random "
                    "draw from the complete Q1 population; neither VIS nor NIR is treated as truth."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    sensitivity.to_csv(out / "threshold_sensitivity.csv", index=False)
    fields.to_csv(out / "field_rates.csv", index=False)
    work.loc[work.is_outlier].sort_values("absolute_residual", ascending=False).to_csv(
        out / "outlier_objects.csv", index=False
    )

    with plt.style.context(["science", "no-latex", "bright"]):
        fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.7), constrained_layout=True)
        axes[0].hexbin(
            work.sersic_sersic_nir_index,
            work.sersic_sersic_vis_index,
            gridsize=55,
            bins="log",
            mincnt=1,
            cmap="viridis",
        )
        axes[0].plot([0.2, 5.5], [0.2, 5.5], "--", color="white", lw=1)
        axes[0].set(xlim=(0, 5.7), ylim=(0, 5.7))
        axes[0].set(
            xlabel="NIR Sersic index", ylabel="VIS Sersic index", title="(a) 20,000 real objects"
        )

        axes[1].scatter(
            sensitivity["threshold_absolute_sersic_index"],
            sensitivity["median_reduced_chi2"],
            s=55,
            c=sensitivity["quantile"],
            cmap="plasma",
        )
        for row in sensitivity.itertuples():
            axes[1].annotate(
                f"q={row.quantile:g}",
                (row.threshold_absolute_sersic_index, row.median_reduced_chi2),
                fontsize=6,
            )
        axes[1].set(
            xlabel="Tail threshold |VIS--NIR|",
            ylabel="Tail median reduced chi-square",
            title="(b) Threshold sensitivity",
        )

        axes[2].bar(fields.deep_field, 100 * fields.rate)
        axes[2].axhline(1, color="0.3", ls="--", lw=1, label="Pooled 1% definition")
        axes[2].set(
            xlabel="Euclid deep field",
            ylabel="99th-percentile tail [%]",
            title="(c) Field prevalence",
        )
        axes[2].tick_params(axis="x", rotation=25)
        axes[2].legend(frameon=False)
        fig.suptitle("Euclid Q1 VIS--NIR Sersic disagreement audit")
        fig.savefig(out / "outlier_audit.png", dpi=240)
        fig.savefig(out / "outlier_audit.pdf")
        plt.close(fig)


if __name__ == "__main__":
    main()
