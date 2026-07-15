"""SemanticCREP — CREP tensor computation for semantic paths.

C_sem = semantic consistency  = 1 − (contradictory_edges / total_edges)
R_sem = semantic resonance    = proximity to verified ground-truth paths
E_sem = semantic emergence    = normalised surprisal of path connections
P_sem = path richness         = tanh(n_edges · mean_weight / ref_density)

Γ_sem = (C · R · E · P)^(1/4)   [standard diamond CREP formula]

Without a live Sigillin store the components are estimated from the
structural properties of the supplied sigillin_ids and q4_transitions.
"""

from __future__ import annotations

import math
import warnings

from scope_resilience.constants import DOMAIN_CONFIG, GAMMA_MAX, SIGMA


class SemanticCREP:
    """Computes the CREP tensor for a semantic path.

    In production this class queries the Sigillin-JetStream store.
    In the current offline implementation it derives plausible proxy
    values from the structural path metadata so that the Diamond
    interface is exercisable without external dependencies.
    """

    DOMAIN_CONFIG = DOMAIN_CONFIG

    @classmethod
    def get_domain_r(cls, domain: str) -> float:
        """Return r_sem for *domain*, falling back to 'general'."""
        config = cls.DOMAIN_CONFIG.get(domain, cls.DOMAIN_CONFIG["general"])
        if config["status"] in ("estimate", "conservative_default"):
            warnings.warn(
                f"r_sem for domain {domain!r} is {config['status']} "
                f"({config['r_sem']}). Calibration pending: "
                f"{config['calibration_source']}. Ρ_sem values are approximate.",
                UserWarning,
                stacklevel=3,
            )
        return config["r_sem"]

    @classmethod
    def calibrate_r(
        cls,
        rho_observed: float,
        gamma: float,
        sigma: float = SIGMA,
        gamma_max: float = GAMMA_MAX,
    ) -> float:
        """Compute r_domain from an observed Ρ and measured Γ.

        r = Ρ_observed / (tanh²(σ·Γ) · (1 − Γ/Γ_max))
        """
        denominator = math.tanh(sigma * gamma) ** 2 * (1.0 - gamma / gamma_max)
        if denominator < 1e-10:
            raise ValueError(f"Γ={gamma} is too close to Γ_max={gamma_max}")
        return rho_observed / denominator

    def compute(
        self,
        sigillin_ids: list[str],
        q4_transitions: list[tuple[str, str]],
    ) -> dict[str, float]:
        """Return CREP components {C, R, E, P} for a semantic path.

        Proxy heuristics (no live store):
          C — consistency: 1.0 when ≥1 sigillin, penalised by duplicate ids
          R — resonance:   tanh(n_anchors / 5) — more anchors → more resonant
          E — emergence:   tanh(n_transitions / 3)
          P — richness:    tanh(total_nodes / 8)
        """
        n_ids = len(sigillin_ids)
        n_unique = len(set(sigillin_ids))
        n_trans = len(q4_transitions)
        total_nodes = n_ids + n_trans

        c_sem = (n_unique / n_ids) if n_ids > 0 else 0.5
        r_sem = math.tanh(n_ids / 5.0) if n_ids > 0 else 0.3
        e_sem = math.tanh(n_trans / 3.0) if n_trans > 0 else 0.2
        p_sem = math.tanh(total_nodes / 8.0) if total_nodes > 0 else 0.2

        return {
            "C": float(max(0.0, min(1.0, c_sem))),
            "R": float(max(0.0, min(1.0, r_sem))),
            "E": float(max(0.0, min(1.0, e_sem))),
            "P": float(max(0.0, min(1.0, p_sem))),
        }

    def gamma_sem(self, crep_components: dict[str, float]) -> float:
        """Γ_sem = (C·R·E·P)^(1/4) — standard CREP formula."""
        product = (
            crep_components["C"]
            * crep_components["R"]
            * crep_components["E"]
            * crep_components["P"]
        )
        return float(product**0.25) if product > 0 else 0.0
