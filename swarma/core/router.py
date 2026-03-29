"""Multi-model router via OpenRouter.

Single interface for all LLM calls. Routes to cheapest model that fits the task.
Supports custom routing tables and provider abstraction.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Default routing table -- cheapest model per task type
DEFAULT_ROUTING = {
    "routing": {
        "model": "mistralai/mistral-nemo",
        "cost_per_m_input": 0.02,
        "cost_per_m_output": 0.02,
        "max_tokens": 500,
        "temperature": 0.3,
    },
    "creative_writing": {
        "model": "qwen/qwen3.5-plus-02-15",
        "cost_per_m_input": 0.26,
        "cost_per_m_output": 0.26,
        "max_tokens": 2000,
        "temperature": 0.7,
    },
    "research_summary": {
        "model": "qwen/qwen-2.5-72b-instruct",
        "cost_per_m_input": 0.10,
        "cost_per_m_output": 0.30,
        "max_tokens": 4000,
        "temperature": 0.5,
    },
    "strategic_reasoning": {
        "model": "deepseek/deepseek-r1",
        "cost_per_m_input": 0.55,
        "cost_per_m_output": 2.19,
        "max_tokens": 4000,
        "temperature": 0.6,
    },
    "hard_decisions": {
        "model": "anthropic/claude-sonnet-4-6",
        "cost_per_m_input": 3.00,
        "cost_per_m_output": 15.00,
        "max_tokens": 4000,
        "temperature": 0.5,
    },
    "deep_research": {
        "model": "perplexity/sonar-deep-research",
        "cost_per_m_input": None,
        "cost_per_m_output": None,
        "max_tokens": 8000,
        "temperature": 0.5,
    },
}


@dataclass
class CompletionResult:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_estimate: float = 0.0
    raw_response: dict = field(default_factory=dict)


class ModelRouter:
    """Routes LLM requests to the optimal model via OpenRouter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        routing_table: Optional[dict] = None,
        base_url: str = "https://openrouter.ai/api/v1/chat/completions",
        app_name: str = "swarma",
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        self.base_url = base_url
        self.app_name = app_name
        self.routing_table = routing_table or DEFAULT_ROUTING
        self._client: Optional[httpx.AsyncClient] = None
        self._total_cost = 0.0

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=300.0)
        return self._client

    async def complete(
        self,
        messages: list[dict],
        task_type: str = "creative_writing",
        model_override: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> CompletionResult:
        """Send a completion request routed to the appropriate model."""
        route = self.routing_table.get(task_type)
        if route is None and model_override is None:
            raise ValueError(f"Unknown task_type: {task_type}. Available: {list(self.routing_table)}")

        model = model_override or route["model"]
        tokens = max_tokens or (route["max_tokens"] if route else 2000)
        temp = temperature if temperature is not None else (route["temperature"] if route else 0.7)

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": model,
            "messages": full_messages,
            "max_tokens": tokens,
            "temperature": temp,
        }

        # Add tool definitions if provided
        if tools:
            payload["tools"] = tools

        client = await self._get_client()
        response = await client.post(
            self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": f"https://{self.app_name}.local",
                "X-Title": self.app_name,
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"].get("content") or ""
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        # Estimate cost using per-token rates
        cost = 0.0
        if route and route.get("cost_per_m_input"):
            output_rate = route.get("cost_per_m_output") or route["cost_per_m_input"]
            cost = (input_tokens * route["cost_per_m_input"] / 1_000_000) + \
                   (output_tokens * output_rate / 1_000_000)
        self._total_cost += cost

        logger.info(
            "completion: model=%s tokens_in=%d tokens_out=%d cost=~$%.4f",
            model, input_tokens, output_tokens, cost,
        )

        return CompletionResult(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_estimate=cost,
            raw_response=data,
        )

    @property
    def total_cost(self) -> float:
        return self._total_cost

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
