"""HallucinationRisk — Ρ_sem computation and risk classification.

Ρ_sem(P, t) = r_sem · tanh²(σ · Γ_sem(P))
            · (1 − Γ_sem(P)/Γ_max)
            · (1 − |dΓ_sem/dt| / Γ̇_critical)

r_sem comes from the DomainProfile — it is the only free parameter per domain.
Without a DomainProfile, r_sem=1.0 is used (explicitly uncalibrated).
"""

from __future__ import annotations

import math

from scope_resilience.constants import (
    GAMMA_DOT_CRITICAL,
    GAMMA_MAX,
    RISK_LEVELS,
    SIGMA,
)


class HallucinationRisk:
    """Computes Ρ_sem and classifies hallucination risk for a semantic path."""

    SIGMA = SIGMA
    GAMMA_MAX = GAMMA_MAX
    GAMMA_DOT_CRITICAL = GAMMA_DOT_CRITICAL
    RISK_LEVELS = RISK_LEVELS

    def compute_rho(
        self,
        gamma_sem: float,
        domain_profile: object | None = None,
        r_sem: float | None = None,
        d_gamma_dt: float = 0.0,
    ) -> float:
        """Return Ρ_sem ∈ [0, ∞).

        r_sem is taken from domain_profile if supplied, then from the
        r_sem keyword argument, then defaults to 1.0 (uncalibrated).
        """
        if domain_profile is not None:
            r = domain_profile.r  # type: ignore[attr-defined]
        elif r_sem is not None:
            r = r_sem
        else:
            r = 1.0

        tanh_term = math.tanh(self.SIGMA * gamma_sem) ** 2
        crit_term = max(0.0, 1.0 - gamma_sem / self.GAMMA_MAX)
        drift_term = max(0.0, 1.0 - abs(d_gamma_dt) / self.GAMMA_DOT_CRITICAL)
        return r * tanh_term * crit_term * drift_term

    def classify_risk(self, rho_sem: float) -> tuple[str, str]:
        """Return (risk_level, message) for a given Ρ_sem."""
        for (low, high), (level, msg) in self.RISK_LEVELS.items():
            if low <= rho_sem < high:
                return level, msg
        return "critical", "Ρ_sem out of expected range."
