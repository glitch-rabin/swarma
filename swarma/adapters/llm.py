"""LLM adapter -- direct API calls via OpenRouter.

This is the default runtime. Most agents use this. It's just a thin
wrapper around ModelRouter that conforms to the RuntimeAdapter interface.
"""

from typing import Optional

from .base import AdapterCapabilities, AdapterResult, RuntimeAdapter
from ..core.router import CompletionResult, ModelRouter


class LLMAdapter(RuntimeAdapter):
    """Direct LLM calls via OpenRouter. Default runtime for all agents."""

    def __init__(self, router: ModelRouter):
        self.router = router

    async def execute(self, brief: dict) -> AdapterResult:
        """Execute a task by sending it as a user message to the LLM."""
        task = brief.get("task", "")
        system_prompt = brief.get("system_prompt", "")
        model = brief.get("model")
        max_tokens = brief.get("max_tokens", 2000)
        temperature = brief.get("temperature", 0.7)
        task_type = brief.get("task_type", "creative_writing")

        messages = [{"role": "user", "content": task}]

        # Add context as part of the message if provided
        context = brief.get("context")
        if context:
            import json
            context_str = json.dumps(context, indent=2) if isinstance(context, dict) else str(context)
            messages = [{"role": "user", "content": f"Context:\n{context_str}\n\nTask:\n{task}"}]

        result: CompletionResult = await self.router.complete(
            messages=messages,
            task_type=task_type,
            model_override=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
        )

        return AdapterResult(
            content=result.content,
            model=result.model,
            cost_estimate=result.cost_estimate,
            metadata={
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
            },
        )

    async def probe(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            mcp=False,
            streaming=False,
            sub_agents=False,
            models=list(self.router.routing_table.keys()),
        )

    async def health(self) -> bool:
        return True

    async def close(self):
        await self.router.close()
