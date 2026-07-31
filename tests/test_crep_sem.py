"""Tests for SemanticCREP."""

import warnings

import pytest

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


# ── compute_from_content: real, content-based CREP ──────────────────────────


def test_compute_from_content_empty_path(crep):
    result = crep.compute_from_content([])
    assert set(result) == {"C", "E", "P"}
    assert "R" not in result  # no reference_texts -> no invented R


def test_compute_from_content_single_segment(crep):
    result = crep.compute_from_content(["a lone segment"])
    assert result["C"] == pytest.approx(0.5)
    assert result["E"] == pytest.approx(0.5)


def test_coherent_path_scores_higher_consistency_than_drifting_one(crep):
    coherent = [
        "The AMOC is weakening due to freshwater input.",
        "Freshwater input from Greenland ice melt reduces AMOC strength.",
        "AMOC strength reduction is linked to Greenland meltwater flux.",
    ]
    drifting = [
        "The AMOC is weakening due to freshwater input.",
        "Bananas are rich in potassium and grow in tropical climates.",
        "The stock market fell sharply after the earnings report.",
    ]
    coherent_result = crep.compute_from_content(coherent)
    drifting_result = crep.compute_from_content(drifting)
    assert coherent_result["C"] > drifting_result["C"]


def test_repeating_the_same_segment_scores_low_emergence(crep):
    repetitive = ["the same point restated", "the same point restated", "the same point restated"]
    novel = [
        "the same point restated",
        "an entirely different idea about ocean currents",
        "a further, unrelated idea about neuronal avalanches",
    ]
    repetitive_result = crep.compute_from_content(repetitive)
    novel_result = crep.compute_from_content(novel)
    assert repetitive_result["E"] < novel_result["E"]


def test_reference_texts_enable_real_r(crep):
    segments = ["AMOC tipping point discussion", "further AMOC tipping point details"]
    references = ["Verified ground truth: AMOC tipping point risk assessment"]
    result = crep.compute_from_content(segments, reference_texts=references)
    assert "R" in result
    assert 0.0 <= result["R"] <= 1.0


def test_custom_similarity_fn_is_used(crep):
    calls = []

    def fake_similarity(a: str, b: str) -> float:
        calls.append((a, b))
        return 0.9

    result = crep.compute_from_content(["x", "y", "z"], similarity_fn=fake_similarity)
    assert calls  # the custom callable was actually invoked
    assert result["C"] == pytest.approx(0.9)


def test_compute_from_content_result_is_gamma_sem_compatible(crep):
    """compute_from_content's output (with R filled in) must work with gamma_sem
    exactly like compute()'s output does - same four-key contract."""
    result = crep.compute_from_content(["a", "b", "c"], reference_texts=["a"])
    gamma = crep.gamma_sem(result)
    assert 0.0 <= gamma <= 1.0
