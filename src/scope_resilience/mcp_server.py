"""MCP server for scope-resilience (optional, requires fastmcp).

Exposes get_semantic_path(), assess_hallucination_risk(), export_llms_txt(),
and list_domain_resilience() as MCP tools for Claude Code / Claude Desktop.

Install::

    pip install "scope-resilience[mcp]"
    scope-resilience serve --port 8765
"""

from __future__ import annotations

try:
    from fastmcp import FastMCP

    _HAS_MCP = True
except ImportError:
    _HAS_MCP = False

if _HAS_MCP:
    from scope_resilience.system import ScopeResilience

    mcp = FastMCP(
        name="scope-resilience",
        version="1.0.0",
        description=(
            "GenesisAeon semantic path resilience server. "
            "Provides hallucination risk assessment and semantic "
            "path quality metrics for LLM initialisation."
        ),
    )

    @mcp.tool()
    def get_semantic_path(
        topic: str, min_rho: float = 0.4, domain: str = "general"
    ) -> dict:
        """Return a semantic path for LLM initialisation with resilience metrics."""
        sr = ScopeResilience(domain=domain)
        path = sr.get_semantic_path(topic, min_rho=min_rho)
        if path is None:
            return {"error": "No path found"}
        return {
            "topic": path.topic,
            "domain": path.domain,
            "gamma_sem": path.gamma_sem,
            "rho_sem": path.rho_sem,
            "risk_level": path.risk_level,
            "sigillin_anchors": path.sigillin_ids,
            "q4_transitions": [f"{s}-->{d}" for s, d in path.q4_transitions],
            "grounding_recommendations": path.grounding_recommendations,
            "llms_txt": sr.to_llms_txt(),
        }

    @mcp.tool()
    def assess_hallucination_risk(topic: str, domain: str = "general") -> dict:
        """Quickly assess hallucination risk for a topic."""
        sr = ScopeResilience(domain=domain)
        result = sr.run_cycle(topic)
        return {
            "topic": topic,
            "rho_sem": result["rho_sem"],
            "risk_level": result["risk_level"],
            "safe_to_initialize": result["rho_sem"] > 0.4,
            "needs_grounding": result["rho_sem"] <= 0.7,
        }

    @mcp.tool()
    def export_llms_txt(topic: str, domain: str = "general") -> str:
        """Export a semantic path as llms.txt for system-prompt injection."""
        sr = ScopeResilience(domain=domain)
        sr.run_cycle(topic)
        return sr.to_llms_txt(topic)

    @mcp.tool()
    def list_domain_resilience() -> dict:
        """Return calibrated resilience values for all GenesisAeon domains."""
        return {
            "quantum-genesis":  {"gamma": 0.050, "rho": 0.90, "safe": True},
            "sandpile-utac":    {"gamma": 0.296, "rho": 0.75, "safe": True},
            "amoc-utac":        {"gamma": 0.251, "rho": 0.65, "safe": True},
            "amazon-utac":      {"gamma": 0.116, "rho": 0.70, "safe": True},
            "seismic-utac":     {"gamma": 0.200, "rho": 0.70, "safe": True},
            "neural-avalanche":  {"gamma": 0.251, "rho": 0.65, "safe": True},
            "theta-resonance":   {"gamma": 0.251, "rho": 0.65, "safe": True},
            "arctic-era5":       {"gamma": 0.920, "rho": 0.05, "safe": False},
            "solar-flare-utac":  {"gamma": 0.014, "rho": 0.85, "safe": True},
        }

    def serve(port: int = 8765) -> None:
        """Start the MCP server."""
        mcp.run(transport="streamable-http", port=port)
