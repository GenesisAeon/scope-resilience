"""Shared constants for scope-resilience.

Universal structural constants (σ, σ_Φ, Γ_max, Γ̇_critical) are fixed across
all domains. Domain-specific r_sem values live in DOMAIN_CONFIG and are
explicitly marked as estimates pending TIP/P49 calibration.
"""

from __future__ import annotations

from typing import Any

SIGMA: float = 2.2
SIGMA_PHI: float = 1.0 / 16.0  # ≈ 0.0625 — Frame-Principle boundary
GAMMA_MAX: float = 0.920        # ERA5 Arctic — most saturated known system
GAMMA_DOT_CRITICAL: float = 0.10  # critical semantic drift rate per step

# ── Domain r_sem configuration ──────────────────────────────────────────────
# Structure is universal; values are domain-specific.
# All status="estimate" until P49/TIP delivers ≥30 perturbation pairs.
# Calibration formula: r = Ρ_observed / (tanh²(σΓ) · (1 − Γ/Γ_max))

DOMAIN_CONFIG: dict[str, dict[str, Any]] = {
    "physics_dense": {
        "r_sem": 0.80,
        "status": "estimate",
        "calibration_source": "pending TIP/P49",
        "notes": "Dense physics literature, fast self-correction expected",
    },
    "sparse_fringe": {
        "r_sem": 0.30,
        "status": "estimate",
        "calibration_source": "pending TIP/P49",
        "notes": "Sparse/speculative domains, slow self-correction",
    },
    "curated_graph": {
        "r_sem": 0.90,
        "status": "estimate",
        "calibration_source": "pending TIP/P49",
        "notes": "Dense curated knowledge graphs, strongest attractor",
    },
    "general": {
        "r_sem": 0.50,
        "status": "conservative_default",
        "calibration_source": "theoretical midpoint",
        "notes": "Conservative default: underestimates Ρ_sem when domain unknown",
    },
    "oceanography": {
        "r_sem": 0.75,
        "status": "estimate",
        "calibration_source": "AMOC-UTAC analogy",
        "notes": "Well-documented physical oceanography literature",
    },
    "quantum": {
        "r_sem": 0.85,
        "status": "estimate",
        "calibration_source": "quantum-genesis analogy (Γ=0.050, Ρ≈0.90)",
        "notes": "Formal quantum physics — high coherence, slow drift",
    },
}

# ── Risk classification thresholds ─────────────────────────────────────────
# Keys: (low_inclusive, high_exclusive)
RISK_LEVELS: dict[tuple[float, float], tuple[str, str]] = {
    (0.70, 1.01): ("safe",      "Path is semantically stable. Proceed."),
    (0.40, 0.70): ("moderate",  "Moderate drift risk. Inject grounding anchors."),
    (0.10, 0.40): ("high_risk", "High hallucination risk. Consider alternative path."),
    (0.00, 0.10): ("critical",  "Critical: near semantic phase boundary. "
                                "Do not initialise on this path."),
}

# ── Atlas reference calibration points ─────────────────────────────────────
ATLAS_REFERENCES: dict[str, dict[str, Any]] = {
    "amoc":        {"gamma": 0.251, "rho_target": 0.65, "r_required": 3.54},
    "arctic_era5": {"gamma": 0.920, "rho_target": 0.05, "r_required": 18.0},
    "sandpile":    {"gamma": 0.296, "rho_target": 0.75, "r_required": 3.0},
    "quantum":     {"gamma": 0.050, "rho_target": 0.90, "r_required": 1.2},
}

# Populated lazily — see domain_profile.py for DomainProfile.from_atlas_target
# to avoid circular imports at module load time.
KNOWN_DOMAIN_PROFILES: dict[str, Any] = {}
