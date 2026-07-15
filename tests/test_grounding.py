"""Tests for GroundingRecommender."""

import pytest

from scope_resilience.grounding import GroundingRecommender
from scope_resilience.semantic_path import SemanticPath


@pytest.fixture
def grounder():
    return GroundingRecommender()


def _make_path(risk_level: str, rho: float = 0.5) -> SemanticPath:
    return SemanticPath(
        topic="test-topic",
        sigillin_ids=["s1", "s2"],
        q4_transitions=[("s1", "s2")],
        gamma_sem=0.4,
        rho_sem=rho,
        domain="general",
        crep_components={"C": 0.5, "R": 0.5, "E": 0.5, "P": 0.5},
        risk_level=risk_level,
    )


def test_safe_returns_no_grounding(grounder):
    recs = grounder.recommend(_make_path("safe"), "safe")
    assert recs == ["No grounding required."]


def test_moderate_mentions_sigillin(grounder):
    recs = grounder.recommend(_make_path("moderate"), "moderate")
    assert any("Sigillin" in r for r in recs)


def test_high_risk_mentions_alternative(grounder):
    recs = grounder.recommend(_make_path("high_risk"), "high_risk")
    assert any("alternative" in r.lower() for r in recs)


def test_critical_contains_warning(grounder):
    recs = grounder.recommend(_make_path("critical", rho=0.03), "critical")
    assert any("WARNING" in r or "NOT" in r for r in recs)


def test_critical_suggests_alternatives(grounder):
    recs = grounder.recommend(_make_path("critical"), "critical")
    assert any("alt_path_test-topic" in r for r in recs)
