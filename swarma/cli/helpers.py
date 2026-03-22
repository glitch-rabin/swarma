"""Shared CLI helpers -- instance discovery, config loading, display."""

import os
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

console = Console()

DEFAULT_SWARMA_HOME = os.path.expanduser("~/.swarma")
DEFAULT_INSTANCE = "default"


def get_instance_path(instance: Optional[str] = None) -> Path:
    """Resolve the instance directory path.

    Priority:
    1. Explicit --instance flag
    2. SWARMA_INSTANCE env var
    3. ~/.swarma/instances/default/
    """
    home = os.environ.get("SWARMA_HOME", DEFAULT_SWARMA_HOME)
    name = instance or os.environ.get("SWARMA_INSTANCE", DEFAULT_INSTANCE)
    return Path(home) / "instances" / name


def require_instance(instance: Optional[str] = None) -> Path:
    """Get instance path, exit if it doesn't exist."""
    path = get_instance_path(instance)
    if not path.exists():
        console.print(f"[red]Instance not found:[/red] {path}")
        console.print("Run [bold]swarma init[/bold] first.")
        raise typer.Exit(1)
    return path


def load_env(instance_path: Path):
    """Load .env file from instance directory."""
    env_file = instance_path / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(str(env_file))


def load_instance_config(instance_path: Path):
    """Load config.yaml from instance directory."""
    from ..core.config import InstanceConfig
    config_path = instance_path / "config.yaml"
    if not config_path.exists():
        console.print(f"[red]No config.yaml in {instance_path}[/red]")
        raise typer.Exit(1)
    return InstanceConfig.from_file(str(config_path))


def load_teams(instance_path: Path):
    """Load all teams from instance directory."""
    from ..core.config import load_all_teams
    teams_dir = instance_path / "teams"
    if not teams_dir.exists():
        return {}
    return load_all_teams(str(teams_dir))


def build_engine(instance_path: Path):
    """Build a full Engine from an instance directory."""
    load_env(instance_path)

    config = load_instance_config(instance_path)
    teams = load_teams(instance_path)

    from ..core.router import ModelRouter
    from ..core.state import StateDB
    from ..core.knowledge import KnowledgeStore
    from ..core.cycle import Engine
    from ..tools.registry import ToolRegistry

    api_key = os.environ.get("OPENROUTER_API_KEY") or config.models.get("api_key")
    if not api_key:
        console.print("[red]No OPENROUTER_API_KEY found in .env or config.yaml[/red]")
        raise typer.Exit(1)

    router = ModelRouter(api_key=api_key, app_name=config.name)
    state = StateDB(str(instance_path / "state.db"))

    qmd_endpoint = None
    knowledge_cfg = config.knowledge
    if knowledge_cfg.get("engine") == "qmd":
        qmd_endpoint = knowledge_cfg.get("qmd_endpoint", "http://localhost:8181/mcp")

    knowledge = KnowledgeStore(
        str(instance_path / "knowledge"),
        state,
        qmd_endpoint=qmd_endpoint,
    )

    # Load tools from config.yaml
    tool_registry = ToolRegistry()
    tools_cfg = config.tools
    if tools_cfg:
        tool_registry.load_from_config(tools_cfg)

    # Build adapter registry for non-LLM runtimes
    from ..adapters.registry import AdapterRegistry
    adapter_registry = AdapterRegistry(
        router=router,
        instance_runtimes=config.runtimes,
    )

    # Load expert catalog
    from ..experts.catalog import ExpertCatalog
    expert_catalog = ExpertCatalog()
    expert_paths = [
        instance_path / "experts",
        Path(os.environ.get("SWARMA_EXPERTS", "")) if os.environ.get("SWARMA_EXPERTS") else None,
        Path(os.path.expanduser("~/.swarma/experts")),
    ]
    for ep in expert_paths:
        if ep and ep.exists():
            expert_catalog.load_directory(str(ep))
            break

    return Engine(
        teams=teams, router=router, state=state,
        knowledge=knowledge, tool_registry=tool_registry,
        adapter_registry=adapter_registry, expert_catalog=expert_catalog,
    )


# Need typer import for Exit
import typer
