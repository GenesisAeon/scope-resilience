"""SemanticUTAC — mapping of UTAC dynamics to LLM semantic coherence.

H_sem(t) = semantic coherence density on path P
K_sem    = maximum coherence capacity (normalised to 1.0)
H*_sem   = K_sem · tanh(σ · Γ_sem) — coherence reference/threshold for
           hallucination-vs-coherence regime classification (NOT a rigorously
           derived fixpoint of the stated logistic ODE; verified numerically
           2026-09-15). See SemanticUTAC class docstring.

When H_sem < H*_sem the system is in the hallucination regime.
When H_sem > H*_sem the system is in the coherence regime.
"""

from __future__ import annotations

import math

from scope_resilience.constants import SIGMA


class SemanticUTAC:
    """Maps UTAC ODE quantities to semantic coherence quantities.

    Motivating / illustrative logistic-growth context (not what attractor()
    integrates):

    dH_sem/dt = r·H_sem·(1 − H_sem/K_sem)·tanh(σ·Γ_sem)

    H*_sem = K_sem · tanh(σ · Γ_sem) is used here as the coherence
    reference/threshold for hallucination-vs-coherence regime classification
    — it is NOT a rigorously derived fixpoint of the stated logistic ODE
    dH/dt = r·H·(1−H/K)·tanh(σΓ) (whose actual nonzero fixpoint is H=K,
    independent of Γ; verified numerically 2026-09-15). The ODE above is
    presented as motivating/illustrative context for the logistic-growth
    intuition behind H_sem, not as the literal equation attractor()
    implements — attractor() computes K_sem·tanh(σΓ_sem) directly and
    algebraically, without integrating any ODE. Treat H*_sem as an
    independently defined regime-boundary reference value.
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
