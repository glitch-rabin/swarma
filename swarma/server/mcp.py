"""MCP server -- expose swarma engine as an MCP tool provider.

Any MCP client (Hermes, Claude Desktop, etc.) can connect and control
the swarma engine: run cycles, query agents, read outputs, manage plans.

Usage:
    swarma serve --mcp                  # stdio transport (default for MCP)
    swarma serve --mcp --http 8383      # HTTP transport
    python -m swarma.server.mcp         # standalone
"""

import asyncio
import json
import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)


# --- Tool definitions (MCP protocol format) ---

TOOLS = [
    {
        "name": "swarma_health",
        "description": "Check engine health: teams, tools, experts count.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "swarma_list_teams",
        "description": "List all teams with their agents, goals, and schedules.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "swarma_get_team",
        "description": "Get detailed info about a specific team.",
        "inputSchema": {
            "type": "object",
            "properties": {"team_id": {"type": "string", "description": "Team ID"}},
            "required": ["team_id"],
        },
    },
    {
        "name": "swarma_list_agents",
        "description": "List all agents across all teams.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "swarma_run_agent",
        "description": "Run a single agent with optional context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Team ID"},
                "agent_id": {"type": "string", "description": "Agent ID"},
                "context": {"type": "object", "description": "Optional context dict"},
            },
            "required": ["team_id", "agent_id"],
        },
    },
    {
        "name": "swarma_run_cycle",
        "description": "Run a full cycle for a team. Returns all agent results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Team ID"},
                "topic": {"type": "string", "description": "Optional topic/task override"},
            },
            "required": ["team_id"],
        },
    },
    {
        "name": "swarma_status",
        "description": "Get engine status: costs, recent runs, queue stats.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "swarma_costs",
        "description": "Get cost breakdown: today, this month, router total.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "swarma_list_plans",
        "description": "List pending plans awaiting approval.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "swarma_approve_plan",
        "description": "Approve a pending plan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "integer", "description": "Plan ID to approve"},
                "reason": {"type": "string", "description": "Optional approval reason"},
            },
            "required": ["plan_id"],
        },
    },
    {
        "name": "swarma_reject_plan",
        "description": "Reject a pending plan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "integer", "description": "Plan ID to reject"},
                "reason": {"type": "string", "description": "Optional rejection reason"},
            },
            "required": ["plan_id"],
        },
    },
    {
        "name": "swarma_get_outputs",
        "description": "Get recent outputs, optionally filtered by team.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Filter by team ID"},
                "limit": {"type": "integer", "description": "Max results (default 20)"},
            },
        },
    },
    {
        "name": "swarma_list_tools",
        "description": "List all installed tools in the registry.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "swarma_list_experts",
        "description": "List all experts in the catalog.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "swarma_get_expert",
        "description": "Get detailed info about an expert by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expert_id": {"type": "integer", "description": "Expert ID number"},
            },
            "required": ["expert_id"],
        },
    },
]


class MCPServer:
    """Swarma MCP server. Wraps the engine and handles JSON-RPC messages."""

    def __init__(self, engine=None):
        self.engine = engine
        self._handlers = {
            "swarma_health": self._handle_health,
            "swarma_list_teams": self._handle_list_teams,
            "swarma_get_team": self._handle_get_team,
            "swarma_list_agents": self._handle_list_agents,
            "swarma_run_agent": self._handle_run_agent,
            "swarma_run_cycle": self._handle_run_cycle,
            "swarma_status": self._handle_status,
            "swarma_costs": self._handle_costs,
            "swarma_list_plans": self._handle_list_plans,
            "swarma_approve_plan": self._handle_approve_plan,
            "swarma_reject_plan": self._handle_reject_plan,
            "swarma_get_outputs": self._handle_get_outputs,
            "swarma_list_tools": self._handle_list_tools,
            "swarma_list_experts": self._handle_list_experts,
            "swarma_get_expert": self._handle_get_expert,
        }

    def _require_engine(self):
        if self.engine is None:
            raise RuntimeError("Engine not initialized")
        return self.engine

    # --- JSON-RPC message handling ---

    async def handle_message(self, message: dict) -> dict:
        """Handle a single JSON-RPC message and return a response."""
        method = message.get("method", "")
        msg_id = message.get("id")
        params = message.get("params", {})

        if method == "initialize":
            return self._rpc_response(msg_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "swarma", "version": "0.1.0"},
            })

        if method == "notifications/initialized":
            return None  # No response for notifications

        if method == "tools/list":
            return self._rpc_response(msg_id, {"tools": TOOLS})

        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            return await self._handle_tool_call(msg_id, tool_name, arguments)

        if method == "ping":
            return self._rpc_response(msg_id, {})

        # Unknown method
        return self._rpc_error(msg_id, -32601, f"Method not found: {method}")

    async def _handle_tool_call(self, msg_id, tool_name: str, arguments: dict) -> dict:
        """Execute a tool call and return the result."""
        handler = self._handlers.get(tool_name)
        if not handler:
            return self._rpc_error(msg_id, -32602, f"Unknown tool: {tool_name}")

        try:
            result = await handler(arguments)
            content = json.dumps(result, indent=2, default=str)
            return self._rpc_response(msg_id, {
                "content": [{"type": "text", "text": content}],
            })
        except Exception as e:
            logger.error("tool %s failed: %s", tool_name, e)
            return self._rpc_response(msg_id, {
                "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                "isError": True,
            })

    def _rpc_response(self, msg_id, result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _rpc_error(self, msg_id, code: int, message: str) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}

    # --- Tool handlers ---

    async def _handle_health(self, args: dict) -> dict:
        eng = self._require_engine()
        return {
            "status": "ok",
            "teams": list(eng.teams.keys()),
            "tools": eng.tool_registry.list_names() if eng.tool_registry else [],
            "experts": eng.expert_catalog.count if eng.expert_catalog else 0,
        }

    async def _handle_list_teams(self, args: dict) -> dict:
        eng = self._require_engine()
        return {
            tid: {
                "name": t.name, "goal": t.goal, "flow": t.flow,
                "agents": list(t.agents.keys()), "tools": t.tools,
            }
            for tid, t in eng.teams.items()
        }

    async def _handle_get_team(self, args: dict) -> dict:
        eng = self._require_engine()
        team = eng.teams.get(args["team_id"])
        if not team:
            raise ValueError(f"Team '{args['team_id']}' not found")
        return {
            "id": team.id, "name": team.name, "goal": team.goal,
            "flow": team.flow, "agents": {
                aid: {"name": a.name, "model": a.model.model_id, "tools": a.tools}
                for aid, a in team.agents.items()
            },
        }

    async def _handle_list_agents(self, args: dict) -> dict:
        eng = self._require_engine()
        agents = {}
        for tid, t in eng.teams.items():
            for aid, a in t.agents.items():
                agents[f"{tid}/{aid}"] = {
                    "team": tid, "name": a.name,
                    "model": a.model.model_id, "runtime": a.runtime,
                }
        return agents

    async def _handle_run_agent(self, args: dict) -> dict:
        eng = self._require_engine()
        runner = eng._runners.get(args["team_id"])
        if not runner:
            raise ValueError(f"Team '{args['team_id']}' not found")
        agent = runner._agents.get(args["agent_id"])
        if not agent:
            raise ValueError(f"Agent '{args['agent_id']}' not found")
        return await agent.run(args.get("context"))

    async def _handle_run_cycle(self, args: dict) -> dict:
        eng = self._require_engine()
        context = {}
        if args.get("topic"):
            context = {"topic": args["topic"], "task": args["topic"]}
        return await eng.run_cycle(args["team_id"], context or None)

    async def _handle_status(self, args: dict) -> dict:
        eng = self._require_engine()
        state = eng.state
        daily = state.get_daily_cost()
        monthly = state.get_monthly_cost()
        runs = state.conn.execute(
            "SELECT agent_id, status, started_at FROM agent_runs ORDER BY id DESC LIMIT 10"
        ).fetchall()
        return {
            "costs": {"today": daily, "this_month": monthly},
            "recent_runs": [
                {"agent_id": r["agent_id"], "status": r["status"], "started_at": r["started_at"]}
                for r in runs
            ],
            "queue": state.get_queue_stats(),
        }

    async def _handle_costs(self, args: dict) -> dict:
        eng = self._require_engine()
        return {
            "today": eng.state.get_daily_cost(),
            "this_month": eng.state.get_monthly_cost(),
            "router_total": eng.router.total_cost,
        }

    async def _handle_list_plans(self, args: dict) -> dict:
        eng = self._require_engine()
        plans = eng.state.get_pending_plans()
        return {"pending": len(plans), "plans": plans}

    async def _handle_approve_plan(self, args: dict) -> dict:
        eng = self._require_engine()
        eng.state.approve_plan(args["plan_id"])
        return {"status": "approved", "plan_id": args["plan_id"]}

    async def _handle_reject_plan(self, args: dict) -> dict:
        eng = self._require_engine()
        eng.state.reject_plan(args["plan_id"])
        return {"status": "rejected", "plan_id": args["plan_id"]}

    async def _handle_get_outputs(self, args: dict) -> list:
        eng = self._require_engine()
        limit = args.get("limit", 20)
        team_id = args.get("team_id")
        if team_id:
            query = "SELECT * FROM outputs WHERE team_id = ? ORDER BY id DESC LIMIT ?"
            params = [team_id, limit]
        else:
            query = "SELECT * FROM outputs ORDER BY id DESC LIMIT ?"
            params = [limit]
        rows = eng.state.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    async def _handle_list_tools(self, args: dict) -> dict:
        eng = self._require_engine()
        if not eng.tool_registry:
            return {}
        return {
            name: {"type": (eng.tool_registry.get_config(name).type
                           if eng.tool_registry.get_config(name) else "unknown")}
            for name in eng.tool_registry.list_names()
        }

    async def _handle_list_experts(self, args: dict) -> list:
        eng = self._require_engine()
        if not eng.expert_catalog:
            return []
        return [
            {"id": e.id, "name": e.name, "domain": e.domain}
            for e in eng.expert_catalog.list_all()
        ]

    async def _handle_get_expert(self, args: dict) -> dict:
        eng = self._require_engine()
        if not eng.expert_catalog:
            raise ValueError("Expert catalog not loaded")
        expert = eng.expert_catalog.get(args["expert_id"])
        if not expert:
            raise ValueError(f"Expert {args['expert_id']} not found")
        return {
            "id": expert.id, "name": expert.name,
            "domain": expert.domain, "core_thesis": expert.core_thesis,
            "operating_beliefs": expert.operating_beliefs,
            "key_questions": expert.key_questions,
            "frameworks": len(expert.frameworks),
        }

    # --- Transport: stdio ---

    async def run_stdio(self):
        """Run MCP server over stdio (for MCP client integration)."""
        logger.info("swarma MCP server starting (stdio)")
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin.buffer)

        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout.buffer
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                message = json.loads(line)
                response = await self.handle_message(message)

                if response is not None:
                    out = json.dumps(response) + "\n"
                    writer.write(out.encode())
                    await writer.drain()

            except json.JSONDecodeError as e:
                logger.warning("invalid JSON: %s", e)
            except Exception as e:
                logger.error("stdio error: %s", e)
                break

    # --- Transport: HTTP (streamable) ---

    async def run_http(self, host: str = "0.0.0.0", port: int = 8383):
        """Run MCP server over HTTP for remote clients."""
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
        import uvicorn

        http_app = FastAPI(title="swarma MCP", version="0.1.0")

        @http_app.post("/mcp")
        async def mcp_endpoint(request: Request):
            body = await request.json()
            response = await self.handle_message(body)
            if response is None:
                return JSONResponse({"status": "ok"})
            return JSONResponse(response)

        @http_app.get("/health")
        async def health():
            return {"status": "ok", "server": "swarma-mcp"}

        config = uvicorn.Config(http_app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        logger.info("swarma MCP server starting (HTTP %s:%d)", host, port)
        await server.serve()


async def main():
    """Standalone entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="swarma MCP server")
    parser.add_argument("--http", type=int, default=0, help="HTTP port (0 = stdio)")
    parser.add_argument("--instance", default="default", help="Instance name")
    args = parser.parse_args()

    # Build engine from instance
    from ..cli.helpers import build_engine, get_instance_path, load_env

    instance_path = get_instance_path(args.instance)
    if instance_path.exists():
        load_env(instance_path)
        engine = build_engine(instance_path)
    else:
        engine = None
        logger.warning("instance '%s' not found, running without engine", args.instance)

    server = MCPServer(engine=engine)

    if args.http > 0:
        await server.run_http(port=args.http)
    else:
        await server.run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
