"""SemanticUTAC — mapping of UTAC dynamics to LLM semantic coherence.

H_sem(t) = semantic coherence density on path P
K_sem    = maximum coherence capacity (normalised to 1.0)
H*_sem   = coherence attractor = tanh(σ · Γ_sem(P))

When H_sem < H*_sem the system is in the hallucination regime.
When H_sem > H*_sem the system is in the coherence regime.
"""

from __future__ import annotations

import math

from scope_resilience.constants import SIGMA


class SemanticUTAC:
    """Maps UTAC ODE quantities to semantic coherence quantities.

    dH_sem/dt = r·H_sem·(1 − H_sem/K_sem)·tanh(σ·Γ_sem)

    Fixpoint: H*_sem = K_sem · tanh(σ · Γ_sem)
    """

    def __init__(self, k_sem: float = 1.0, sigma: float = SIGMA) -> None:
        self.k_sem = k_sem
        self.sigma = sigma

    def attractor(self, gamma_sem: float) -> float:
        """H*_sem = K_sem · tanh(σ · Γ_sem)."""
        return self.k_sem * math.tanh(self.sigma * gamma_sem)

    def is_hallucination_regime(self, h_sem: float, gamma_sem: float) -> bool:
        """True when the system is below the coherence attractor."""
        return h_sem < self.attractor(gamma_sem)

    def state_dict(self, rho_sem: float, gamma_sem: float) -> dict[str, float]:
        """Return UTACState-compatible dict with semantic interpretations."""
        return {
            "H": float(max(0.0, min(1.0, rho_sem))),
            "H_star": float(max(0.0, min(1.0, self.attractor(gamma_sem)))),
            "K_eff": float(self.k_sem),
        }
