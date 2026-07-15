"""scope-resilience — Hallucination resilience mapping for LLM semantic paths.

Package 41 of the GenesisAeon ecosystem. Extends genesis-scope with Ρ_sem
quantification: a formal pre-flight risk assessment before LLM initialisation
on a semantic path.
"""

from scope_resilience.constants import (
    DOMAIN_CONFIG,
    GAMMA_DOT_CRITICAL,
    GAMMA_MAX,
    KNOWN_DOMAIN_PROFILES,
    RISK_LEVELS,
    SIGMA,
    SIGMA_PHI,
)
from scope_resilience.domain_profile import DomainProfile
from scope_resilience.grounding import GroundingRecommender
from scope_resilience.hallucination_risk import HallucinationRisk
from scope_resilience.llms_txt import LLMSTxtExporter
from scope_resilience.path_monitor import PathDriftMonitor
from scope_resilience.semantic_crep import SemanticCREP
from scope_resilience.semantic_path import SemanticPath
from scope_resilience.semantic_utac import SemanticUTAC
from scope_resilience.system import ScopeResilience

__version__ = "1.0.0"
__author__ = "GenesisAeon"

__all__ = [
    "DOMAIN_CONFIG",
    "GAMMA_DOT_CRITICAL",
    "GAMMA_MAX",
    "KNOWN_DOMAIN_PROFILES",
    "RISK_LEVELS",
    "SIGMA",
    "SIGMA_PHI",
    "DomainProfile",
    "GroundingRecommender",
    "HallucinationRisk",
    "LLMSTxtExporter",
    "PathDriftMonitor",
    "SemanticCREP",
    "SemanticPath",
    "SemanticUTAC",
    "ScopeResilience",
    "__version__",
]
