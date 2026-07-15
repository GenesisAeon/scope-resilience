"""LLMSTxtExporter — llms.txt export for semantic paths.

llms.txt is a machine-readable knowledge-space summary for LLM consumption
(analogous to robots.txt). This is the first implementation in GenesisAeon.
"""

from __future__ import annotations

from scope_resilience.semantic_path import SemanticPath


class LLMSTxtExporter:
    """Exports a SemanticPath as an llms.txt-compliant string."""

    def export(self, path: SemanticPath) -> str:
        """Return an llms.txt-formatted representation of *path*."""
        crep = path.crep_components
        lines: list[str] = [
            f"# GenesisAeon Semantic Map — {path.topic}",
            f"# Domain: {path.domain}",
            f"# Resilience: rho_sem={path.rho_sem:.3f} ({path.risk_level})",
            f"# CREP: Gamma={path.gamma_sem:.3f} "
            f"(C={crep.get('C', 0.0):.2f}, "
            f"R={crep.get('R', 0.0):.2f}, "
            f"E={crep.get('E', 0.0):.2f}, "
            f"P={crep.get('P', 0.0):.2f})",
            "",
            "## Core Semantic Path",
        ]
        for i, sig_id in enumerate(path.sigillin_ids, start=1):
            lines.append(f"  {i}. [Sigillin:{sig_id}]")

        lines.extend(["", "## Q4 Transitions"])
        for src, dst in path.q4_transitions:
            lines.append(f"  {src} --> {dst}")

        lines.extend(["", "## Grounding Recommendations"])
        for rec in path.grounding_recommendations:
            lines.append(f"  - {rec}")

        return "\n".join(lines)
