"""swarma tool -- manage instance-level tools.

Commands:
    swarma tool list                 # list installed tools
    swarma tool add <name> [opts]    # install a tool
    swarma tool test <name>          # test a tool
    swarma tool remove <name>        # remove a tool from config
"""

import asyncio
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from .helpers import load_env, load_instance_config, require_instance

console = Console()

tool_app = typer.Typer(
    name="tool",
    help="Manage tools (install, test, remove).",
    no_args_is_help=True,
)


@tool_app.command("list")
def tool_list(
    instance: str = typer.Option("default", help="Instance name"),
):
    """List all installed tools."""
    instance_path = require_instance(instance)
    load_env(instance_path)

    config = load_instance_config(instance_path)
    tools_cfg = config.tools or {}

    if not tools_cfg:
        console.print("[dim]No tools configured. Run [bold]swarma tool add[/bold] to install one.[/dim]")
        return

    table = Table(title="Installed Tools")
    table.add_column("Name", style="bold")
    table.add_column("Type")
    table.add_column("Provider")
    table.add_column("Endpoint")

    for name, data in tools_cfg.items():
        data = data or {}
        table.add_row(
            name,
            data.get("type", "builtin"),
            data.get("provider", "-"),
            data.get("endpoint", "-"),
        )

    console.print(table)


@tool_app.command("add")
def tool_add(
    name: str = typer.Argument(help="Tool name (e.g. web_search, twitter_api)"),
    tool_type: str = typer.Option("builtin", "--type", "-t", help="Tool type: builtin, api, mcp"),
    provider: Optional[str] = typer.Option(None, help="Provider name"),
    endpoint: Optional[str] = typer.Option(None, help="API endpoint URL"),
    method: str = typer.Option("GET", help="HTTP method for API tools"),
    description: Optional[str] = typer.Option(None, help="Tool description"),
    instance: str = typer.Option("default", help="Instance name"),
):
    """Install a tool to the instance."""
    instance_path = require_instance(instance)
    config_path = instance_path / "config.yaml"

    with open(config_path) as f:
        config_data = yaml.safe_load(f) or {}

    if "tools" not in config_data:
        config_data["tools"] = {}

    tool_entry = {"type": tool_type}
    if provider:
        tool_entry["provider"] = provider
    if endpoint:
        tool_entry["endpoint"] = endpoint
    if method != "GET":
        tool_entry["method"] = method
    if description:
        tool_entry["description"] = description

    # For builtin tools, minimal config
    if tool_type == "builtin":
        tool_entry = {"type": "builtin"}

    config_data["tools"][name] = tool_entry

    with open(config_path, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Tool installed:[/green] {name} (type={tool_type})")

    if tool_type == "api" and not endpoint:
        console.print("[yellow]Note: API tools need an endpoint. Edit config.yaml to add it.[/yellow]")


@tool_app.command("test")
def tool_test(
    name: str = typer.Argument(help="Tool name to test"),
    instance: str = typer.Option("default", help="Instance name"),
):
    """Test if a tool works (credentials valid, endpoint reachable)."""
    instance_path = require_instance(instance)
    load_env(instance_path)

    config = load_instance_config(instance_path)
    tools_cfg = config.tools or {}

    if name not in tools_cfg:
        console.print(f"[red]Tool '{name}' not found in config.[/red]")
        console.print(f"Available: {list(tools_cfg.keys())}")
        raise typer.Exit(1)

    from ..tools.registry import ToolRegistry

    registry = ToolRegistry()
    registry.install_from_dict(name, tools_cfg[name] or {})

    result = asyncio.run(_test_tool(registry, name))

    if result:
        console.print(f"[green]Tool '{name}' is working.[/green]")
    else:
        console.print(f"[red]Tool '{name}' test failed.[/red]")
        raise typer.Exit(1)


async def _test_tool(registry, name):
    return await registry.test_tool(name)


@tool_app.command("remove")
def tool_remove(
    name: str = typer.Argument(help="Tool name to remove"),
    instance: str = typer.Option("default", help="Instance name"),
):
    """Remove a tool from the instance config."""
    instance_path = require_instance(instance)
    config_path = instance_path / "config.yaml"

    with open(config_path) as f:
        config_data = yaml.safe_load(f) or {}

    tools = config_data.get("tools", {})
    if name not in tools:
        console.print(f"[red]Tool '{name}' not found.[/red]")
        raise typer.Exit(1)

    del tools[name]
    config_data["tools"] = tools

    with open(config_path, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]Tool removed:[/green] {name}")
