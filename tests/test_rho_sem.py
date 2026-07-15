"""Tests for HallucinationRisk Ρ_sem computation."""

import math
import pytest
from scope_resilience.hallucination_risk import HallucinationRisk
from scope_resilience.constants import SIGMA, GAMMA_MAX


@pytest.fixture
def risk():
    return HallucinationRisk()


def test_rho_positive(risk):
    rho = risk.compute_rho(0.5)
    assert rho >= 0.0


def test_rho_zero_gamma(risk):
    rho = risk.compute_rho(0.0)
    assert rho == pytest.approx(0.0, abs=1e-9)


def test_rho_at_gamma_max_is_zero(risk):
    rho = risk.compute_rho(GAMMA_MAX)
    assert rho == pytest.approx(0.0, abs=1e-9)


def test_rho_formula_uncalibrated(risk):
    gamma = 0.5
    tanh_sq = math.tanh(SIGMA * gamma) ** 2
    crit = 1.0 - gamma / GAMMA_MAX
    expected = 1.0 * tanh_sq * crit  # r=1.0 (default)
    assert risk.compute_rho(gamma) == pytest.approx(expected, rel=1e-9)


def test_rho_with_explicit_r(risk):
    gamma = 0.251
    rho_r1 = risk.compute_rho(gamma, r_sem=1.0)
    rho_r3 = risk.compute_rho(gamma, r_sem=3.0)
    assert rho_r3 == pytest.approx(3.0 * rho_r1, rel=1e-9)


def test_drift_reduces_rho(risk):
    gamma = 0.4
    rho_nodrift = risk.compute_rho(gamma, d_gamma_dt=0.0)
    rho_drift = risk.compute_rho(gamma, d_gamma_dt=0.05)
    assert rho_drift < rho_nodrift


def test_critical_drift_zeroes_rho(risk):
    gamma = 0.4
    rho = risk.compute_rho(gamma, d_gamma_dt=0.10)
    assert rho == pytest.approx(0.0, abs=1e-9)


def test_classify_safe(risk):
    level, msg = risk.classify_risk(0.75)
    assert level == "safe"


def test_classify_moderate(risk):
    level, _ = risk.classify_risk(0.55)
    assert level == "moderate"


def test_classify_high_risk(risk):
    level, _ = risk.classify_risk(0.25)
    assert level == "high_risk"


def test_classify_critical(risk):
    level, _ = risk.classify_risk(0.05)
    assert level == "critical"
