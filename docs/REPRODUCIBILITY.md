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

The live per-field query intentionally omits a server-side `ORDER BY`
(measured to be ~30x slower with one -- `docs/LIMITATIONS.md`); instead,
`load_morphology_sample` sorts each field's fetched rows by `object_id`
client-side, which guarantees deterministic *output* row order regardless
of the server's own scan order. The set of rows a fresh `TOP N` fetch
returns is not formally guaranteed stable by the ADQL/TAP specification
(and may change if the underlying static Q1 release were ever updated),
but each field's sample is fetched once and cached to
`data/cache/morphology_sample_{n}.csv` (git-ignored); re-running
`euclidmorph run` against an existing cache reuses it rather than
re-fetching. `filter_consistency`'s bootstrap resampling is seeded
(default `seed=0`) and reproducible given the same input data. Fetched
raw responses are checksummed and timestamped in
`data/cache/manifest.json` (git-ignored).
