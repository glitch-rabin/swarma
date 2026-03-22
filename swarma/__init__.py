"""swarma -- learning agent swarms that get smarter every cycle.

Quick start:
    from swarma import Team, Agent, Flow, Engine

    team = Team(name="content", goal="build personal brand")
    team.add_agent(Agent(name="researcher", model="perplexity/sonar-pro"))
    team.add_agent(Agent(name="writer", model="qwen/qwen3.5-plus-02-15"))
    team.flow = "researcher -> writer"

    engine = Engine.from_teams([team], api_key="sk-...")
    result = await engine.run_cycle("content")
"""

__version__ = "0.1.0"

from .core.agent import Agent
from .core.config import AgentConfig, InstanceConfig, TeamConfig, load_all_teams
from .core.cycle import CycleRunner, Engine
from .core.experiment import ExperimentEngine
from .core.knowledge import KnowledgeStore
from .core.router import CompletionResult, ModelRouter
from .core.state import StateDB
from .flow.parser import Flow, FlowStep, parse_flow
from .tools.base import Tool, ToolDefinition, ToolResult
from .tools.registry import ToolRegistry
from .experts.catalog import Expert, ExpertCatalog
from .server.app import create_app
from .server.mcp import MCPServer

__all__ = [
    "Agent",
    "AgentConfig",
    "CompletionResult",
    "CycleRunner",
    "Engine",
    "Expert",
    "ExpertCatalog",
    "ExperimentEngine",
    "Flow",
    "FlowStep",
    "InstanceConfig",
    "KnowledgeStore",
    "MCPServer",
    "ModelRouter",
    "StateDB",
    "TeamConfig",
    "Tool",
    "ToolDefinition",
    "ToolRegistry",
    "ToolResult",
    "create_app",
    "load_all_teams",
    "parse_flow",
]
