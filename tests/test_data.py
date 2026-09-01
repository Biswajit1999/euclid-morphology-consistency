"""Offline tests use a small, real, verbatim excerpt of the live Euclid Q1
MER morphology x catalogue join (IRSA TAP, fetched 2026-08-28) so parsing
is checked without a network dependency. A network-marked test exercises
the live service directly.
"""
import io

import pandas as pd
import pytest

from euclidmorph.data import CachePaths, _record_manifest


def test_record_manifest_creates_cache_directory(tmp_path):
    paths = CachePaths(cache_dir=tmp_path / "new-cache")
    _record_manifest("sample.csv", "SELECT 1", b"value\n1\n", paths)
    assert paths.manifest.exists()

_REAL_EXCERPT_CSV = """object_id,ra,dec,sersic_sersic_vis_radius,sersic_sersic_vis_axis_ratio,sersic_sersic_vis_index,sersic_sersic_nir_radius,sersic_sersic_nir_axis_ratio,sersic_sersic_nir_index,sersic_ext_reduced_chi2,sersic_ext_flags,concentration,concentration_err,gini,asymmetry,smoothness
-640313926487389991,64.03139267,-48.73899914,2.4099083245e-01,1.0000000000e+00,2.9156799316e+00,5.3580588102e-01,9.0964704752e-01,1.3727476597e+00,3.8974237061e+02,0,4.1289453506e+00,2.7381345630e-01,7.1791917086e-01,3.9151895046e-01,3.7834545970e-01
-640371822487390002,64.03718226,-48.73900027,1.3159011602e+00,3.8113859296e-01,1.0992510319e+00,6.2844686508e+00,3.2191899419e-01,3.0364966393e-01,9.0923421085e-02,0,2.1145503521e+00,5.7251971960e-01,7.9500389099e-01,4.9027439207e-02,2.6977646351e-01
-640027557487389085,64.00275576,-48.73890856,3.3545038104e-01,2.4100649357e-01,3.0000495911e-01,1.3232149184e-01,9.9999403954e-01,3.0036813021e-01,4.6766843647e-02,0,1.6249437332e+00,7.2298938036e-01,5.5612760782e-01,7.0993995667e-01,1.6741202772e-01
-645512401487388491,64.55124016,-48.73884917,4.3702483177e-01,2.9052382708e-01,1.1172707081e+00,2.3680059910e+00,4.3124911189e-01,5.2910871506e+00,7.4710689485e-02,0,2.3734433651e+00,4.8808500171e-01,8.1222176552e-01,1.1691187620e+00,3.6038365960e-01
-638986272487386262,63.89862728,-48.73862621,4.4573980570e-01,2.5616329908e-01,3.5956236720e-01,8.9761769772e-01,3.2462403178e-01,1.1715689898e+00,6.6243425012e-02,0,1.7847268581e+00,6.3766002655e-01,5.6473296881e-01,1.0951143503e-01,2.1696208417e-01
"""


def test_real_excerpt_parses_and_has_expected_columns():
    df = pd.read_csv(io.StringIO(_REAL_EXCERPT_CSV))
    assert len(df) == 5
    expected_cols = {
        "object_id", "ra", "dec", "sersic_sersic_vis_index", "sersic_sersic_nir_index",
        "sersic_ext_flags", "concentration", "gini", "asymmetry", "smoothness",
    }
    assert expected_cols.issubset(set(df.columns))


def test_real_excerpt_all_rows_have_good_sersic_flag():
    # the query filters on sersic_ext_flags = 0; the real excerpt must
    # reflect that filter having been applied upstream
    df = pd.read_csv(io.StringIO(_REAL_EXCERPT_CSV))
    assert (df["sersic_ext_flags"] == 0).all()


def test_real_excerpt_ra_dec_are_in_the_q1_deep_field_range():
    """Regression test: the original version of this test only checked
    generic all-sky bounds (0-360, -90 to 90) despite its name claiming to
    check the actual Q1 deep field range -- an external review (Codex)
    caught this. This excerpt's coordinates (RA~64.0, Dec~-48.7) are
    actually from the Euclid Deep Field **South** region (center
    RA=61.2410, Dec=-48.4230), not Fornax as an earlier comment here
    incorrectly stated -- corrected. Check it actually falls within that
    field, not just anywhere on the sky."""
    import numpy as np

    from euclidmorph.data import DEEP_FIELDS

    south = next(f for f in DEEP_FIELDS if f["name"] == "EDF-South")
    df = pd.read_csv(io.StringIO(_REAL_EXCERPT_CSV))
    # Angular separation on the sky (small-angle approximation, adequate
    # for a few-degree separation), not independent RA/Dec box bounds --
    # matches the actual CIRCLE(...) cone-search geometry used by the
    # live query in data.py.
    dec_rad = np.radians(df["dec"])
    d_ra = (df["ra"] - south["ra_deg"]) * np.cos(dec_rad)
    d_dec = df["dec"] - south["dec_deg"]
    sep_deg = np.hypot(d_ra, d_dec)
    assert (sep_deg < south["search_radius_deg"]).all()


@pytest.mark.network
def test_live_fetch_returns_populated_concentration_column(tmp_path):
    from euclidmorph.data import CachePaths, load_morphology_sample

    paths = CachePaths(cache_dir=tmp_path)
    df = load_morphology_sample(paths, n=200)
    # Not asserting an exact count: a field may have fewer than its
    # proportional allocation of real qualifying objects within its
    # search radius, in which case TOP N returns fewer rows -- a real
    # possibility with live data, not something to paper over with an
    # exact-count assertion.
    assert len(df) > 150
    assert df["concentration"].notna().all()
    assert (df["sersic_ext_flags"] == 0).all()


@pytest.mark.network
def test_live_fetch_covers_multiple_deep_fields(tmp_path):
    """Regression test for the representativeness bug: the original
    unordered SELECT TOP N drew almost the entire sample from one deep
    field (an external review, Codex, found only 3 of 36 spatial bins
    populated in the committed sample). The stratified fetch should
    return objects from all three deep fields."""
    from euclidmorph.data import CachePaths, load_morphology_sample

    paths = CachePaths(cache_dir=tmp_path)
    df = load_morphology_sample(paths, n=300)
    assert df["deep_field"].nunique() == 3


@pytest.mark.network
def test_disk_sersic_null_audit_is_reproducible_and_committed(tmp_path):
    from euclidmorph.data import CachePaths, audit_disk_sersic_null_fraction

    paths = CachePaths(cache_dir=tmp_path)
    result = audit_disk_sersic_null_fraction(paths)
    assert result["n_total_rows"] > 0
    assert 0.0 <= result["frac_null"] <= 1.0
    assert (paths.cache_dir / "disk_sersic_null_audit.json").exists()
