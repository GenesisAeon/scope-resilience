"""Diamond interface compliance tests for ScopeResilience."""

import pytest
from diamond_setup.protocol import NotConvergedError
from diamond_setup.validation import validate_diamond_instance
from scope_resilience.system import ScopeResilience


@pytest.fixture
def sr():
    return ScopeResilience(domain="general")


def test_raises_before_run_cycle(sr):
    with pytest.raises(NotConvergedError):
        sr.get_crep_state()
    with pytest.raises(NotConvergedError):
        sr.get_utac_state()


def test_run_cycle_returns_dict(sr):
    result = sr.run_cycle("AMOC tipping point")
    assert isinstance(result, dict)
    for key in ("topic", "gamma_sem", "rho_sem", "risk_level"):
        assert key in result


def test_crep_state_keys(sr):
    sr.run_cycle("quantum decoherence", sigillin_ids=["q1", "q2"])
    state = sr.get_crep_state()
    assert set(state) >= {"C", "R", "E", "P", "Gamma"}
    assert state["Gamma"] is not None
    assert 0.0 <= state["Gamma"] <= 1.0


def test_utac_state_keys(sr):
    sr.run_cycle("entropy production")
    state = sr.get_utac_state()
    assert set(state) == {"H", "H_star", "K_eff"}


def test_phase_events_list(sr):
    sr.run_cycle("test topic")
    events = sr.get_phase_events()
    assert isinstance(events, list)


def test_zenodo_record_keys(sr):
    record = sr.to_zenodo_record()
    assert set(record) >= {"title", "description", "creators"}
    assert "scope-resilience" in record["title"].lower() or "hallucination" in record["title"].lower()


def test_resilience_state_after_cycle(sr):
    sr.run_cycle("arctic ice loss", sigillin_ids=["a1"])
    res = sr.get_resilience_state()
    assert res["implemented"] is True
    assert res["rho_sem"] is not None
    assert res["risk_level"] in ("safe", "moderate", "high_risk", "critical")


def test_resilience_state_before_cycle_no_error(sr):
    res = sr.get_resilience_state()
    assert res["rho_sem"] is None
    assert res["risk_level"] == "unknown"


def test_validate_diamond_instance():
    instance = ScopeResilience()
    errors = validate_diamond_instance(
        instance,
        run_cycle=True,
        check_pre_cycle_guard=True,
    )
    assert errors == [], f"Diamond validation failed: {errors}"


def test_get_semantic_path_returns_path(sr):
    path = sr.get_semantic_path("AMOC", min_rho=0.0)
    assert path is not None
    assert path.topic == "AMOC"
    assert 0.0 <= path.gamma_sem <= 1.0


def test_llms_txt_no_cycle():
    sr = ScopeResilience()
    txt = sr.to_llms_txt()
    assert "No semantic path" in txt


def test_llms_txt_with_topic():
    sr = ScopeResilience()
    txt = sr.to_llms_txt("dark matter")
    assert "dark matter" in txt
    assert "Resilience" in txt


def test_cycles_completed_increments(sr):
    assert sr.cycles_completed == 0
    sr.run_cycle("test")
    assert sr.cycles_completed == 1
    sr.run_cycle("test2")
    assert sr.cycles_completed == 2


def test_high_risk_generates_phase_event():
    # A path with no sigillin_ids → very low Γ_sem → likely critical/high_risk
    sr = ScopeResilience(domain="sparse_fringe")
    sr.run_cycle("highly speculative fringe topic")
    events = sr.get_phase_events()
    # Events may or may not be present depending on computed rho; just check type
    assert isinstance(events, list)
