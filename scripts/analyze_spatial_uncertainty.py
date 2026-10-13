"""Reanalyse the existing cached real Q1 sample; does not fetch new data.

Run after generating the repository's documented cached 20,000-object sample.
Outputs are conditional on that quality-selected, nonrandom sample.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from euclidmorph.data import DEEP_FIELDS  # noqa: E402
from euclidmorph.spatial_uncertainty import (  # noqa: E402
    field_median_diagnostics, moran_permutation, spatial_block_bootstrap,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path, default=ROOT / "data/cache/morphology_sample_20000.csv"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "results/spatial-uncertainty")
    parser.add_argument("--permutations", type=int, default=499)
    parser.add_argument("--replicates", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20261013)
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"missing cached Euclid sample: {args.input}")
    data = pd.read_csv(args.input)
    areas = {field["name"]: field["area_deg2"] for field in DEEP_FIELDS}
    medians = field_median_diagnostics(data, areas)
    spatial = moran_permutation(data, permutations=args.permutations, seed=args.seed)
    bootstrap = spatial_block_bootstrap(data, replicates=args.replicates, seed=args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(medians["fields"]).to_csv(args.out / "field_medians.csv", index=False)
    pd.DataFrame({"permutation_moran_i": spatial["null_statistics"]}).to_csv(
        args.out / "moran_null.csv", index=False)
    summary = {
        "data_kind": "input CSV; scientific provenance not independently verified by this script",
        "expected_source": "repository-cached Euclid Q1 MER sample when using default input",
        "input_file": str(args.input), "seed": args.seed,
        "pooled_median": medians["pooled_median"],
        "area_weighted_mean_field_medians": medians["area_weighted_mean_field_medians"],
        "moran_i": spatial["moran_i"], "moran_null_mean": spatial["null_mean"],
        "moran_p_two_sided": spatial["permutation_p_two_sided"],
        "spatial_block_bootstrap": bootstrap,
        "limitations": (
            "Field-area weights are descriptive only; neither random sampling "
            "nor independence is established. No Euclid-wide inference."
        ),
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    ax.hist(spatial["null_statistics"], bins=35, alpha=0.8, label="Within-field null")
    ax.axvline(spatial["moran_i"], color="black", linestyle="--", label="Observed")
    ax.set(xlabel="Moran's I", ylabel="Permutation count",
           title="VIS−NIR residual spatial autocorrelation")
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.out / "moran_permutation.png", dpi=180)
    plt.close(fig)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
