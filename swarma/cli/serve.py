"""swarma serve -- start the API server and/or MCP server.

Usage:
    swarma serve                    # API on :8282
    swarma serve --port 9090        # API on custom port
    swarma serve --mcp              # MCP server (stdio)
    swarma serve --mcp --http 8383  # MCP server (HTTP)
    swarma serve --port 8282 --mcp --http 8383  # both
"""

import asyncio

import typer
from rich.console import Console

from .helpers import build_engine, get_instance_path, load_env, require_instance

console = Console()


def serve_command(
    instance: str = typer.Option("default", help="Instance name"),
    port: int = typer.Option(8282, help="API server port (0 = disabled)"),
    mcp: bool = typer.Option(False, "--mcp", help="Enable MCP server"),
    http: int = typer.Option(0, "--http", help="MCP HTTP port (0 = stdio transport)"),
):
    """Start the swarma API server and/or MCP server."""
    instance_path = get_instance_path(instance)

    # In MCP stdio mode, all output must go to stderr to keep stdout clean for JSON-RPC
    import sys
    if mcp and http == 0:
        log_console = Console(file=sys.stderr)
    else:
        log_console = console

    engine = None
    if instance_path.exists():
        load_env(instance_path)
        engine = build_engine(instance_path)
        log_console.print(f"[bold]swarma[/bold] serve")
        log_console.print(f"  instance: {instance}")
        log_console.print(f"  teams: {list(engine.teams.keys())}")
    else:
        log_console.print(f"[yellow]Instance '{instance}' not found. Running without engine.[/yellow]")

    if not mcp and port == 0:
        console.print("[red]Nothing to serve.[/red] Use --port or --mcp.")
        raise typer.Exit(1)

    # Create the app before entering asyncio to avoid import-ordering issues
    api_app = None
    if port > 0 and engine:
        from ..server.app import create_app
        api_app = create_app(engine)

    asyncio.run(_serve(engine, api_app, port, mcp, http))


async def _serve(engine, api_app, api_port: int, mcp_enabled: bool, mcp_http_port: int):
    """Run API and/or MCP server."""
    tasks = []

    if mcp_enabled and mcp_http_port == 0:
        # stdio MCP mode: ONLY run MCP, no API server (it would corrupt stdout)
        await _run_mcp_stdio(engine)
        return

    if api_port > 0 and api_app:
        tasks.append(_run_api(api_app, api_port))

    if mcp_enabled:
        if mcp_http_port > 0:
            tasks.append(_run_mcp_http(engine, mcp_http_port))
        else:
            tasks.append(_run_mcp_stdio(engine))

    if tasks:
        await asyncio.gather(*tasks)


async def _run_api(app, port: int):
    """Start the FastAPI server."""
    import uvicorn

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    console.print(f"  API: http://0.0.0.0:{port}")
    await server.serve()


async def _run_mcp_stdio(engine):
    """Start MCP server on stdio."""
    import sys
    from ..server.mcp import MCPServer

    # Log to stderr only — stdout is reserved for JSON-RPC
    Console(file=sys.stderr).print("  MCP: stdio")
    server = MCPServer(engine=engine)
    await server.run_stdio()


async def _run_mcp_http(engine, port: int):
    """Start MCP server on HTTP."""
    from ..server.mcp import MCPServer

    console.print(f"  MCP: http://0.0.0.0:{port}/mcp")
    server = MCPServer(engine=engine)
    await server.run_http(port=port)
