"""PathDriftMonitor — live dΓ_sem/dt monitoring during a conversation.

Maintains a sliding window of Γ_sem values and signals when the drift
rate exceeds the critical threshold, triggering semantic re-grounding.
"""

from __future__ import annotations

from scope_resilience.constants import GAMMA_DOT_CRITICAL


class PathDriftMonitor:
    """Tracks Γ_sem over a sliding window to detect semantic drift."""

    def __init__(self, window_size: int = 5) -> None:
        self.window: list[float] = []
        self.window_size = window_size

    def update(self, gamma_sem: float) -> float:
        """Append a new Γ_sem value and return the instantaneous dΓ/dt."""
        self.window.append(gamma_sem)
        if len(self.window) > self.window_size:
            self.window.pop(0)
        if len(self.window) < 2:
            return 0.0
        return self.window[-1] - self.window[-2]

    def current_drift(self) -> float:
        """Return the most recent dΓ/dt (0.0 if fewer than 2 samples)."""
        if len(self.window) < 2:
            return 0.0
        return self.window[-1] - self.window[-2]

    def needs_regrounding(self) -> bool:
        """True when |dΓ/dt| exceeds GAMMA_DOT_CRITICAL."""
        return abs(self.current_drift()) > GAMMA_DOT_CRITICAL

    def reset(self) -> None:
        """Clear the sliding window."""
        self.window.clear()
