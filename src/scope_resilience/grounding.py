"""GroundingRecommender — grounding strategies when Ρ_sem is low.

Grounding = embedding verified Sigillin anchors into the LLM context to
raise H_sem and dampen dΓ_sem/dt, pulling the system back to the attractor.
"""

from __future__ import annotations

from scope_resilience.semantic_path import SemanticPath

# Domains with high calibrated Ρ used as cross-domain grounding sources
_HIGH_RESILIENCE_DOMAINS = ["quantum-genesis", "sandpile-utac"]


class GroundingRecommender:
    """Recommends grounding actions based on the current risk level."""

    def recommend(self, path: SemanticPath, risk_level: str) -> list[str]:
        """Return a list of grounding recommendations for *path*."""
        if risk_level == "safe":
            return ["No grounding required."]
        if risk_level == "moderate":
            return [
                f"Inject top Sigillin anchors: {path.sigillin_ids[:3]}",
                "Set Q4 state to the most coherent node on the path.",
                "Monitor dΓ/dt during conversation.",
            ]
        if risk_level == "high_risk":
            cross = self._find_resilient_cross_domains(path.domain)
            return [
                "Seek an alternative path with higher Γ_sem.",
                f"Cross-domain grounding from: {cross}",
                "Consider reducing task complexity for this domain.",
            ]
        # critical
        alts = self._alternative_paths(path)
        return [
            "WARNING: DO NOT INITIALISE LLM on this path.",
            "Semantic domain is near a phase boundary.",
            f"Suggested alternatives: {alts}",
        ]

    @staticmethod
    def _find_resilient_cross_domains(domain: str) -> list[str]:
        """Return domains with high Ρ suitable as grounding sources."""
        _ = domain  # future: filter out same domain
        return _HIGH_RESILIENCE_DOMAINS

    @staticmethod
    def _alternative_paths(path: SemanticPath) -> list[str]:
        """Suggest alternative path identifiers for the same topic."""
        return [f"alt_path_{path.topic}_v2", f"alt_path_{path.topic}_v3"]
