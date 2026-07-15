"""Known DomainProfiles — populated here to avoid circular imports."""

from __future__ import annotations

from scope_resilience import constants
from scope_resilience.domain_profile import DomainProfile

KNOWN_DOMAIN_PROFILES: dict[str, DomainProfile] = {
    # Physical calibration reference points (analytically estimated from Atlas)
    "amoc":        DomainProfile.from_atlas_target("amoc",    0.251, 0.65),
    "arctic_era5": DomainProfile.from_atlas_target("arctic",  0.920, 0.05),
    "sandpile":    DomainProfile.from_atlas_target("sandpile", 0.296, 0.75),
    "quantum":     DomainProfile.from_atlas_target("quantum",  0.050, 0.90),
    # Semantic domains — pending P49/TIP calibration
    "llm_physics": DomainProfile(
        "llm_physics", gamma=0.65, r=2.5,
        r_status="estimated", r_source="expert estimate, pending TIP",
    ),
    "llm_fringe": DomainProfile(
        "llm_fringe", gamma=0.20, r=0.9,
        r_status="estimated", r_source="expert estimate, pending TIP",
    ),
}

# Expose through the constants namespace for convenience
constants.KNOWN_DOMAIN_PROFILES.update(KNOWN_DOMAIN_PROFILES)
