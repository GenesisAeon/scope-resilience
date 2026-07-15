"""SemanticPath — primary entity for the Semantic Operating System."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SemanticPath:
    """A semantic path through the GenesisAeon knowledge space.

    Consists of a sequence of Sigillin state anchors connected via valid
    Q4 transitions, with a CREP coherence value as quality measure.
    """

    topic: str
    sigillin_ids: list[str]
    q4_transitions: list[tuple[str, str]]
    gamma_sem: float
    rho_sem: float
    domain: str
    crep_components: dict[str, float]
    risk_level: str
    grounding_recommendations: list[str] = field(default_factory=list)
