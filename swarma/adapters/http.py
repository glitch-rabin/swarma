"""HTTP adapter -- generic external agent via POST brief/result pattern.

Any agent that speaks HTTP can join the swarm: receive a JSON brief,
return a JSON result. Minimal protocol.

Config example (in agent.yaml):
    runtime: http
    runtime_config:
      endpoint: https://my-agent.example.com/run
      api_key: ${MY_AGENT_KEY}
      method: POST
      timeout: 120
"""

import json
import logging
from typing import Optional

import httpx

from .base import AdapterCapabilities, AdapterResult, RuntimeAdapter

logger = logging.getLogger(__name__)


class HTTPAdapter(RuntimeAdapter):
    """Send brief as POST JSON, receive result as JSON response."""

    def __init__(
        self,
        endpoint: str,
        api_key: Optional[str] = None,
        headers: Optional[dict] = None,
        timeout: float = 120.0,
    ):
        self.endpoint = endpoint
        self.api_key = api_key
        self._extra_headers = headers or {}
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        headers.update(self._extra_headers)
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def execute(self, brief: dict) -> AdapterResult:
        """POST the brief, expect JSON result with at least a 'content' field."""
        client = await self._get_client()

        try:
            resp = await client.post(
                self.endpoint,
                headers=self._headers(),
                json=brief,
            )
            resp.raise_for_status()
            data = resp.json()

            # Flexible response parsing: accept various formats
            if isinstance(data, str):
                return AdapterResult(content=data)

            content = (
                data.get("content")
                or data.get("result")
                or data.get("output")
                or data.get("text")
                or json.dumps(data)
            )

            return AdapterResult(
                content=content,
                model=data.get("model", "external"),
                cost_estimate=data.get("cost", data.get("cost_estimate", 0.0)),
                metadata=data.get("metadata", {}),
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            logger.error("http adapter error: %s", error_msg)
            return AdapterResult(content="", error=error_msg)

        except Exception as e:
            error_msg = f"HTTP adapter failed: {e}"
            logger.error(error_msg)
            return AdapterResult(content="", error=error_msg)

    async def health(self) -> bool:
        try:
            client = await self._get_client()
            resp = await client.get(self.endpoint)
            return resp.status_code < 500
        except Exception:
            return False

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
