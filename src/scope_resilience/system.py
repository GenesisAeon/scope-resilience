"""ScopeResilience — Diamond Interface main class for scope-resilience.

Package 41 of the GenesisAeon ecosystem. Implements all six Diamond methods
(five standard + get_resilience_state) using the semantic UTAC mapping.
"""

from __future__ import annotations

from typing import Any

from diamond_setup.protocol import (
    CREPState,
    DiamondPackage,
    UTACState,
    ZenodoCreator,
    ZenodoRecord,
)
from scope_resilience.grounding import GroundingRecommender
from scope_resilience.hallucination_risk import HallucinationRisk
from scope_resilience.llms_txt import LLMSTxtExporter
from scope_resilience.path_monitor import PathDriftMonitor
from scope_resilience.semantic_crep import SemanticCREP
from scope_resilience.semantic_path import SemanticPath
from scope_resilience.semantic_utac import SemanticUTAC


class ScopeResilience(DiamondPackage):
    """GenesisAeon Diamond interface for semantic hallucination resilience.

    Maps the UTAC system-resilience formalism onto LLM semantic paths,
    providing a formal pre-flight risk assessment (Ρ_sem) before LLM
    initialisation on a semantic topic path.

    Usage::

        sr = ScopeResilience(domain="physics_dense")
        result = sr.run_cycle(
            topic="AMOC tipping point",
            sigillin_ids=["s1", "s2", "s3"],
            q4_transitions=[("s1", "s2"), ("s2", "s3")],
        )
        print(result["rho_sem"], result["risk_level"])
        path = sr.get_semantic_path("AMOC tipping point")
    """

    def __init__(self, domain: str = "general") -> None:
        super().__init__()
        self.domain = domain
        self._crep = SemanticCREP()
        self._risk = HallucinationRisk()
        self._utac = SemanticUTAC()
        self._grounder = GroundingRecommender()
        self._monitor = PathDriftMonitor()
        self._exporter = LLMSTxtExporter()
        self._current_path: SemanticPath | None = None
        # Pending args for _run_cycle (set by run_cycle override)
        self._pending_topic: str = "default"
        self._pending_ids: list[str] = []
        self._pending_trans: list[tuple[str, str]] = []

    # ── DiamondPackage hooks ─────────────────────────────────────────────────

    def _run_cycle(self) -> dict[str, Any]:
        """Compute hallucination resilience for a semantic path."""
        topic = self._pending_topic
        sigillin_ids = self._pending_ids
        q4_transitions = self._pending_trans

        crep_comps = self._crep.compute(sigillin_ids, q4_transitions)
        gamma_sem = self._crep.gamma_sem(crep_comps)
        d_gamma = self._monitor.update(gamma_sem)
        rho_sem = self._risk.compute_rho(gamma_sem, d_gamma_dt=d_gamma)
        risk_level, _ = self._risk.classify_risk(rho_sem)
        recs = self._grounder.recommend(
            SemanticPath(
                topic=topic,
                sigillin_ids=sigillin_ids,
                q4_transitions=q4_transitions,
                gamma_sem=gamma_sem,
                rho_sem=rho_sem,
                domain=self.domain,
                crep_components=crep_comps,
                risk_level=risk_level,
                grounding_recommendations=[],
            ),
            risk_level,
        )
        self._current_path = SemanticPath(
            topic=topic,
            sigillin_ids=sigillin_ids,
            q4_transitions=q4_transitions,
            gamma_sem=gamma_sem,
            rho_sem=rho_sem,
            domain=self.domain,
            crep_components=crep_comps,
            risk_level=risk_level,
            grounding_recommendations=recs,
        )
        return {
            "topic": topic,
            "gamma_sem": gamma_sem,
            "rho_sem": rho_sem,
            "risk_level": risk_level,
            "d_gamma_dt": d_gamma,
            "needs_regrounding": self._monitor.needs_regrounding(),
        }

    def _build_crep_state(self) -> CREPState:
        assert self._current_path is not None
        c = self._current_path
        return CREPState(
            C=c.crep_components["C"],
            R=c.crep_components["R"],
            E=c.crep_components["E"],
            P=c.crep_components["P"],
            Gamma=c.gamma_sem,
        )

    def _build_utac_state(self) -> UTACState:
        assert self._current_path is not None
        return UTACState(
            **self._utac.state_dict(
                self._current_path.rho_sem,
                self._current_path.gamma_sem,
            )
        )

    def _build_phase_events(self) -> list[dict[str, Any]]:
        if self._current_path and self._current_path.risk_level in (
            "high_risk",
            "critical",
        ):
            return [
                {
                    "type": "hallucination_risk",
                    "topic": self._current_path.topic,
                    "rho_sem": self._current_path.rho_sem,
                    "risk_level": self._current_path.risk_level,
                }
            ]
        return []

    def _build_zenodo_record(self) -> ZenodoRecord:
        return ZenodoRecord(
            title=(
                "scope-resilience: Hallucination resilience mapping "
                "for LLM semantic paths"
            ),
            description=(
                "Extends genesis-scope with hallucination resilience "
                "quantification (rho_sem) for semantic paths. Maps UTAC "
                "system dynamics to LLM coherence maintenance, providing "
                "a pre-flight risk assessment before LLM initialisation on "
                "a semantic path."
            ),
            creators=[ZenodoCreator(name="Römer, Johann", affiliation="MOR Research Collective")],
        )

    # ── Extended public API ──────────────────────────────────────────────────

    def run_cycle(  # type: ignore[override]
        self,
        topic: str = "default",
        sigillin_ids: list[str] | None = None,
        q4_transitions: list[tuple[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Override to expose topic/sigillin_ids/q4_transitions as keyword args."""
        self._pending_topic = topic
        self._pending_ids = sigillin_ids or []
        self._pending_trans = q4_transitions or []
        return super().run_cycle()

    def get_resilience_state(self) -> dict[str, Any]:
        """6th Diamond method — semantic resilience details.

        Returns rho_sem, gamma_sem, risk_level, current drift rate,
        regrounding flag, and grounding recommendations.
        """
        if self._current_path is None:
            return {"rho_sem": None, "risk_level": "unknown", "implemented": True}
        p = self._current_path
        drift = self._monitor.current_drift()
        return {
            "rho_sem": p.rho_sem,
            "gamma_sem": p.gamma_sem,
            "risk_level": p.risk_level,
            "d_gamma_dt": drift,
            "needs_regrounding": self._monitor.needs_regrounding(),
            "grounding_recs": p.grounding_recommendations,
            "implemented": True,
        }

    def get_semantic_path(
        self, topic: str, min_rho: float = 0.4
    ) -> SemanticPath | None:
        """Return the best semantic path for *topic* with Ρ_sem >= min_rho.

        If no path meets the threshold the best available path is returned
        with a warning attached in grounding_recommendations.
        """
        self.run_cycle(topic)
        path = self._current_path
        if path is None:
            return None
        if path.rho_sem < min_rho:
            path.grounding_recommendations.insert(
                0,
                f"WARNING: Ρ_sem={path.rho_sem:.3f} < min_rho={min_rho}. "
                "Path may not be safe for LLM initialisation.",
            )
        return path

    def to_llms_txt(self, topic: str | None = None) -> str:
        """Return an llms.txt export of the current (or requested) path."""
        if self._current_path is None:
            if topic is not None:
                self.run_cycle(topic)
            else:
                return "# No semantic path computed yet."
        assert self._current_path is not None
        return self._exporter.export(self._current_path)
