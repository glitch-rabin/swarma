"""swarma CLI -- the main entrypoint.

Usage:
    swarma init              # scaffold a new instance
    swarma run               # start the engine
    swarma serve             # start API + MCP servers
    swarma cycle [team]      # run one cycle
    swarma status            # show current state
    swarma team list         # list teams
    swarma team create       # create a new team
    swarma team show [name]  # show team details
"""

import typer

from .init import init_command
from .run import run_command
from .serve import serve_command
from .cycle import cycle_command
from .status import status_command
from .expert import expert_app
from .team import team_app
from .tool import tool_app

app = typer.Typer(
    name="swarma",
    help="Learning agent swarms that get smarter every cycle.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

app.command("init")(init_command)
app.command("run")(run_command)
app.command("serve")(serve_command)
app.command("cycle")(cycle_command)
app.command("status")(status_command)
app.add_typer(team_app, name="team")
app.add_typer(tool_app, name="tool")
app.add_typer(expert_app, name="expert")


if __name__ == "__main__":
    app()
