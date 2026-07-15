"""DomainProfile — the only free parameter per domain in the UTAC framework.

r is the 'fingerprint' of a domain. All other quantities are either universal
constants (σ, σ_Φ, Γ_max) or measurable (Γ, C_ij).

Calibration formula (identical for physical and semantic domains):
    r_domain = Ρ_observed / (tanh²(σ·Γ) · (1 − Γ/Γ_max))
"""

from __future__ import annotations

import math
from typing import Any


class DomainProfile:
    """Domain-specific configuration for UTAC resilience.

    status values:
        "calibrated" — r fitted from real time-series data (gold standard)
        "estimated"  — r derived analytically from an atlas target value
        "open"       — r not yet determined; default r=1.0 active
    """

    def __init__(
        self,
        domain: str,
        gamma: float,
        r: float = 1.0,
        r_status: str = "open",
        r_source: str = "default",
        rho_atlas_target: float | None = None,
    ) -> None:
        self.domain = domain
        self.gamma = gamma
        self.r = r
        self.r_status = r_status
        self.r_source = r_source
        self.rho_atlas_target = rho_atlas_target

    @classmethod
    def from_atlas_target(
        cls,
        domain: str,
        gamma: float,
        rho_target: float,
        sigma: float = 2.2,
        gamma_max: float = 0.920,
    ) -> DomainProfile:
        """Compute r_required analytically from an atlas target Ρ.

        r_required = Ρ_target / (tanh²(σ·Γ) · (1 − Γ/Γ_max))

        Status = "estimated" — no real time-series yet.
        """
        tanh_sq = math.tanh(sigma * gamma) ** 2
        crit = max(1e-10, 1.0 - gamma / gamma_max)
        r_required = rho_target / (tanh_sq * crit)
        return cls(
            domain=domain,
            gamma=gamma,
            r=r_required,
            r_status="estimated",
            r_source=f"analytical from Ρ_atlas={rho_target}",
            rho_atlas_target=rho_target,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "gamma": self.gamma,
            "r": self.r,
            "r_status": self.r_status,
            "r_source": self.r_source,
            "rho_atlas_target": self.rho_atlas_target,
        }

    def __repr__(self) -> str:
        return (
            f"DomainProfile(domain={self.domain!r}, gamma={self.gamma}, "
            f"r={self.r:.4f}, status={self.r_status!r})"
        )
