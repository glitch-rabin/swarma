"""Runtime adapter interface.

Any agent runtime must implement these 3 methods.
The default LLM adapter (direct OpenRouter calls) is the simplest.
Hermes, OpenClaw, Claude Code etc. implement the same interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AdapterCapabilities:
    """What a runtime can do, discovered via probe()."""
    mcp: bool = False
    streaming: bool = False
    sub_agents: bool = False
    code_execution: bool = False
    browser: bool = False
    tools: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)


@dataclass
class AdapterResult:
    """Standard result from any adapter."""
    content: str
    metadata: dict = field(default_factory=dict)
    cost_estimate: float = 0.0
    model: str = ""
    error: Optional[str] = None


class RuntimeAdapter(ABC):
    """Base interface for agent runtimes."""

    @abstractmethod
    async def execute(self, brief: dict) -> AdapterResult:
        """Send a task, get a result. The only hard requirement.

        Args:
            brief: {
                "task": str,         # What to do
                "context": dict,     # Input from previous agents
                "system_prompt": str, # Agent system prompt
                "tools": list[str],  # Available tools
                "model": str,        # Preferred model (adapter may ignore)
                "max_tokens": int,
                "temperature": float,
            }
        """
        ...

    async def probe(self) -> AdapterCapabilities:
        """What can this runtime do? Called once on registration."""
        return AdapterCapabilities()

    async def health(self) -> bool:
        """Is this runtime alive?"""
        return True

    async def close(self):
        """Cleanup resources."""
        pass
