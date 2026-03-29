"""swarma init -- scaffold a new instance.

Creates ~/.swarma/instances/{name}/ with config.yaml, .env, and
a starter team directory.
"""

import os
import shutil
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel

from .helpers import get_instance_path


def _get_examples_dir() -> Path:
    """Return the path to bundled example squad templates."""
    import swarma
    return Path(swarma.__file__).parent / "examples"


def _list_available_templates() -> list[str]:
    """Return sorted list of available template names."""
    examples_dir = _get_examples_dir()
    if not examples_dir.is_dir():
        return []
    return sorted(
        d.name for d in examples_dir.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )

console = Console()


def init_command(
    name: str = typer.Option("default", help="Instance name"),
    api_key: str = typer.Option("", help="OpenRouter API key (or set later in .env)"),
    non_interactive: bool = typer.Option(False, "--yes", "-y", help="Skip prompts, use defaults"),
    template: str = typer.Option(None, "--template", "-t", help="Copy a pre-built squad template into teams/"),
    list_templates: bool = typer.Option(False, "--list-templates", help="List available squad templates and exit"),
):
    """Initialize a new swarma instance."""
    # Handle --list-templates
    if list_templates:
        templates = _list_available_templates()
        if not templates:
            console.print("[yellow]No templates found.[/yellow]")
        else:
            console.print("[bold]Available squad templates:[/bold]")
            for t in templates:
                console.print(f"  {t}")
        raise typer.Exit(0)

    # Validate --template if provided
    if template:
        available = _list_available_templates()
        if template not in available:
            console.print(f"[red]Unknown template:[/red] {template}")
            console.print("[bold]Available templates:[/bold]")
            for t in available:
                console.print(f"  {t}")
            raise typer.Exit(1)

    instance_path = get_instance_path(name)

    if instance_path.exists():
        config_exists = (instance_path / "config.yaml").exists()
        if config_exists:
            console.print(f"Instance [bold]{name}[/bold] already exists at {instance_path}")
            if not non_interactive:
                overwrite = typer.confirm("Overwrite config?", default=False)
                if not overwrite:
                    raise typer.Exit(0)

    # Gather info
    if not non_interactive and not api_key:
        console.print()
        console.print(Panel(
            "[bold]swarma[/bold] needs an OpenRouter API key to call LLMs.\n"
            "Get one at: https://openrouter.ai/keys",
            title="setup",
        ))
        api_key = typer.prompt("OpenRouter API key", default="", show_default=False)

    if not non_interactive:
        instance_name = typer.prompt("Instance name", default=name)
    else:
        instance_name = name

    # Create directory structure
    instance_path.mkdir(parents=True, exist_ok=True)
    (instance_path / "teams").mkdir(exist_ok=True)
    (instance_path / "knowledge").mkdir(exist_ok=True)
    (instance_path / "logs").mkdir(exist_ok=True)

    # Write config.yaml
    config = {
        "instance": {
            "name": instance_name,
        },
        "models": {
            "provider": "openrouter",
            "routing": {
                "cheap": "mistralai/mistral-nemo",
                "writing": "qwen/qwen3.5-plus-02-15",
                "reasoning": "deepseek/deepseek-r1",
                "planning": "anthropic/claude-sonnet-4-6",
                "research": "perplexity/sonar-pro",
            },
        },
        "knowledge": {
            "engine": "local",
        },
    }

    config_path = instance_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Write .env
    env_path = instance_path / ".env"
    env_lines = []
    if api_key:
        env_lines.append(f"OPENROUTER_API_KEY={api_key}")
    else:
        env_lines.append("# OPENROUTER_API_KEY=sk-or-...")

    # Preserve existing .env entries
    if env_path.exists():
        existing = env_path.read_text().strip().split("\n")
        existing_keys = {line.split("=")[0] for line in existing if "=" in line and not line.startswith("#")}
        for line in env_lines:
            key = line.split("=")[0]
            if key not in existing_keys:
                existing.append(line)
        env_lines = existing

    env_path.write_text("\n".join(env_lines) + "\n")

    # Write .gitignore
    gitignore = instance_path / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(".env\nstate.db\nknowledge/\nlogs/\n")

    # Copy template squad if requested (skip starter team if template provided)
    if template:
        src = _get_examples_dir() / template
        dst = instance_path / "teams" / template
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        console.print(f"Copied squad template '{template}' to teams/")
    elif not any((instance_path / "teams").iterdir()):
        # Create a starter team only if no template and no existing teams
        starter_team = instance_path / "teams" / "starter"
        _create_starter_team(starter_team)

    # Done
    console.print()
    console.print(f"[green]Instance created:[/green] {instance_path}")
    console.print()
    console.print("  config:  config.yaml")
    console.print("  secrets: .env")
    console.print("  teams:   teams/")
    console.print()

    if not api_key:
        console.print("[yellow]Next:[/yellow] Add your OpenRouter API key to .env")
    else:
        console.print('[yellow]Next:[/yellow] Run [bold]swarma cycle starter --topic "why do startups fail?"[/bold]')
    console.print()
    console.print('Try a pre-built squad:  [bold]swarma init --template hook-lab[/bold]')


def _create_starter_team(team_path: Path):
    """Create a minimal starter team for first-run testing."""
    team_path.mkdir(parents=True, exist_ok=True)
    agents_dir = team_path / "agents"
    agents_dir.mkdir(exist_ok=True)

    # team.yaml
    team_config = {
        "name": "starter",
        "goal": "test that swarma works end to end",
        "flow": "thinker -> writer",
    }
    with open(team_path / "team.yaml", "w") as f:
        yaml.dump(team_config, f, default_flow_style=False, sort_keys=False)

    # thinker agent
    thinker = {
        "name": "thinker",
        "model": {
            "model_id": "mistralai/mistral-nemo",
            "max_tokens": 300,
            "temperature": 0.5,
        },
        "instructions": (
            "You are a creative thinker. Come up with ONE interesting, "
            "non-obvious observation about a topic the user gives you. "
            "Keep it to 2-3 sentences. Be specific and original."
        ),
    }
    with open(agents_dir / "thinker.yaml", "w") as f:
        yaml.dump(thinker, f, default_flow_style=False, sort_keys=False)

    # writer agent
    writer = {
        "name": "writer",
        "model": {
            "model_id": "mistralai/mistral-nemo",
            "max_tokens": 400,
            "temperature": 0.7,
        },
        "instructions": (
            "You are a sharp writer. Take the idea you receive and "
            "turn it into a punchy social media post (3-4 sentences). "
            "Direct, lowercase energy, no corporate speak. Start with a hook."
        ),
        "triggered_by": "thinker",
    }
    with open(agents_dir / "writer.yaml", "w") as f:
        yaml.dump(writer, f, default_flow_style=False, sort_keys=False)
