"""Tests for SemanticCREP."""

import math
import pytest
import warnings
from scope_resilience.semantic_crep import SemanticCREP


@pytest.fixture
def crep():
    return SemanticCREP()


def test_compute_empty_path(crep):
    result = crep.compute([], [])
    assert set(result) == {"C", "R", "E", "P"}
    for v in result.values():
        assert 0.0 <= v <= 1.0


def test_compute_with_ids(crep):
    ids = ["s1", "s2", "s3"]
    trans = [("s1", "s2"), ("s2", "s3")]
    result = crep.compute(ids, trans)
    assert result["C"] == pytest.approx(1.0)  # all unique
    assert result["R"] > 0.0
    assert result["E"] > 0.0
    assert result["P"] > 0.0


def test_duplicate_ids_reduce_consistency(crep):
    ids_unique = ["s1", "s2", "s3"]
    ids_dup = ["s1", "s1", "s2"]
    r_unique = crep.compute(ids_unique, [])
    r_dup = crep.compute(ids_dup, [])
    assert r_dup["C"] < r_unique["C"]


def test_gamma_sem_formula(crep):
    comps = {"C": 0.5, "R": 0.5, "E": 0.5, "P": 0.5}
    expected = (0.5 ** 4) ** 0.25
    assert crep.gamma_sem(comps) == pytest.approx(expected, rel=1e-9)


def test_gamma_sem_zero_component(crep):
    comps = {"C": 0.0, "R": 0.5, "E": 0.5, "P": 0.5}
    assert crep.gamma_sem(comps) == pytest.approx(0.0)


def test_calibrate_r_amoc():
    # r = Ρ / (tanh²(σΓ) · (1 − Γ/Γ_max)) for AMOC should be ≈ 3.54
    r = SemanticCREP.calibrate_r(rho_observed=0.65, gamma=0.251)
    assert r == pytest.approx(3.54, rel=0.05)


def test_calibrate_r_near_gamma_max_raises():
    with pytest.raises(ValueError):
        SemanticCREP.calibrate_r(rho_observed=0.5, gamma=0.920)


def test_get_domain_r_warns_for_estimate():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = SemanticCREP.get_domain_r("physics_dense")
        assert any("estimate" in str(warning.message).lower() for warning in w)
    assert r == pytest.approx(0.80)


def test_get_domain_r_fallback_to_general():
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        r = SemanticCREP.get_domain_r("unknown_domain_xyz")
    assert r == pytest.approx(0.50)
