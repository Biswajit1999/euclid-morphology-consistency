"""Plot observed sample-specific Euclid field tail rates and Wilson intervals."""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from euclidmorph.field_inference import wilson_field_intervals  # noqa: E402


def main() -> None:
    fields = wilson_field_intervals(pd.read_csv(ROOT / "results/outlier-audit/field_rates.csv"))
    x = range(len(fields))
    rate = 100 * fields.rate.to_numpy()
    err = [100 * (fields.rate - fields.wilson_low).to_numpy(),
           100 * (fields.wilson_high - fields.rate).to_numpy()]
    fig, ax = plt.subplots(figsize=(7.2, 4.3), layout="constrained")
    ax.errorbar(x, rate, yerr=err, fmt="o", capsize=4, markersize=7)
    ax.axhline(1, linestyle="--", linewidth=1,
               label="Pooled 1% (fixed by tail selection)")
    ax.set_xticks(list(x), fields.deep_field)
    ax.set(ylabel="Sample-specific 99th-percentile tail [%]",
           title="Euclid Q1: field-rate sensitivity (Wilson intervals)")
    ax.legend(loc="best")
    out = ROOT / "results/field-inference/field_rates_wilson.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()
