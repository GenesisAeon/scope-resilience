# scope-resilience — P41

**Hallucination resilience mapping for LLM semantic paths**
GenesisAeon Package 41 · MOR Research Collective · Johann Römer

[![CI](https://github.com/GenesisAeon/scope-resilience/actions/workflows/ci.yml/badge.svg)](https://github.com/GenesisAeon/scope-resilience/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What is Ρ_sem?

`scope-resilience` extends [`genesis-scope`](https://github.com/GenesisAeon/genesis-scope) with a formal **pre-flight hallucination risk assessment** for LLMs: before initialising a model on a semantic topic path, compute how resilient that path is against semantic drift.

```
Ρ_sem(P, t) = r_sem · tanh²(σ · Γ_sem(P))
            · (1 − Γ_sem(P)/Γ_max)
            · (1 − |dΓ_sem/dt| / Γ̇_critical)
```

This is the same UTAC fixpoint-resilience formalism as [`resilience-core`](https://github.com/GenesisAeon/resilience-core) (P40), applied to a new domain: instead of physical tipping systems (AMOC, Arctic ice), the "system" is an LLM's coherence on a semantic path, and Γ_sem is derived from a CREP tensor over that path's Sigillin anchors and Q4 transitions.

| Factor | Meaning |
|--------|---------|
| `r_sem` | Domain-specific self-correction rate — the one free parameter per knowledge domain |
| `tanh²(σ·Γ_sem)` | Intrinsic pull toward the semantic coherence attractor |
| `1 − Γ_sem/Γ_max` | Criticality margin before the path nears a semantic phase boundary |
| `1 − \|dΓ_sem/dt\| / Γ̇_critical` | Live drift penalty — punishes paths that are destabilising in real time |

**Ρ_sem → 0** means the path is near a semantic phase boundary *and* actively drifting — the regime where hallucination risk is highest and LLM initialisation should be avoided.

---

## Installation

```bash
pip install scope-resilience
# or with the MCP server
pip install "scope-resilience[mcp]"
```

## Quick Start

```python
from scope_resilience import ScopeResilience

sr = ScopeResilience(domain="physics_dense")
result = sr.run_cycle(
    topic="AMOC tipping point",
    sigillin_ids=["s1", "s2", "s3"],
    q4_transitions=[("s1", "s2"), ("s2", "s3")],
)
print(result["rho_sem"], result["risk_level"])

# Best available semantic path for a topic, with a minimum resilience bar
path = sr.get_semantic_path("AMOC tipping point", min_rho=0.4)
print(path.risk_level, path.grounding_recommendations)

# Export as llms.txt for system-prompt injection
print(sr.to_llms_txt())
```

CLI equivalent:

```bash
scope-resilience assess "AMOC tipping point" --domain physics_dense
scope-resilience path "AMOC tipping point" --min-rho 0.4
scope-resilience export-llms-txt "AMOC tipping point"
```

## Risk Levels

| Ρ_sem range | Level | Meaning |
|---|---|---|
| 0.70 – 1.00 | `safe` | Path is semantically stable. Proceed. |
| 0.40 – 0.70 | `moderate` | Moderate drift risk. Inject grounding anchors. |
| 0.10 – 0.40 | `high_risk` | High hallucination risk. Consider an alternative path. |
| 0.00 – 0.10 | `critical` | Near a semantic phase boundary. Do not initialise on this path. |

When risk rises, `GroundingRecommender` suggests concrete mitigations: injecting Sigillin anchors, pulling in cross-domain grounding from high-resilience domains (`quantum-genesis`, `sandpile-utac`), or switching to an alternative path entirely.

## Domain Calibration

`r_sem` is the only free parameter per knowledge domain. Structural values (σ, σ_Φ, Γ_max, Γ̇_critical) are universal and shared with `resilience-core`.

| Domain | r_sem | Status | Source |
|---|---|---|---|
| `curated_graph` | 0.90 | estimate | pending TIP/P49 |
| `physics_dense` | 0.80 | estimate | pending TIP/P49 |
| `quantum` | 0.85 | estimate | quantum-genesis analogy (Γ=0.050, Ρ≈0.90) |
| `oceanography` | 0.75 | estimate | AMOC-UTAC analogy |
| `general` | 0.50 | conservative_default | theoretical midpoint |
| `sparse_fringe` | 0.30 | estimate | pending TIP/P49 |

**All `r_sem` values are provisional.** They hold as a **pre-registered hypothesis** until the TIP/P49 calibration effort delivers ≥30 real perturbation-pair measurements per domain. `SemanticCREP.get_domain_r()` raises a `UserWarning` on every use of an uncalibrated domain so this is never silently forgotten. Once real data lands, `SemanticCREP.calibrate_r(rho_observed, gamma)` recomputes `r_sem` from measured Ρ and Γ using the same closed-form inversion `resilience-core` uses for physical domains.

## Diamond Interface

`ScopeResilience` implements all 6 GenesisAeon Diamond methods:

```python
sr.run_cycle(topic, sigillin_ids, q4_transitions)  # Method 1: execute one step
sr.get_crep_state()                                # Method 2: CREP snapshot {C, R, E, P, Gamma}
sr.get_utac_state()                                # Method 3: UTAC snapshot {H, H_star, K_eff}
sr.get_phase_events()                               # Method 4: hallucination-risk events
sr.to_zenodo_record()                               # Method 5: Zenodo deposition metadata
sr.get_resilience_state()                           # Method 6 (NEW): full Ρ_sem breakdown
```

`get_resilience_state()` is the same 6th Diamond method introduced by `resilience-core` — here it returns `rho_sem`, `gamma_sem`, `risk_level`, live drift rate, a re-grounding flag, and grounding recommendations.

## MCP Server

With the `mcp` extra installed, `scope-resilience` exposes its risk assessment as MCP tools for Claude Code / Claude Desktop:

```bash
pip install "scope-resilience[mcp]"
scope-resilience serve --port 8765
```

Tools exposed: `get_semantic_path`, `assess_hallucination_risk`, `export_llms_txt`, `list_domain_resilience`.

## llms.txt Export

`scope-resilience` ships the first GenesisAeon implementation of [`llms.txt`](https://llmstxt.org/) export — a machine-readable knowledge-space summary (analogous to `robots.txt`) listing a path's Sigillin anchors, Q4 transitions, CREP breakdown, and grounding recommendations, suitable for direct system-prompt injection.

## Structure

```
scope_resilience/
├── constants.py         # σ, σ_Φ, Γ_max, Γ̇_critical, DOMAIN_CONFIG, RISK_LEVELS
├── domain_profile.py     # DomainProfile — r_sem fingerprint per domain
├── semantic_crep.py       # SemanticCREP — CREP tensor + Γ_sem for a path
├── semantic_utac.py       # SemanticUTAC — H_sem attractor mapping
├── hallucination_risk.py  # HallucinationRisk — Ρ_sem + risk classification
├── path_monitor.py        # PathDriftMonitor — sliding-window dΓ_sem/dt
├── grounding.py            # GroundingRecommender — mitigation suggestions
├── llms_txt.py             # LLMSTxtExporter — llms.txt export
├── mcp_server.py            # Optional FastMCP server (requires [mcp] extra)
├── system.py                # ScopeResilience — Diamond Interface main class
└── _cli.py                  # Typer CLI (assess / path / export-llms-txt / serve)
```

## Citation

```bibtex
@software{romer2026scoperesilience,
  author       = {Römer, Johann},
  title        = {scope-resilience: Hallucination resilience mapping for LLM semantic paths},
  year         = 2026,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.XXXXXXX},
  url          = {https://github.com/GenesisAeon/scope-resilience}
}
```

---

Part of the [GenesisAeon](https://github.com/GenesisAeon) ecosystem · related: `diamond-setup` (P-INFRA-1), `resilience-core` (P40), `genesis-scope`
