# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
