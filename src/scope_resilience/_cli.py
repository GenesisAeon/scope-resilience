"""CLI entry-point for scope-resilience."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from scope_resilience.system import ScopeResilience

app = typer.Typer(name="scope-resilience", add_completion=False)
console = Console()


@app.command("serve")
def serve(
    port: int = typer.Option(8765, help="Port for the MCP server"),
) -> None:
    """Start the MCP server (requires scope-resilience[mcp] to be installed)."""
    try:
        from scope_resilience.mcp_server import serve as _serve
    except ImportError:
        console.print(
            "[red]MCP server requires fastmcp. "
            "Install with: pip install 'scope-resilience[mcp]'[/red]"
        )
        raise typer.Exit(1) from None
    console.print(f"Starting MCP server on port {port}...")
    _serve(port=port)


@app.command("assess")
def assess(
    topic: str = typer.Argument(..., help="Semantic topic to assess"),
    domain: str = typer.Option("general", help="Domain hint"),
    min_rho: float = typer.Option(0.4, help="Minimum acceptable Ρ_sem"),
) -> None:
    """Assess hallucination risk for a semantic topic."""
    sr = ScopeResilience(domain=domain)
    result = sr.run_cycle(topic)

    table = Table(title=f"Hallucination Risk: {topic}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Ρ_sem", f"{result['rho_sem']:.4f}")
    table.add_row("Γ_sem", f"{result['gamma_sem']:.4f}")
    table.add_row("Risk Level", result["risk_level"])
    table.add_row("dΓ/dt", f"{result['d_gamma_dt']:.4f}")
    table.add_row("Needs Re-grounding", str(result["needs_regrounding"]))
    console.print(table)


@app.command("export-llms-txt")
def export_llms(
    topic: str = typer.Argument(..., help="Topic to export"),
    domain: str = typer.Option("general", help="Domain hint"),
) -> None:
    """Export semantic path as llms.txt."""
    sr = ScopeResilience(domain=domain)
    sr.run_cycle(topic)
    console.print(sr.to_llms_txt(topic))


@app.command("path")
def path_cmd(
    topic: str = typer.Argument(..., help="Topic to navigate"),
    domain: str = typer.Option("general", help="Domain hint"),
    min_rho: float = typer.Option(0.4, help="Minimum Ρ_sem"),
) -> None:
    """Get and display the best semantic path for a topic."""
    sr = ScopeResilience(domain=domain)
    path = sr.get_semantic_path(topic, min_rho=min_rho)
    if path is None:
        console.print("[red]No path found.[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]Topic:[/bold] {path.topic}")
    console.print(f"[bold]Γ_sem:[/bold] {path.gamma_sem:.4f}")
    console.print(f"[bold]Ρ_sem:[/bold] {path.rho_sem:.4f}")
    console.print(f"[bold]Risk:[/bold] {path.risk_level}")
    for rec in path.grounding_recommendations:
        console.print(f"  • {rec}")
