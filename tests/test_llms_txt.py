"""Tests for LLMSTxtExporter."""

from scope_resilience.llms_txt import LLMSTxtExporter
from scope_resilience.semantic_path import SemanticPath


def _make_path() -> SemanticPath:
    return SemanticPath(
        topic="quantum decoherence",
        sigillin_ids=["q1", "q2", "q3"],
        q4_transitions=[("q1", "q2"), ("q2", "q3")],
        gamma_sem=0.55,
        rho_sem=0.72,
        domain="physics_dense",
        crep_components={"C": 0.8, "R": 0.7, "E": 0.5, "P": 0.6},
        risk_level="safe",
        grounding_recommendations=["No grounding required."],
    )


def test_export_contains_topic():
    txt = LLMSTxtExporter().export(_make_path())
    assert "quantum decoherence" in txt


def test_export_contains_rho():
    txt = LLMSTxtExporter().export(_make_path())
    assert "0.720" in txt


def test_export_contains_sigillin_ids():
    txt = LLMSTxtExporter().export(_make_path())
    assert "[Sigillin:q1]" in txt
    assert "[Sigillin:q3]" in txt


def test_export_contains_transitions():
    txt = LLMSTxtExporter().export(_make_path())
    assert "q1 --> q2" in txt


def test_export_contains_crep_components():
    txt = LLMSTxtExporter().export(_make_path())
    assert "C=0.80" in txt


def test_export_contains_grounding_section():
    txt = LLMSTxtExporter().export(_make_path())
    assert "## Grounding Recommendations" in txt
