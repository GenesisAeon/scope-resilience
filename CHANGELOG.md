# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.2] - 2026-09-15

### Fixed (test suite only, no behavior change)
- Removed `tests/test_preset.py`, `tests/test_validator.py`,
  `tests/test_protocol.py`: unmodified copies of `diamond-setup`'s own
  test suite, exercising only `diamond_setup` internals, never
  `scope-resilience` code.
- `tests/test_cli.py` replaced with real tests against
  `scope_resilience/_cli.py` (`serve`/`assess`/`export-llms-txt`/`path`),
  previously a copy of diamond-setup's CLI tests with 0% actual coverage
  of this package's own CLI.

## [1.0.1] - 2026-09-15

### Fixed (documentation only, no behavior change)
- `semantic_utac.py`: removed a false "Fixpoint" claim. The module and
  class docstrings previously stated `H*_sem = K_sem · tanh(σ · Γ_sem)`
  was the fixpoint of the stated logistic ODE `dH_sem/dt = r·H_sem·
  (1-H_sem/K_sem)·tanh(σ·Γ_sem)`. Verified numerically (2026-09-15) that
  this is false: the ODE's actual nonzero fixpoint is `H=K_sem`,
  independent of Γ. `H*_sem` is now documented as an independently
  defined coherence reference/threshold used for hallucination-vs-
  coherence regime classification, not a derived ODE fixpoint; the ODE
  itself is now labeled as motivating/illustrative context, since
  `attractor()` computes `K_sem·tanh(σΓ_sem)` directly and algebraically
  without integrating any ODE. No change to `attractor()`,
  `is_hallucination_regime()`, or `state_dict()` — 144/145 tests pass
  before and after (one pre-existing, unrelated CLI version-string
  failure shared with `resilience-core`, tracked in
  `crep-utac-afet-formalism/FOLLOWUP_TICKETS.md`).

## [1.0.0] - 2026-07-16
### Added
- `ScopeResilience` — Diamond Interface main class implementing all 6
  GenesisAeon Diamond methods, including `get_resilience_state()`.
- `HallucinationRisk` — Ρ_sem computation and risk classification
  (`safe` / `moderate` / `high_risk` / `critical`).
- `SemanticCREP` — CREP tensor (C, R, E, P) and Γ_sem computation for a
  semantic path, plus `calibrate_r()` for closed-form r_sem inversion from
  observed Ρ and Γ.
- `SemanticUTAC` — H_sem coherence-attractor mapping of UTAC dynamics onto
  LLM semantic coherence.
- `DomainProfile` — per-domain r_sem fingerprint, with `from_atlas_target()`
  for analytical estimation from physical UTAC-Atlas reference points.
- `PathDriftMonitor` — sliding-window dΓ_sem/dt tracking with
  re-grounding triggers.
- `GroundingRecommender` — risk-level-driven grounding recommendations,
  including cross-domain grounding from high-resilience domains.
- `LLMSTxtExporter` — first GenesisAeon implementation of `llms.txt` export
  for semantic paths.
- Optional MCP server (`scope-resilience[mcp]`) exposing `get_semantic_path`,
  `assess_hallucination_risk`, `export_llms_txt`, and
  `list_domain_resilience` as tools for Claude Code / Claude Desktop.
- CLI (`scope-resilience`): `assess`, `path`, `export-llms-txt`, `serve`.
- Initial domain calibration table (`physics_dense`, `sparse_fringe`,
  `curated_graph`, `general`, `oceanography`, `quantum`) — all `r_sem`
  values marked as a pre-registered hypothesis pending TIP/P49 calibration.
