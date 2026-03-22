"""swarma cycle -- run a single cycle for a team.

Quick way to test without starting the full engine.
"""

import asyncio

import typer
from rich.console import Console

from .helpers import build_engine, load_env, load_teams, require_instance
from .run import _print_cycle_result

console = Console()


def cycle_command(
    team: str = typer.Argument(help="Team name to run cycle for"),
    instance: str = typer.Option("default", help="Instance name"),
    topic: str = typer.Option("", help="Optional topic/prompt to seed the cycle"),
):
    """Run a single cycle for a team."""
    instance_path = require_instance(instance)
    load_env(instance_path)

    teams = load_teams(instance_path)
    if team not in teams:
        available = list(teams.keys())
        console.print(f"[red]Team '{team}' not found.[/red]")
        if available:
            console.print(f"Available: {available}")
        else:
            console.print("No teams configured. Run [bold]swarma team create[/bold] first.")
        raise typer.Exit(1)

    engine = build_engine(instance_path)

    context = None
    if topic:
        context = {"topic": topic, "task": topic}
        console.print(f"Topic: {topic}")

    console.print(f"[bold]Running cycle:[/bold] {team}")
    console.print(f"  flow: {teams[team].flow}")
    console.print(f"  agents: {list(teams[team].agents.keys())}")
    console.print()

    try:
        result = asyncio.run(_run(engine, team, context))
        _print_cycle_result(result)
    except Exception as e:
        console.print(f"[red]Cycle failed:[/red] {e}")
        raise typer.Exit(1)


async def _run(engine, team_id, context):
    result = await engine.run_cycle(team_id, context)
    await engine.close()
    return result
