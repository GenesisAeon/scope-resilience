"""Tests for the real, content-based semantic similarity backends.

tfidf_similarity is tested for real - deterministic, offline, no mocking
needed. grok_similarity's subprocess plumbing is tested against a mocked
subprocess.run, mirroring genesis-tip's test_llm_judge.py: real end-to-end
grok CLI calls are verified manually, not part of the automated suite,
since CI has neither the grok CLI installed nor an authenticated account.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from scope_resilience.semantic_similarity import (
    SimilarityError,
    _parse_similarity_score,
    grok_similarity,
    tfidf_similarity,
)


class TestTfidfSimilarity:
    def test_identical_text_scores_one(self) -> None:
        assert tfidf_similarity("The AMOC is weakening.", "The AMOC is weakening.") == 1.0

    def test_disjoint_vocabulary_scores_low(self) -> None:
        score = tfidf_similarity(
            "The Atlantic meridional overturning circulation is slowing.",
            "Bananas are a good source of potassium.",
        )
        assert score < 0.2

    def test_partial_overlap_is_between_extremes(self) -> None:
        score = tfidf_similarity(
            "The AMOC tipping point is approaching in the North Atlantic.",
            "The AMOC collapse risk is rising in the North Atlantic ocean.",
        )
        assert 0.2 < score < 1.0

    def test_empty_string_returns_zero(self) -> None:
        assert tfidf_similarity("", "something") == 0.0
        assert tfidf_similarity("something", "   ") == 0.0
        assert tfidf_similarity("", "") == 0.0

    def test_pure_stopword_texts_do_not_raise(self) -> None:
        # sklearn's default English stop-word-free TfidfVectorizer keeps
        # these as vocabulary, but this exercises the ValueError fallback
        # path defensively for any text that tokenises to nothing shared.
        score = tfidf_similarity("a a a", "b b b")
        assert 0.0 <= score <= 1.0

    def test_returns_float_in_unit_interval(self) -> None:
        score = tfidf_similarity("some real content here", "other real content there")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


class TestParseSimilarityScore:
    def test_plain_number(self) -> None:
        assert _parse_similarity_score("87") == 0.87

    def test_hundred(self) -> None:
        assert _parse_similarity_score("100") == 1.0

    def test_embedded_in_sentence(self) -> None:
        assert _parse_similarity_score("I would say about 42 out of 100.") == 0.42

    def test_unparseable_raises(self) -> None:
        with pytest.raises(SimilarityError):
            _parse_similarity_score("I cannot quantify this.")


class TestGrokSimilaritySubprocessPlumbing:
    @patch("scope_resilience.semantic_similarity.subprocess.run")
    def test_successful_call(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="73\n", stderr="")
        result = grok_similarity("The meeting was Monday.", "The meeting was postponed.")
        assert result == 0.73
        args = mock_run.call_args[0][0]
        assert args[0] == "grok"
        assert args[1] == "-p"

    @patch("scope_resilience.semantic_similarity.subprocess.run")
    def test_nonzero_exit_raises(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="not logged in")
        with pytest.raises(SimilarityError):
            grok_similarity("a", "b")

    @patch("scope_resilience.semantic_similarity.time.sleep")
    @patch("scope_resilience.semantic_similarity.subprocess.run")
    def test_min_interval_throttles_second_call(
        self, mock_run: MagicMock, mock_sleep: MagicMock
    ) -> None:
        import scope_resilience.semantic_similarity as sim_module

        sim_module._last_grok_call_at = None
        mock_run.return_value = MagicMock(returncode=0, stdout="50\n", stderr="")

        grok_similarity("a", "b", min_interval_seconds=30.0)
        mock_sleep.assert_not_called()

        grok_similarity("c", "d", min_interval_seconds=30.0)
        mock_sleep.assert_called_once()
        waited = mock_sleep.call_args[0][0]
        assert 0 < waited <= 30.0

    @patch("scope_resilience.semantic_similarity.subprocess.run")
    def test_missing_binary_raises_similarity_error(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = FileNotFoundError("grok not found")
        with pytest.raises(SimilarityError):
            grok_similarity("a", "b")

    @patch("scope_resilience.semantic_similarity.subprocess.run")
    def test_timeout_error_does_not_leak_judged_text(self, mock_run: MagicMock) -> None:
        secret_text = "SENSITIVE_MARKER_e8f3a1 should never appear in the error"
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["grok", "-p", secret_text], timeout=60.0
        )
        with pytest.raises(SimilarityError) as excinfo:
            grok_similarity(secret_text, "b")
        assert "SENSITIVE_MARKER_e8f3a1" not in str(excinfo.value)
