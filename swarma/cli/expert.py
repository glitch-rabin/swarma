"""swarma expert -- browse and assign expert reasoning lenses.

Commands:
    swarma expert list               # list all available experts
    swarma expert show <id>          # show expert details
    swarma expert search <query>     # search by name/domain
    swarma expert compose <ids>      # preview composed prompt for IDs
"""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .helpers import get_instance_path, load_env, load_instance_config, require_instance

console = Console()

expert_app = typer.Typer(
    name="expert",
    help="Browse and compose expert reasoning lenses.",
    no_args_is_help=True,
)


def _load_catalog(instance: str):
    """Load the expert catalog from instance config or default paths."""
    from ..experts.catalog import ExpertCatalog

    catalog = ExpertCatalog()

    # Try instance-specific expert path first
    instance_path = get_instance_path(instance)
    if instance_path.exists():
        load_env(instance_path)
        config_path = instance_path / "config.yaml"
        if config_path.exists():
            config = load_instance_config(instance_path)
            expert_path = config.runtimes.get("expert_catalog_path")
            if expert_path:
                catalog.load_directory(expert_path)
                return catalog
            # Also check instance/experts/ directory
            inst_experts = instance_path / "experts"
            if inst_experts.exists():
                catalog.load_directory(str(inst_experts))
                if catalog.count > 0:
                    return catalog

    # Fall back to well-known locations
    import os
    search_paths = [
        os.path.expanduser("~/.swarma/experts"),
        os.path.join(os.getcwd(), "references", "43-experts"),
        os.path.join(os.getcwd(), "experts"),
    ]

    # Also check SWARMA_EXPERTS env var
    env_path = os.environ.get("SWARMA_EXPERTS")
    if env_path:
        search_paths.insert(0, env_path)

    for path in search_paths:
        if os.path.isdir(path):
            catalog.load_directory(path)
            if catalog.count > 0:
                return catalog

    return catalog


@expert_app.command("list")
def expert_list(
    instance: str = typer.Option("default", help="Instance name"),
):
    """List all available experts in the catalog."""
    catalog = _load_catalog(instance)

    if catalog.count == 0:
        console.print("[dim]No experts found. Set SWARMA_EXPERTS or add experts to ~/.swarma/experts/[/dim]")
        return

    table = Table(title=f"Expert Catalog ({catalog.count} experts)")
    table.add_column("ID", style="bold", width=4)
    table.add_column("Name", width=25)
    table.add_column("Domain", width=40)

    for e in catalog.list_all():
        table.add_row(str(e.id), e.name, e.domain)

    console.print(table)


@expert_app.command("show")
def expert_show(
    expert_id: int = typer.Argument(help="Expert ID number"),
    instance: str = typer.Option("default", help="Instance name"),
):
    """Show detailed info about an expert."""
    catalog = _load_catalog(instance)
    expert = catalog.get(expert_id)

    if not expert:
        console.print(f"[red]Expert {expert_id} not found.[/red]")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold]{expert.name}[/bold]\n"
        f"Domain: {expert.domain}\n\n"
        f"[italic]{expert.core_thesis}[/italic]",
        title=f"Expert #{expert.id}",
    ))

    if expert.operating_beliefs:
        console.print("\n[bold]Operating Beliefs:[/bold]")
        for b in expert.operating_beliefs:
            console.print(f"  - {b}")

    if expert.key_questions:
        console.print("\n[bold]Key Questions:[/bold]")
        for q in expert.key_questions:
            console.print(f"  - {q}")

    if expert.biases:
        console.print("\n[bold]Biases:[/bold]")
        for b in expert.biases:
            console.print(f"  - {b}")

    if expert.frameworks:
        console.print(f"\n[bold]Frameworks:[/bold] {len(expert.frameworks)}")
        for fw in expert.frameworks:
            console.print(f"  - {fw.get('name', 'unnamed')}: {fw.get('purpose', '')[:80]}")

    console.print()


@expert_app.command("search")
def expert_search(
    query: str = typer.Argument(help="Search term (name, domain, or thesis)"),
    instance: str = typer.Option("default", help="Instance name"),
):
    """Search experts by name or domain."""
    catalog = _load_catalog(instance)
    results = catalog.search(query)

    if not results:
        console.print(f"[dim]No experts matching '{query}'[/dim]")
        return

    table = Table(title=f"Search: '{query}' ({len(results)} results)")
    table.add_column("ID", style="bold", width=4)
    table.add_column("Name", width=25)
    table.add_column("Domain", width=40)

    for e in results:
        table.add_row(str(e.id), e.name, e.domain)

    console.print(table)


@expert_app.command("compose")
def expert_compose(
    ids: str = typer.Argument(help="Comma-separated expert IDs (e.g. '1,6,20')"),
    frameworks: bool = typer.Option(False, "--frameworks", "-f", help="Include framework details"),
    instance: str = typer.Option("default", help="Instance name"),
):
    """Preview the composed prompt section for selected experts."""
    catalog = _load_catalog(instance)

    expert_ids = [int(x.strip()) for x in ids.split(",") if x.strip()]
    experts = catalog.get_multiple(expert_ids)

    if not experts:
        console.print("[red]No valid experts found for given IDs.[/red]")
        raise typer.Exit(1)

    from ..experts.composer import compose_prompt_section

    prompt = compose_prompt_section(experts, include_frameworks=frameworks)

    console.print(Panel(
        f"[bold]Composed Reasoning Lenses[/bold]\n"
        f"Experts: {', '.join(e.name for e in experts)}\n"
        f"Token estimate: ~{len(prompt.split()) * 1.3:.0f} tokens",
        title="Preview",
    ))
    console.print()
    console.print(prompt)
    console.print()

    # Show the YAML config snippet
    id_list = [e.id for e in experts]
    console.print("[bold]Add to agent.yaml:[/bold]")
    console.print(f"  expert_lenses: {id_list}")
