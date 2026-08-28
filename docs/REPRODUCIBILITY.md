# Reproducibility

```bash
git clone https://github.com/Biswajit1999/euclid-morphology-consistency.git
cd euclid-morphology-consistency
python -m pip install -e ".[dev]"

pytest -q
euclidmorph run --out results/default --n 20000
```

Regenerates `results/default/summary.json` and `position_residuals.csv`
from a live IRSA TAP query; every number in `README.md`, `CHANGELOG.md`,
and `paper/manuscript.md` traces to these files.

## Determinism

The IRSA TAP `TOP N` query is not explicitly seeded and may return
different (though overlapping) rows on repeated queries if the underlying
catalog changes; within one query response, the analysis functions
themselves are fully deterministic (no randomness). Fetched data is
checksummed and timestamped in `data/cache/manifest.json` (git-ignored).
