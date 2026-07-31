"""SemanticCREP — CREP tensor computation for semantic paths.

C_sem = semantic consistency  = 1 − (contradictory_edges / total_edges)
R_sem = semantic resonance    = proximity to verified ground-truth paths
E_sem = semantic emergence    = normalised surprisal of path connections
P_sem = path richness         = tanh(n_edges · mean_weight / ref_density)

Γ_sem = (C · R · E · P)^(1/4)   [standard diamond CREP formula]

``compute()`` is the original entry point: without a live Sigillin store
(or any real text at all - it only ever receives opaque ids/transitions)
the components are estimated from structural properties alone. This is a
proxy, not a measurement of real semantic drift or contradiction - see
``compute_from_content()`` below and ``semantic_similarity.py`` for the
real, content-based alternative, added once real text is available to
the caller. ``compute()`` is kept exactly as-is for backward
compatibility with existing callers that only have ids/transitions.
"""

from __future__ import annotations

import math
import warnings

from scope_resilience.constants import DOMAIN_CONFIG, GAMMA_MAX, SIGMA
from scope_resilience.semantic_similarity import SimilarityCallable, tfidf_similarity


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
        return float(config["r_sem"])  # config values are float

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

    def compute_from_content(
        self,
        segment_texts: list[str],
        reference_texts: list[str] | None = None,
        similarity_fn: SimilarityCallable = tfidf_similarity,
    ) -> dict[str, float]:
        """Real, content-based CREP components {C, R, E, P} for a semantic path.

        Unlike ``compute()``, this reads the actual text of each path
        segment (``segment_texts``, one string per sigillin/step, in
        path order) via ``similarity_fn`` - so a path that visibly drifts
        or contradicts itself in its real content produces a lower C_sem,
        instead of being invisible to a purely structural id/edge count.

        C — consistency: mean pairwise similarity between CONSECUTIVE
            segments. High similarity between adjacent real segments =
            a coherent path; a segment that abruptly contradicts its
            predecessor pulls this down - the real analogue of
            "1 - contradictory_edges/total_edges".
        R — resonance: mean best-match similarity of each segment against
            ``reference_texts`` (e.g. verified ground-truth/Sigillin
            content), i.e. real "proximity to verified ground-truth
            paths". Falls back to the domain-level structural default
            (``get_domain_r``, via the caller) when no reference text is
            available - there is no way to measure proximity to a
            ground truth that was never supplied.
        E — emergence: 1 - (similarity of each new segment to the most
            similar prior segment), averaged. A segment near-identical
            to something already seen is not surprising (low E); one
            that introduces genuinely new content relative to the whole
            path so far is more emergent (high E). This is a real
            surprisal proxy, unlike the old edge-count heuristic.
        P — richness: kept structural (total content volume), since
            "richness" is a breadth/count property by definition, not a
            per-pair similarity judgement.

        Args:
            segment_texts: real text content, one entry per path segment,
                in path order. Needs at least 1 entry; needs at least 2
                for C/E to be meaningful (both default to a neutral 0.5
                for a single-segment path, mirroring compute()'s n=1
                defaults).
            reference_texts: optional real ground-truth/reference text to
                compute R against. When omitted, R is returned as None so
                callers can fall back to ``get_domain_r()`` instead of
                silently treating "no reference" as "zero resonance".
            similarity_fn: any ``SimilarityCallable`` - defaults to the
                offline, network-free ``tfidf_similarity``. Pass
                ``grok_similarity`` (semantic_similarity.py) for deeper
                semantic judgment at the cost of a real network call.
        """
        n = len(segment_texts)
        if n == 0:
            result: dict[str, float] = {"C": 0.5, "E": 0.5, "P": 0.2}
            if reference_texts:
                result["R"] = 0.5
            return result

        if n < 2:
            c_sem = 0.5
            e_sem = 0.5
        else:
            pairwise = [similarity_fn(segment_texts[i], segment_texts[i + 1]) for i in range(n - 1)]
            c_sem = sum(pairwise) / len(pairwise)

            surprisals = [
                1.0 - max(similarity_fn(segment_texts[i], segment_texts[j]) for j in range(i))
                for i in range(1, n)
            ]
            e_sem = sum(surprisals) / len(surprisals)

        r_sem: float | None
        if reference_texts:
            best_matches = [
                max(similarity_fn(seg, ref) for ref in reference_texts) for seg in segment_texts
            ]
            r_sem = sum(best_matches) / len(best_matches)
        else:
            r_sem = None

        total_chars = sum(len(s) for s in segment_texts)
        p_sem = math.tanh(total_chars / 500.0)

        result: dict[str, float] = {
            "C": float(max(0.0, min(1.0, c_sem))),
            "E": float(max(0.0, min(1.0, e_sem))),
            "P": float(max(0.0, min(1.0, p_sem))),
        }
        if r_sem is not None:
            result["R"] = float(max(0.0, min(1.0, r_sem)))
        return result

    def gamma_sem(self, crep_components: dict[str, float]) -> float:
        """Γ_sem = (C·R·E·P)^(1/4) — standard CREP formula."""
        product = (
            crep_components["C"]
            * crep_components["R"]
            * crep_components["E"]
            * crep_components["P"]
        )
        return float(product**0.25) if product > 0 else 0.0
