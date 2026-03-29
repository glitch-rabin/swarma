"""swarma team -- manage teams."""

import os
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .helpers import load_teams, require_instance

console = Console()
team_app = typer.Typer(help="Manage teams.", no_args_is_help=True)


@team_app.command("list")
def team_list(
    instance: str = typer.Option("default", help="Instance name"),
):
    """List all teams in this instance."""
    instance_path = require_instance(instance)
    teams = load_teams(instance_path)

    if not teams:
        console.print("[dim]No teams. Create one with:[/dim] swarma team create")
        return

    table = Table(title="Teams")
    table.add_column("Name", style="bold")
    table.add_column("Goal")
    table.add_column("Agents")
    table.add_column("Flow")

    for tid, t in teams.items():
        agents = ", ".join(t.agents.keys())
        goal = (t.goal[:50] + "...") if len(t.goal) > 50 else t.goal
        table.add_row(tid, goal, agents, t.flow or "-")

    console.print(table)


@team_app.command("show")
def team_show(
    name: str = typer.Argument(help="Team name"),
    instance: str = typer.Option("default", help="Instance name"),
):
    """Show details of a team."""
    instance_path = require_instance(instance)
    teams = load_teams(instance_path)

    if name not in teams:
        console.print(f"[red]Team '{name}' not found.[/red] Available: {list(teams.keys())}")
        raise typer.Exit(1)

    team = teams[name]
    console.print(Panel(f"[bold]{team.name}[/bold]\n{team.goal}", title="Team"))
    console.print(f"  flow: {team.flow or '(not defined)'}")
    console.print(f"  schedule: {team.schedule or '(manual)'}")
    console.print(f"  budget: ${team.budget_monthly:.0f}/mo" if team.budget_monthly else "  budget: (unlimited)")
    console.print(f"  tools: {team.tools or '(none)'}")
    console.print()

    if team.agents:
        table = Table(title="Agents")
        table.add_column("Name", style="bold")
        table.add_column("Model")
        table.add_column("Runtime")
        table.add_column("Trigger")
        table.add_column("Metric")

        for aid, a in team.agents.items():
            model = a.model.model_id
            if "/" in model:
                model = model.split("/")[-1]
            trigger = a.triggered_by or a.schedule or "-"
            metric = a.metric.name or "-"
            table.add_row(aid, model, a.runtime, trigger, metric)

        console.print(table)


@team_app.command("templates")
def team_templates():
    """List available team templates."""
    from ..templates import list_templates

    templates = list_templates()
    if not templates:
        console.print("[dim]No templates found.[/dim]")
        return

    table = Table(title="Team Templates")
    table.add_column("ID", style="bold", width=12)
    table.add_column("Name", width=20)
    table.add_column("Agents", width=6)
    table.add_column("Flow", width=30)
    table.add_column("Description")

    for t in templates:
        table.add_row(t["id"], t["name"], str(t["agents"]), t["flow"][:30], t["description"][:50])

    console.print(table)
    console.print("\n[dim]Use:[/dim] swarma team create myteam --template <id>")


@team_app.command("create")
def team_create(
    name: str = typer.Argument(help="Team name (used as folder name)"),
    instance: str = typer.Option("default", help="Instance name"),
    template: str = typer.Option("", help="Template to use (see 'swarma team templates')"),
    goal: str = typer.Option("", help="Team goal"),
    flow: str = typer.Option("", help="Flow definition (e.g. 'a -> b -> c')"),
    from_goal: str = typer.Option("", "--from-goal", help="Generate team from a goal using AI (e.g. 'improve LinkedIn engagement')"),
    context: str = typer.Option("", help="Business context for --from-goal (who you are, what you do)"),
    budget: float = typer.Option(30.0, help="Monthly budget for --from-goal generation"),
):
    """Create a new team."""
    instance_path = require_instance(instance)

    # AI-generated team from goal description
    if from_goal:
        import asyncio
        from .helpers import load_env, build_engine

        load_env(instance_path)

        console.print(f"[bold]Generating team from goal:[/bold] {from_goal}")
        console.print("[dim]This calls an LLM to design your team...[/dim]")

        # We need a router for the LLM call. Build a minimal one.
        import os
        from ..core.router import ModelRouter

        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            console.print("[red]No OPENROUTER_API_KEY found. Set it in your instance .env file.[/red]")
            raise typer.Exit(1)

        router = ModelRouter(api_key=api_key, app_name="swarma")

        from ..core.generator import generate_team

        try:
            result = asyncio.run(generate_team(
                intent=from_goal,
                router=router,
                instance_path=instance_path,
                context=context,
                name=name,
                budget=budget,
            ))
        except FileExistsError:
            console.print(f"[red]Team '{name}' already exists.[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Generation failed:[/red] {e}")
            raise typer.Exit(1)

        console.print(f"\n[green]Team generated:[/green] {result['team_dir']}")
        console.print(f"  name: {result['display_name']}")
        console.print(f"  goal: {result['goal']}")
        console.print(f"  flow: {result['flow']}")
        console.print(f"  agents: {result['agents']}")

        if result.get("first_experiment"):
            exp = result["first_experiment"]
            console.print(f"\n[bold]First experiment:[/bold]")
            console.print(f"  hypothesis: {exp.get('hypothesis', '(none)')}")
            console.print(f"  metric: {exp.get('metric_name', '(none)')}")

        if result.get("issues"):
            console.print(f"\n[yellow]Warnings:[/yellow] {result['issues']}")

        console.print(f"\n[yellow]Next:[/yellow] Review configs in {result['team_dir']}/")
        console.print(f"Then run: [bold]swarma cycle {result['team_name']}[/bold]")
        return

    team_dir = instance_path / "teams" / name

    if team_dir.exists():
        console.print(f"[red]Team '{name}' already exists at {team_dir}[/red]")
        raise typer.Exit(1)

    # If using a template, load it
    if template:
        from ..templates import get_template

        tmpl = get_template(template)
        if not tmpl:
            console.print(f"[red]Template '{template}' not found.[/red] Run: swarma team templates")
            raise typer.Exit(1)

        goal = goal or tmpl.get("goal", "")
        flow = flow or tmpl.get("flow", "")
        tmpl_agents = tmpl.get("agents", {})

        # Create team directory
        team_dir.mkdir(parents=True, exist_ok=True)
        agents_dir = team_dir / "agents"
        agents_dir.mkdir(exist_ok=True)

        # Write team.yaml from template
        team_config = {
            "name": tmpl.get("name", name),
            "goal": goal,
            "flow": flow,
            "schedule": tmpl.get("schedule"),
            "budget_monthly": tmpl.get("budget_monthly"),
        }
        with open(team_dir / "team.yaml", "w") as f:
            yaml.dump(team_config, f, default_flow_style=False, sort_keys=False)

        # Write agent configs from template
        for agent_id, agent_data in tmpl_agents.items():
            with open(agents_dir / f"{agent_id}.yaml", "w") as f:
                yaml.dump(agent_data, f, default_flow_style=False, sort_keys=False)

        console.print(f"[green]Team created from template '{template}':[/green] {team_dir}")
        console.print(f"  agents: {list(tmpl_agents.keys())}")
        console.print(f"  flow: {flow}")
        console.print()
        console.print(f"[yellow]Next:[/yellow] Customize agents in {agents_dir}/")
        console.print(f"Then run: [bold]swarma cycle {name}[/bold]")
        return

    # Manual creation (no template)
    if not goal:
        goal = typer.prompt("Team goal", default=f"run {name} tasks")
    if not flow:
        flow = typer.prompt("Flow (e.g. 'researcher -> writer')", default="agent-1 -> agent-2")

    # Parse flow to get agent names
    from ..flow.parser import parse_flow
    parsed = parse_flow(flow)
    agent_names = parsed.all_agents

    # Create team directory
    team_dir.mkdir(parents=True, exist_ok=True)
    agents_dir = team_dir / "agents"
    agents_dir.mkdir(exist_ok=True)

    # Write team.yaml
    team_config = {
        "name": name,
        "goal": goal,
        "flow": flow,
    }
    with open(team_dir / "team.yaml", "w") as f:
        yaml.dump(team_config, f, default_flow_style=False, sort_keys=False)

    # Write agent stubs
    for agent_name in agent_names:
        agent_config = {
            "name": agent_name,
            "model": {
                "model_id": "mistralai/mistral-nemo",
                "max_tokens": 500,
                "temperature": 0.7,
            },
            "instructions": f"You are the {agent_name}. Define your behavior here.",
        }
        with open(agents_dir / f"{agent_name}.yaml", "w") as f:
            yaml.dump(agent_config, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Team created:[/green] {team_dir}")
    console.print(f"  agents: {agent_names}")
    console.print(f"  flow: {flow}")
    console.print()
    console.print(f"[yellow]Next:[/yellow] Edit agent configs in {agents_dir}/")
    console.print(f"Then run: [bold]swarma cycle {name}[/bold]")
