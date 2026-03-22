"""Tool interface and built-in tool implementations.

A Tool is something an agent can call during execution. Tools are:
1. Installed at instance level (with credentials)
2. Granted to teams
3. Assigned to agents

Tools get injected into the LLM call as function definitions.
The router handles tool call execution and returns results.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """OpenAI-compatible function definition for LLM tool calling."""
    name: str
    description: str
    parameters: dict = field(default_factory=lambda: {"type": "object", "properties": {}})


@dataclass
class ToolResult:
    """Result from executing a tool."""
    content: str
    success: bool = True
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class Tool(ABC):
    """Base tool interface. All tools implement this."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """Return the function definition for LLM tool calling."""
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        ...

    async def test(self) -> bool:
        """Test that the tool works (credentials valid, endpoint reachable)."""
        return True


# --- Built-in Tools ---

class WebSearchTool(Tool):
    """Search the web via DuckDuckGo (no API key needed)."""

    name = "web_search"
    description = "Search the web for information"

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        )

    async def execute(self, query: str = "", **kwargs) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "swarma/0.1"},
                    follow_redirects=True,
                )
                # Extract text snippets (basic parsing)
                text = resp.text
                results = []
                for block in text.split('class="result__snippet"')[1:6]:
                    snippet = block.split(">", 1)[-1].split("<", 1)[0].strip()
                    if snippet:
                        results.append(snippet)
                return ToolResult(content="\n\n".join(results) if results else "No results found.")
        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))


class WebFetchTool(Tool):
    """Fetch content from a URL."""

    name = "web_fetch"
    description = "Fetch the text content of a web page"

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                },
                "required": ["url"],
            },
        )

    async def execute(self, url: str = "", **kwargs) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "swarma/0.1"})
                # Strip HTML tags (basic)
                import re
                text = re.sub(r"<[^>]+>", " ", resp.text)
                text = re.sub(r"\s+", " ", text).strip()
                return ToolResult(content=text[:5000])
        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))


class APITool(Tool):
    """Generic API tool -- calls an HTTP endpoint with configured auth."""

    def __init__(self, name: str, description: str, endpoint: str,
                 method: str = "GET", headers: Optional[dict] = None,
                 params_schema: Optional[dict] = None):
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.method = method.upper()
        self._headers = headers or {}
        self._params_schema = params_schema or {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "API query parameter"},
            },
        }

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self._params_schema,
        )

    async def execute(self, **kwargs) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if self.method == "GET":
                    resp = await client.get(
                        self.endpoint, params=kwargs, headers=self._headers,
                    )
                else:
                    resp = await client.post(
                        self.endpoint, json=kwargs, headers=self._headers,
                    )
                resp.raise_for_status()
                return ToolResult(content=resp.text[:5000])
        except Exception as e:
            return ToolResult(content="", success=False, error=str(e))

    async def test(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    self.endpoint, headers=self._headers, params={"q": "test"},
                )
                return resp.status_code < 500
        except Exception:
            return False


# Registry of built-in tools (no credentials needed)
BUILTIN_TOOLS = {
    "web_search": WebSearchTool,
    "web_fetch": WebFetchTool,
}
