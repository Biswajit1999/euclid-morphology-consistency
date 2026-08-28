# Contributing

## Development setup

```bash
git clone https://github.com/Biswajit1999/euclid-morphology-consistency.git
cd euclid-morphology-consistency
python -m pip install -e ".[dev]"
pytest -q
```

## Before opening a pull request

- Run `pytest -q` and `ruff check src tests`; both must pass.
- If you add a new measurement comparison, use real IRSA TAP data (a
  small verbatim excerpt as an offline test fixture, plus a live network
  test) -- never fabricated values, following the pattern in
  `tests/test_data.py`.

## Good first issues

See the repository Issues tab, including drawing a spatially stratified
sample across the full Q1 footprint (the current sample is concentrated
in one sky region; see `docs/LIMITATIONS.md`) to properly resolve the
position-dependent residual maps the research question asks for.
