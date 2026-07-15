"""Tests for SemanticUTAC."""

import math
import pytest
from scope_resilience.semantic_utac import SemanticUTAC
from scope_resilience.constants import SIGMA


def test_attractor_at_zero_gamma():
    utac = SemanticUTAC()
    assert utac.attractor(0.0) == pytest.approx(0.0, abs=1e-9)


def test_attractor_formula():
    utac = SemanticUTAC(k_sem=1.0, sigma=SIGMA)
    gamma = 0.5
    expected = math.tanh(SIGMA * gamma)
    assert utac.attractor(gamma) == pytest.approx(expected, rel=1e-9)


def test_hallucination_regime_below_attractor():
    utac = SemanticUTAC()
    gamma = 0.5
    h_star = utac.attractor(gamma)
    assert utac.is_hallucination_regime(h_star * 0.5, gamma) is True


def test_coherence_regime_above_attractor():
    utac = SemanticUTAC()
    gamma = 0.5
    h_star = utac.attractor(gamma)
    assert utac.is_hallucination_regime(h_star * 1.1, gamma) is False


def test_state_dict_keys():
    utac = SemanticUTAC()
    d = utac.state_dict(rho_sem=0.6, gamma_sem=0.4)
    assert set(d) == {"H", "H_star", "K_eff"}


def test_state_dict_clamps_h():
    utac = SemanticUTAC()
    d = utac.state_dict(rho_sem=2.0, gamma_sem=0.3)
    assert d["H"] <= 1.0
