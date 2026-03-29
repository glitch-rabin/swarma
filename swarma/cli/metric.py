"""swarma metric -- log external metrics into experiments.

Closes the measurement gap: instead of only LLM self-eval,
users can feed back real-world signals (CTR, conversion, engagement).

Usage:
    swarma metric log <team> <agent> <value>          # log a metric value
    swarma metric log <team> <agent> <value> --exp 3   # attach to specific experiment
    swarma metric import <team> <csv-file>             # bulk import from CSV
    swarma metric show <team>                          # show recent metrics
"""

import csv
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .helpers import require_instance, load_env

console = Console()
metric_app = typer.Typer(help="Log and view external metrics.", no_args_is_help=True)


@metric_app.command("log")
def metric_log(
    team: str = typer.Argument(help="Team name"),
    agent: str = typer.Argument(help="Agent ID"),
    value: float = typer.Argument(help="Metric value (numeric)"),
    metric_name: str = typer.Option("", "--metric", "-m", help="Metric name (default: agent's configured metric)"),
    experiment_id: Optional[int] = typer.Option(None, "--exp", "-e", help="Attach to specific experiment ID"),
    note: str = typer.Option("", "--note", "-n", help="Optional note about this data point"),
    instance: str = typer.Option("default", help="Instance name"),
):
    """Log an external metric value for an agent.

    This feeds real-world data into the experiment loop. Use it to log
    engagement rates, conversion numbers, revenue -- anything the LLM
    can't self-evaluate.

    Examples:
        swarma metric log hook-lab copywriter 4.2 --metric ctr_pct
        swarma metric log hook-lab copywriter 127 --metric impressions --exp 3
        swarma metric log my-team writer 8.5 --note "from linkedin analytics"
    """
    instance_path = require_instance(instance)
    load_env(instance_path)

    from ..core.state import StateDB
    state = StateDB(str(instance_path / "state.db"))

    # If no experiment specified, find the active one for this agent
    if experiment_id is None:
        active = state.get_active_experiments(team, agent)
        if active:
            experiment_id = active[0]["id"]
            console.print(f"[dim]auto-attached to experiment #{experiment_id}[/dim]")
        else:
            console.print(f"[dim]no active experiment for {team}/{agent} -- logging standalone[/dim]")

    # Log as an output with metrics_json
    import json
    metrics_data = {"value": value}
    if metric_name:
        metrics_data["metric_name"] = metric_name
    if note:
        metrics_data["note"] = note
    if experiment_id:
        metrics_data["experiment_id"] = experiment_id

    # Store in outputs table as a metric entry
    output_id = state.create_output(
        team_id=team,
        agent_id=agent,
        output_type="external_metric",
        content=json.dumps(metrics_data),
        experiment_id=experiment_id,
    )

    # Also update the experiment's sample count if attached
    if experiment_id:
        state.conn.execute(
            "UPDATE experiments SET sample_size_current = sample_size_current + 1 WHERE id = ?",
            (experiment_id,),
        )
        state.conn.commit()

    console.print(f"[green]logged[/green] {team}/{agent} = {value}", end="")
    if metric_name:
        console.print(f" ({metric_name})", end="")
    if experiment_id:
        console.print(f" [dim]exp #{experiment_id}[/dim]", end="")
    console.print()

    state.close()


@metric_app.command("import")
def metric_import(
    team: str = typer.Argument(help="Team name"),
    csv_file: str = typer.Argument(help="Path to CSV file"),
    instance: str = typer.Option("default", help="Instance name"),
):
    """Bulk import metrics from a CSV file.

    CSV format: agent,value,metric_name(optional),note(optional)

    Example CSV:
        copywriter,4.2,ctr_pct,week 1
        copywriter,5.1,ctr_pct,week 2
        researcher,7.8,relevance_score,
    """
    instance_path = require_instance(instance)
    load_env(instance_path)

    csv_path = Path(csv_file)
    if not csv_path.exists():
        console.print(f"[red]File not found:[/red] {csv_file}")
        raise typer.Exit(1)

    from ..core.state import StateDB
    import json
    state = StateDB(str(instance_path / "state.db"))

    count = 0
    with open(csv_path) as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith("#"):
                continue

            agent = row[0].strip()
            try:
                value = float(row[1].strip())
            except (IndexError, ValueError):
                console.print(f"[yellow]skipping invalid row:[/yellow] {row}")
                continue

            metric_name = row[2].strip() if len(row) > 2 and row[2].strip() else ""
            note = row[3].strip() if len(row) > 3 and row[3].strip() else ""

            metrics_data = {"value": value}
            if metric_name:
                metrics_data["metric_name"] = metric_name
            if note:
                metrics_data["note"] = note

            # Find active experiment for this agent
            active = state.get_active_experiments(team, agent)
            exp_id = active[0]["id"] if active else None

            state.create_output(
                team_id=team,
                agent_id=agent,
                output_type="external_metric",
                content=json.dumps(metrics_data),
                experiment_id=exp_id,
            )

            if exp_id:
                state.conn.execute(
                    "UPDATE experiments SET sample_size_current = sample_size_current + 1 WHERE id = ?",
                    (exp_id,),
                )

            count += 1

    state.conn.commit()
    state.close()

    console.print(f"[green]imported {count} metric entries[/green] for team '{team}'")


@metric_app.command("show")
def metric_show(
    team: str = typer.Argument(help="Team name"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of entries to show"),
    instance: str = typer.Option("default", help="Instance name"),
):
    """Show recent external metrics for a team."""
    instance_path = require_instance(instance)
    load_env(instance_path)

    from ..core.state import StateDB
    import json
    state = StateDB(str(instance_path / "state.db"))

    outputs = state.get_outputs(team, output_type="external_metric", limit=limit)

    if not outputs:
        console.print(f"[dim]No external metrics logged for '{team}' yet.[/dim]")
        console.print("[dim]Log one:[/dim] swarma metric log <team> <agent> <value>")
        state.close()
        return

    table = Table(title=f"External Metrics: {team}")
    table.add_column("Time", style="dim", width=16)
    table.add_column("Agent", style="bold", width=14)
    table.add_column("Value", width=8)
    table.add_column("Metric", width=16)
    table.add_column("Exp", width=5)
    table.add_column("Note", style="dim")

    for o in outputs:
        try:
            data = json.loads(o["content"])
        except (json.JSONDecodeError, TypeError):
            continue

        ts = o.get("created_at", "")[:16] if o.get("created_at") else ""
        exp = str(o.get("experiment_id", "")) if o.get("experiment_id") else "-"
        table.add_row(
            ts,
            o.get("agent_id", ""),
            f"{data.get('value', '?')}",
            data.get("metric_name", "-"),
            exp,
            data.get("note", ""),
        )

    console.print(table)
    state.close()
