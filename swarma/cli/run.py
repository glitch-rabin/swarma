"""swarma run -- start the engine with scheduling.

Loads all teams, starts APScheduler for cron-based agents,
starts the heartbeat loop, and optionally starts the API server.
"""

import asyncio
import signal

import typer
from rich.console import Console

from .helpers import build_engine, console, load_env, load_teams, require_instance

console = Console()


def run_command(
    instance: str = typer.Option("default", help="Instance name"),
    team: str = typer.Option("", help="Run only this team (default: all)"),
    once: bool = typer.Option(False, help="Run one cycle and exit"),
    port: int = typer.Option(0, help="Start API server on this port (0 = no server)"),
):
    """Start the swarma engine."""
    instance_path = require_instance(instance)
    load_env(instance_path)

    teams = load_teams(instance_path)
    if not teams:
        console.print("[red]No teams found.[/red] Create one with [bold]swarma team create[/bold]")
        raise typer.Exit(1)

    if team:
        if team not in teams:
            console.print(f"[red]Team '{team}' not found.[/red] Available: {list(teams.keys())}")
            raise typer.Exit(1)
        teams = {team: teams[team]}

    engine = build_engine(instance_path)

    console.print(f"[bold]swarma[/bold] engine starting")
    console.print(f"  instance: {instance}")
    console.print(f"  teams: {list(teams.keys())}")
    console.print()

    if once:
        # Single cycle mode
        asyncio.run(_run_once(engine, teams))
    else:
        # Continuous mode with scheduling
        asyncio.run(_run_continuous(engine, teams, port))


async def _run_once(engine, teams):
    """Run one cycle for each team and exit."""
    for team_id in teams:
        console.print(f"[bold]Running cycle:[/bold] {team_id}")
        try:
            result = await engine.run_cycle(team_id)
            _print_cycle_result(result)
        except Exception as e:
            console.print(f"[red]Cycle failed:[/red] {e}")
    await engine.close()


async def _run_continuous(engine, teams, port):
    """Run continuously with scheduling."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler()
    loop = asyncio.get_event_loop()

    # Schedule teams with cron expressions
    for team_id, team_config in teams.items():
        schedule = team_config.schedule
        if schedule:
            # Parse cron: "0 7 * * *" or simple "HH:MM"
            if len(schedule.split()) == 5:
                parts = schedule.split()
                scheduler.add_job(
                    engine.run_cycle, "cron",
                    args=[team_id],
                    minute=parts[0], hour=parts[1],
                    day=parts[2], month=parts[3], day_of_week=parts[4],
                    id=f"cycle-{team_id}",
                )
                console.print(f"  scheduled: {team_id} at cron({schedule})")
            else:
                console.print(f"  [yellow]skipping schedule for {team_id}:[/yellow] '{schedule}' not a valid cron")
        else:
            console.print(f"  [dim]{team_id}: no schedule (manual trigger only)[/dim]")

    scheduler.start()
    console.print()
    console.print("[green]Engine running.[/green] Press Ctrl+C to stop.")

    # Handle graceful shutdown
    stop_event = asyncio.Event()

    def _signal_handler():
        console.print("\n[yellow]Shutting down...[/yellow]")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    # If API server requested, start it
    if port > 0:
        # Import here to avoid dependency if not using server
        try:
            from ..server.app import create_app
            import uvicorn
            config = uvicorn.Config(
                create_app(engine), host="0.0.0.0", port=port,
                log_level="info",
            )
            server = uvicorn.Server(config)
            asyncio.create_task(server.serve())
            console.print(f"  API server: http://0.0.0.0:{port}")
        except ImportError:
            console.print("[yellow]API server requires: pip install swarma[dashboard][/yellow]")

    await stop_event.wait()
    scheduler.shutdown()
    await engine.close()
    console.print("[green]Stopped.[/green]")


def _print_cycle_result(result: dict):
    """Pretty-print a cycle result."""
    from rich.table import Table

    console.print()

    table = Table(title=f"Cycle: {result['team_id']}")
    table.add_column("Agent", style="bold")
    table.add_column("Model")
    table.add_column("Cost")
    table.add_column("Output Preview")

    for agent_id, r in result.get("results", {}).items():
        content = r.get("content", "")[:80]
        cost = f"${r.get('cost', 0):.6f}"
        model = r.get("model", "?")
        # Shorten model name
        if "/" in model:
            model = model.split("/")[-1]
        table.add_row(agent_id, model, cost, content)

    console.print(table)

    errors = result.get("errors", {})
    if errors:
        console.print(f"[red]Errors:[/red]")
        for aid, err in errors.items():
            console.print(f"  {aid}: {err}")

    console.print(
        f"\n  duration: {result['duration_seconds']:.1f}s | "
        f"total cost: ${result['total_cost']:.6f} | "
        f"agents: {len(result.get('agents_run', []))}"
    )
    console.print()
