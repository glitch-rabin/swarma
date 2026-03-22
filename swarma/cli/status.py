"""swarma status -- show current state of the instance."""

import typer
from rich.console import Console
from rich.table import Table

from .helpers import load_env, load_teams, require_instance

console = Console()


def status_command(
    instance: str = typer.Option("default", help="Instance name"),
):
    """Show the current state of a swarma instance."""
    instance_path = require_instance(instance)
    load_env(instance_path)

    from ..core.config import InstanceConfig
    from ..core.state import StateDB

    # Load config
    config_path = instance_path / "config.yaml"
    if config_path.exists():
        config = InstanceConfig.from_file(str(config_path))
    else:
        console.print(f"[red]No config.yaml found[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]swarma[/bold] instance: {config.name}")
    console.print(f"  path: {instance_path}")
    console.print()

    # Teams
    teams = load_teams(instance_path)
    if teams:
        team_table = Table(title="Teams")
        team_table.add_column("Name", style="bold")
        team_table.add_column("Agents")
        team_table.add_column("Flow")
        team_table.add_column("Schedule")
        team_table.add_column("Budget")

        for tid, t in teams.items():
            agents = ", ".join(t.agents.keys())
            budget = f"${t.budget_monthly:.0f}/mo" if t.budget_monthly else "-"
            team_table.add_row(tid, agents, t.flow or "-", t.schedule or "-", budget)

        console.print(team_table)
    else:
        console.print("[dim]No teams configured.[/dim]")

    # State DB stats
    db_path = instance_path / "state.db"
    if db_path.exists():
        state = StateDB(str(db_path))
        console.print()

        # Costs
        daily = state.get_daily_cost()
        monthly = state.get_monthly_cost()
        console.print(f"  [bold]Costs:[/bold] today ${daily:.4f} | this month ${monthly:.4f}")

        # Recent runs
        runs = state.conn.execute(
            "SELECT agent_id, status, started_at FROM agent_runs ORDER BY id DESC LIMIT 5"
        ).fetchall()
        if runs:
            run_table = Table(title="Recent Runs")
            run_table.add_column("Agent")
            run_table.add_column("Status")
            run_table.add_column("Time")
            for r in runs:
                r = dict(r)
                status_style = "green" if r["status"] == "completed" else "red"
                run_table.add_row(
                    r["agent_id"],
                    f"[{status_style}]{r['status']}[/{status_style}]",
                    r.get("started_at", "")[:19],
                )
            console.print(run_table)

        # Pending plans
        plans = state.get_pending_plans()
        if plans:
            console.print(f"  [yellow]Pending plans: {len(plans)}[/yellow]")

        # Queue
        stats = state.get_queue_stats()
        if stats["pending"] > 0 or stats["processing"] > 0:
            console.print(f"  Queue: {stats['pending']} pending, {stats['processing']} processing")

        state.close()
    else:
        console.print("[dim]No state.db yet (run a cycle first).[/dim]")

    console.print()
