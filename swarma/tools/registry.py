"""Three-layer tool registry.

Layer 1 - Instance: All installed tools with credentials
Layer 2 - Team: Which tools a team can access (grants)
Layer 3 - Agent: Which tools an agent uses per run (assignments)

Tools are configured in config.yaml (instance level) and team.yaml
(team grants). Agent assignments come from agent YAML configs.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from .base import BUILTIN_TOOLS, APITool, Tool, ToolDefinition, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class ToolConfig:
    """Parsed tool config from config.yaml."""
    name: str
    type: str = "builtin"  # builtin | api | mcp
    provider: Optional[str] = None
    endpoint: Optional[str] = None
    method: str = "GET"
    description: str = ""
    credentials: dict = field(default_factory=dict)
    params_schema: Optional[dict] = None
    rate_limit: Optional[str] = None


class ToolRegistry:
    """Manages tools across all three layers."""

    def __init__(self):
        self._instance_tools: dict[str, Tool] = {}
        self._tool_configs: dict[str, ToolConfig] = {}

    def install(self, config: ToolConfig) -> Tool:
        """Install a tool at instance level (Layer 1).

        Creates the Tool object from config, stores it in the registry.
        """
        self._tool_configs[config.name] = config

        if config.type == "builtin":
            cls = BUILTIN_TOOLS.get(config.name)
            if not cls:
                raise ValueError(f"Unknown builtin tool: {config.name}. Available: {list(BUILTIN_TOOLS)}")
            tool = cls()
        elif config.type == "api":
            # Resolve credential env vars
            headers = {}
            for key, val in config.credentials.items():
                resolved = _expand_env(str(val))
                if key.lower() in ("api_key", "apikey"):
                    headers["X-API-Key"] = resolved
                elif key.lower() in ("bearer", "token"):
                    headers["Authorization"] = f"Bearer {resolved}"
                else:
                    headers[key] = resolved

            tool = APITool(
                name=config.name,
                description=config.description or f"API tool: {config.provider or config.name}",
                endpoint=config.endpoint or "",
                method=config.method,
                headers=headers,
                params_schema=config.params_schema,
            )
        elif config.type == "mcp":
            # MCP tools are handled separately (via adapter)
            # Store config but don't create a Tool object
            logger.info("MCP tool registered: %s (endpoint: %s)", config.name, config.endpoint)
            return None
        else:
            raise ValueError(f"Unknown tool type: {config.type}")

        self._instance_tools[config.name] = tool
        logger.info("tool installed: %s (type=%s)", config.name, config.type)
        return tool

    def install_from_dict(self, name: str, data: dict) -> Optional[Tool]:
        """Install a tool from a config dict (parsed from YAML)."""
        config = ToolConfig(
            name=name,
            type=data.get("type", "builtin"),
            provider=data.get("provider"),
            endpoint=data.get("endpoint"),
            method=data.get("method", "GET"),
            description=data.get("description", ""),
            credentials=data.get("credentials", {}),
            params_schema=data.get("params_schema"),
            rate_limit=data.get("rate_limit"),
        )
        return self.install(config)

    def load_from_config(self, tools_config: dict):
        """Load all tools from the instance config.yaml tools section.

        tools_config example:
            web_search:
              type: builtin
            twitter_api:
              type: api
              provider: twitterapi.io
              endpoint: https://api.twitterapi.io/twitter/tweet/advanced_search
              credentials:
                api_key: ${TWITTER_API_KEY}
        """
        for name, data in tools_config.items():
            try:
                self.install_from_dict(name, data or {})
            except Exception as e:
                logger.warning("failed to install tool %s: %s", name, e)

    def get(self, name: str) -> Optional[Tool]:
        """Get an installed tool by name."""
        return self._instance_tools.get(name)

    def get_config(self, name: str) -> Optional[ToolConfig]:
        """Get tool config by name."""
        return self._tool_configs.get(name)

    @property
    def installed(self) -> dict[str, Tool]:
        """All installed tools."""
        return dict(self._instance_tools)

    def list_names(self) -> list[str]:
        """List all installed tool names."""
        return list(self._instance_tools.keys())

    # --- Layer 2: Team grants ---

    def get_team_tools(self, team_tool_names: list[str]) -> dict[str, Tool]:
        """Get tools granted to a team.

        team_tool_names: list of tool names from team.yaml
        Returns only tools that are both installed AND granted.
        """
        tools = {}
        for name in team_tool_names:
            tool = self._instance_tools.get(name)
            if tool:
                tools[name] = tool
            else:
                logger.warning("team references tool '%s' but it's not installed", name)
        return tools

    # --- Layer 3: Agent assignments ---

    def get_agent_tools(self, agent_tool_names: list[str],
                        team_tool_names: list[str]) -> dict[str, Tool]:
        """Get tools assigned to an agent.

        Only returns tools that are:
        1. Installed at instance level
        2. Granted to the team
        3. Assigned to the agent
        """
        team_tools = set(team_tool_names) if team_tool_names else set(self._instance_tools.keys())
        tools = {}
        for name in agent_tool_names:
            if name not in team_tools:
                logger.warning("agent references tool '%s' but team doesn't have it", name)
                continue
            tool = self._instance_tools.get(name)
            if tool:
                tools[name] = tool
        return tools

    def get_definitions(self, tool_names: list[str]) -> list[dict]:
        """Get OpenAI-compatible function definitions for a list of tools.

        Used when making LLM calls with tool_use.
        """
        definitions = []
        for name in tool_names:
            tool = self._instance_tools.get(name)
            if tool:
                defn = tool.get_definition()
                definitions.append({
                    "type": "function",
                    "function": {
                        "name": defn.name,
                        "description": defn.description,
                        "parameters": defn.parameters,
                    },
                })
        return definitions

    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self._instance_tools.get(tool_name)
        if not tool:
            return ToolResult(content="", success=False, error=f"Tool '{tool_name}' not found")
        return await tool.execute(**kwargs)

    async def test_tool(self, name: str) -> bool:
        """Test if a tool works."""
        tool = self._instance_tools.get(name)
        if not tool:
            return False
        return await tool.test()


def _expand_env(value: str) -> str:
    """Expand ${VAR} in strings."""
    if "${" in value:
        import re
        def _replace(m):
            return os.environ.get(m.group(1), m.group(0))
        return re.sub(r"\$\{(\w+)\}", _replace, value)
    return value
