"""Hermes adapter -- bridge to NousResearch Hermes Agent instances.

Sends briefs via HTTP to a running Hermes agent. Hermes handles MCP tools,
sub-agents, browser, code execution etc. Swarma just sends the task and
gets the result back.

The adapter also exposes Hermes MCP tools back to swarma so other agents
can use them.
"""

import json
import logging
from typing import Optional

import httpx

from .base import AdapterCapabilities, AdapterResult, RuntimeAdapter

logger = logging.getLogger(__name__)


class HermesAdapter(RuntimeAdapter):
    """Bridge to a running Hermes agent instance.

    Config example (in agent.yaml):
        runtime: hermes
        runtime_config:
          endpoint: http://localhost:3000
          api_key: ${HERMES_API_KEY}   # optional
          timeout: 300
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:3000",
        api_key: Optional[str] = None,
        timeout: float = 300.0,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def execute(self, brief: dict) -> AdapterResult:
        """Send a task to Hermes and return the result.

        Uses the Hermes chat/completions-compatible endpoint or
        the delegate_task MCP tool pattern.
        """
        task = brief.get("task", "")
        context = brief.get("context")
        system_prompt = brief.get("system_prompt", "")

        # Build the message for Hermes
        user_content = task
        if context:
            ctx_str = json.dumps(context, indent=2) if isinstance(context, dict) else str(context)
            user_content = f"Context:\n{ctx_str}\n\nTask:\n{task}"

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }

        # Optional model preference (Hermes may ignore)
        if brief.get("model"):
            payload["model"] = brief["model"]

        client = await self._get_client()

        try:
            resp = await client.post(
                f"{self.endpoint}/v1/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})

            return AdapterResult(
                content=content,
                model=data.get("model", "hermes"),
                cost_estimate=0.0,  # Hermes doesn't report cost directly
                metadata={
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                    "source": "hermes",
                },
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"Hermes returned {e.response.status_code}: {e.response.text[:200]}"
            logger.error(error_msg)
            return AdapterResult(content="", error=error_msg)

        except Exception as e:
            error_msg = f"Hermes request failed: {e}"
            logger.error(error_msg)
            return AdapterResult(content="", error=error_msg)

    async def probe(self) -> AdapterCapabilities:
        """Check what Hermes can do by hitting its health/info endpoint."""
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self.endpoint}/health",
                headers=self._headers(),
            )
            if resp.status_code == 200:
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                tools = data.get("tools", [])
                return AdapterCapabilities(
                    mcp=True,
                    streaming=True,
                    sub_agents=True,
                    code_execution=True,
                    browser=True,
                    tools=tools,
                )
        except Exception as e:
            logger.warning("hermes probe failed: %s", e)

        return AdapterCapabilities(mcp=True, sub_agents=True)

    async def health(self) -> bool:
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.endpoint}/health", headers=self._headers())
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
