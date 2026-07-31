"""Real, content-based semantic similarity backends for SemanticCREP.

Motivation
----------
``SemanticCREP.compute()`` (the original, still-supported entry point)
never receives actual text content — only opaque ``sigillin_ids`` and
``q4_transitions`` — so its C/R/E components are structural proxies
(duplicate-id counting, edge counting) rather than a measurement of
whether the underlying semantic content actually drifts or contradicts.
This is the scope-resilience side of the same gap genesis-tip found and
fixed in ``metrics/llm_judge.py``: a regex/structural stand-in that
cannot see genuine semantic change, because it never looks at real text.

This module provides that missing real measurement as an OPTIONAL,
pluggable callback — mirroring genesis-tip's ``JudgeCallable`` design.
``SemanticCREP.compute_from_content()`` (semantic_crep.py) uses a
``SimilarityCallable`` only when the caller actually supplies real
segment text; the original structural ``compute()`` is untouched and
remains the default.

Two concrete implementations, with different tradeoffs:

``tfidf_similarity`` — lexical-overlap similarity via scikit-learn's
TF-IDF vectoriser + cosine similarity. Deterministic, offline, no
network, no rate limits, runs in CI. Real in the sense that it reads
actual text content (unlike the structural proxy), but it is a lexical
measure, not deep semantic understanding — two sentences that are
synonymous but share no words will score low. Use this as the safe
default.

``grok_similarity`` — deeper semantic judgment via the ``grok`` CLI
(same backend and same hard-won lessons as genesis-tip's ``grok_judge``:
60s timeout, opt-in ``min_interval_seconds`` pacing for the free tier's
per-minute rate limit, privacy-safe error messages that do not leak the
judged text). Requires an authenticated ``grok`` CLI and is a real,
metered network call — use when lexical overlap is not a good enough
proxy for the judgment being made.

Verified manually (2026-07-31), real calls, no mocking - two paraphrases
of the same AMOC fact in different words:
``tfidf_similarity`` scored them only 0.088 (little literal word overlap)
while ``grok_similarity`` scored them 0.97 (correctly recognises they
say the same thing). Both scored a genuinely unrelated pair at 0.0. This
is the concrete case for keeping both: TF-IDF is a real but limited
lexical measure that under-scores genuine paraphrase-level similarity;
grok_similarity is closer to actual semantic judgment but costs a real,
rate-limited network call. Not part of the automated test suite for the
same reason as genesis-tip's grok_judge (no grok CLI/auth in CI).
"""

from __future__ import annotations

import re
import subprocess
import time
from collections.abc import Callable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SimilarityCallable = Callable[[str, str], float]
"""similarity(text_a, text_b) -> float in [0.0, 1.0].

1.0 = semantically identical/equivalent, 0.0 = unrelated or contradictory.
"""

_last_grok_call_at: float | None = None


class SimilarityError(RuntimeError):
    """Raised when a similarity backend fails or returns an unparseable answer."""


def tfidf_similarity(text_a: str, text_b: str) -> float:
    """Real, offline, content-based similarity via TF-IDF cosine similarity.

    Fits the vectoriser on just the two supplied texts (no external corpus
    needed), so this works standalone and deterministically. Identical
    text returns 1.0; texts sharing no vocabulary return 0.0.

    Empty-string inputs return 0.0 rather than raising - an empty segment
    has no content to be similar to anything, which is the conservative
    (lowest-coherence) answer for a drift/consistency measurement.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0
    if text_a.strip() == text_b.strip():
        return 1.0
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    try:
        matrix = vectorizer.fit_transform([text_a, text_b])
    except ValueError:
        # Both texts are pure stop-words/empty-after-tokenising - no shared
        # vocabulary to compare, i.e. no measurable similarity.
        return 0.0
    similarity = cosine_similarity(matrix[0], matrix[1])[0, 0]
    return float(max(0.0, min(1.0, similarity)))


_SIMILARITY_PROMPT_TEMPLATE = """You are a strict semantic similarity scorer. \
Answer with exactly one number from 0 to 100, nothing else. \
0 means completely unrelated or contradictory in meaning. \
100 means semantically equivalent.

Statement A: {text_a}

Statement B: {text_b}"""


def grok_similarity(
    text_a: str,
    text_b: str,
    *,
    model: str | None = None,
    timeout: float = 60.0,
    min_interval_seconds: float = 0.0,
) -> float:
    """Ask the ``grok`` CLI (single-turn, headless) to score semantic similarity.

    Requires the ``grok`` CLI to be installed and authenticated - not
    checked here, a failure surfaces as ``SimilarityError`` with the
    underlying cause.

    Same rate-limit/timeout lessons as genesis-tip's ``grok_judge``
    (see that module's docstring): 60s default timeout (real answers can
    run long), and an opt-in ``min_interval_seconds`` to pace sequential
    calls under the free "Grok Build" tier's per-minute limit.
    """
    global _last_grok_call_at
    if min_interval_seconds > 0 and _last_grok_call_at is not None:
        elapsed = time.monotonic() - _last_grok_call_at
        remaining = min_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    prompt = _SIMILARITY_PROMPT_TEMPLATE.format(text_a=text_a, text_b=text_b)
    cmd = ["grok", "-p", prompt]
    if model:
        cmd += ["-m", model]

    _last_grok_call_at = time.monotonic()
    try:
        proc = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        # Deliberately do not include str(exc)/exc.cmd: TimeoutExpired's
        # default repr embeds the full command list, i.e. the judged
        # text_a/text_b verbatim - would leak into any log/JSON that
        # records this message. Report only the (non-sensitive) timeout
        # value instead.
        raise SimilarityError(f"grok CLI timed out after {timeout}s") from exc
    except OSError as exc:
        raise SimilarityError(f"grok CLI invocation failed: {exc}") from exc

    if proc.returncode != 0:
        raise SimilarityError(f"grok CLI exited {proc.returncode}: {proc.stderr.strip()}")

    return _parse_similarity_score(proc.stdout)


def _parse_similarity_score(raw: str) -> float:
    match = re.search(r"\b(100|[0-9]{1,2})\b", raw.strip())
    if not match:
        raise SimilarityError(f"could not parse a 0-100 score from output: {raw!r}")
    return max(0.0, min(1.0, int(match.group(1)) / 100.0))
