"""Tests for scope-resilience's own CLI (src/scope_resilience/_cli.py)."""

from typer.testing import CliRunner

from scope_resilience._cli import app

runner = CliRunner()


def test_assess_runs_and_shows_metrics():
    result = runner.invoke(app, ["assess", "AMOC tipping point"])
    assert result.exit_code == 0, result.output
    assert "Hallucination Risk" in result.output
    assert "Risk Level" in result.output


def test_assess_with_domain_option():
    result = runner.invoke(app, ["assess", "quantum computing", "--domain", "physics_dense"])
    assert result.exit_code == 0, result.output
    assert "Hallucination Risk" in result.output


def test_export_llms_txt_runs():
    result = runner.invoke(app, ["export-llms-txt", "test topic"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() != ""


def test_path_command_runs():
    result = runner.invoke(app, ["path", "test topic"])
    assert result.exit_code == 0, result.output
    assert "Topic:" in result.output
    assert "\u0393_sem:" in result.output or "Gamma_sem:" in result.output


def test_path_command_no_path_found_is_graceful():
    # min_rho=1.1 is unreachable (rho_sem is bounded well below 1.1),
    # so get_semantic_path's own "no path meets threshold" branch still
    # returns a path with a warning attached -- assert this stays exit 0.
    result = runner.invoke(app, ["path", "test topic", "--min-rho", "1.1"])
    assert result.exit_code == 0, result.output


def test_serve_without_mcp_extra_fails_gracefully():
    # fastmcp is an optional extra; if not installed, serve() must exit
    # cleanly with code 1 and an explanatory message, not crash.
    result = runner.invoke(app, ["serve"])
    if result.exit_code != 0:
        assert "fastmcp" in result.output.lower() or "mcp" in result.output.lower()
    # If fastmcp IS installed in this environment, serve would try to
    # actually bind a port and block -- do not assert exit_code==0 here.
