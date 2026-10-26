"""Audit published Euclid Q1 field rates; no network calls or new catalog queries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from euclidmorph.field_inference import (  # noqa: E402
    conditional_field_heterogeneity,
    pairwise_field_contrasts,
    wilson_field_intervals,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "results/outlier-audit/field_rates.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "results/field-inference")
    parser.add_argument("--simulations", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261026)
    args = parser.parse_args()
    fields = pd.read_csv(args.input)
    args.output.mkdir(parents=True, exist_ok=True)
    intervals = wilson_field_intervals(fields)
    pairs = pairwise_field_contrasts(fields)
    heterogeneity = conditional_field_heterogeneity(
        fields, simulations=args.simulations, seed=args.seed
    )
    intervals.to_csv(args.output / "field_intervals.csv", index=False)
    pairs.to_csv(args.output / "pairwise_fisher_bh.csv", index=False)
    (args.output / "heterogeneity.json").write_text(
        json.dumps({"data_kind": "derived from committed real Euclid Q1 field counts",
                    "interpretation": "conditional, sample-specific; not a survey-population claim",
                    **heterogeneity}, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(heterogeneity, indent=2))


if __name__ == "__main__":
    main()
