"""Tests for PathDriftMonitor."""

import pytest
from scope_resilience.path_monitor import PathDriftMonitor
from scope_resilience.constants import GAMMA_DOT_CRITICAL


def test_no_drift_with_one_sample():
    m = PathDriftMonitor()
    drift = m.update(0.5)
    assert drift == pytest.approx(0.0)


def test_drift_detected():
    m = PathDriftMonitor()
    m.update(0.5)
    drift = m.update(0.7)
    assert drift == pytest.approx(0.2, rel=1e-9)


def test_needs_regrounding_false_below_threshold():
    m = PathDriftMonitor()
    m.update(0.5)
    m.update(0.5 + GAMMA_DOT_CRITICAL * 0.5)
    assert m.needs_regrounding() is False


def test_needs_regrounding_true_above_threshold():
    m = PathDriftMonitor()
    m.update(0.5)
    m.update(0.5 + GAMMA_DOT_CRITICAL * 1.5)
    assert m.needs_regrounding() is True


def test_window_size_respected():
    m = PathDriftMonitor(window_size=3)
    for v in [0.1, 0.2, 0.3, 0.4, 0.5]:
        m.update(v)
    assert len(m.window) == 3


def test_reset_clears_window():
    m = PathDriftMonitor()
    m.update(0.5)
    m.update(0.6)
    m.reset()
    assert m.window == []
    assert m.current_drift() == 0.0
