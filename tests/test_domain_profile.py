"""Tests for DomainProfile."""

import math
import pytest
from scope_resilience.domain_profile import DomainProfile
from scope_resilience.constants import SIGMA, GAMMA_MAX


def test_default_profile():
    p = DomainProfile("test", gamma=0.3)
    assert p.r == pytest.approx(1.0)
    assert p.r_status == "open"


def test_from_atlas_target_amoc():
    p = DomainProfile.from_atlas_target("amoc", 0.251, 0.65)
    assert p.r_status == "estimated"
    assert p.r == pytest.approx(3.54, rel=0.05)


def test_from_atlas_target_arctic():
    p = DomainProfile.from_atlas_target("arctic", 0.920, 0.05)
    assert p.r > 10.0  # ≈18 expected


def test_from_atlas_target_quantum():
    # r is large because Γ=0.050 makes tanh²(σΓ) very small
    p = DomainProfile.from_atlas_target("quantum", 0.050, 0.90)
    assert p.r > 1.0
    # Round-trip check: reconstructed Ρ matches target
    rho_check = p.r * math.tanh(SIGMA * 0.050) ** 2 * (1.0 - 0.050 / GAMMA_MAX)
    assert rho_check == pytest.approx(0.90, rel=1e-6)


def test_as_dict_keys():
    p = DomainProfile("test", gamma=0.3)
    d = p.as_dict()
    assert set(d) == {"domain", "gamma", "r", "r_status", "r_source", "rho_atlas_target"}


def test_repr():
    p = DomainProfile("ocean", gamma=0.251, r=3.54, r_status="estimated")
    assert "ocean" in repr(p)
    assert "3.5400" in repr(p)


def test_r_formula_consistency():
    # r = Ρ / (tanh²(σΓ) · (1 − Γ/Γ_max)) should round-trip
    gamma, rho = 0.251, 0.65
    p = DomainProfile.from_atlas_target("x", gamma, rho)
    computed_rho = p.r * math.tanh(SIGMA * gamma) ** 2 * (1.0 - gamma / GAMMA_MAX)
    assert computed_rho == pytest.approx(rho, rel=1e-6)
