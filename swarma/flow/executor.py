"""Flow executor -- runs a parsed flow definition step by step.

Sequential steps run one at a time, passing output as context to the next.
Parallel steps run concurrently via asyncio.gather, and their combined
outputs become the context for the next step.
"""

import asyncio
import logging
from typing import Callable, Awaitable, Optional

from .parser import Flow, FlowStep

logger = logging.getLogger(__name__)


async def execute_flow(
    flow: Flow,
    run_agent: Callable[[str, Optional[dict]], Awaitable[dict]],
    initial_context: Optional[dict] = None,
) -> dict:
    """Execute a flow step by step.

    Args:
        flow: Parsed Flow object (list of sequential/parallel steps).
        run_agent: async function(agent_id, context) -> result dict.
            The caller provides this -- it handles agent lookup, error handling, etc.
        initial_context: Optional starting context for the first step.

    Returns:
        Dict with:
            - results: {agent_id: result_dict} for all agents
            - flow_output: the final step's output (passed downstream)
            - errors: {agent_id: error_str} for any failures
    """
    all_results = {}
    all_errors = {}
    context = initial_context or {}

    for i, step in enumerate(flow.steps):
        step_name = repr(step)
        logger.info("flow step %d/%d: %s", i + 1, len(flow), step_name)

        if step.is_parallel:
            # Run all agents in this step concurrently
            step_results = await _run_parallel(step, run_agent, context)
        else:
            # Run single agent
            step_results = await _run_single(step.agents[0], run_agent, context)

        # Collect results and errors
        for agent_id, result in step_results.items():
            if result.get("error"):
                all_errors[agent_id] = result["error"]
                logger.warning("flow step %d: %s failed: %s", i + 1, agent_id, result["error"])
            else:
                all_results[agent_id] = result

        # Build context for next step from this step's output
        # Each step's output becomes the next step's input
        if step.is_parallel:
            # Merge all parallel outputs into one context
            context = {
                "previous_step": step_name,
                "outputs": {
                    agent_id: result.get("content", "")
                    for agent_id, result in step_results.items()
                    if not result.get("error")
                },
            }
        else:
            agent_id = step.agents[0]
            result = step_results.get(agent_id, {})
            context = {
                "previous_step": agent_id,
                "output": result.get("content", ""),
                **{k: v for k, v in result.items() if k != "content"},
            }

    return {
        "results": all_results,
        "flow_output": context,
        "errors": all_errors,
    }


async def _run_single(
    agent_id: str,
    run_agent: Callable,
    context: dict,
) -> dict[str, dict]:
    """Run a single agent and return {agent_id: result}."""
    try:
        result = await run_agent(agent_id, context)
        return {agent_id: result}
    except Exception as e:
        logger.error("agent %s failed: %s", agent_id, e)
        return {agent_id: {"error": str(e)}}


async def _run_parallel(
    step: FlowStep,
    run_agent: Callable,
    context: dict,
) -> dict[str, dict]:
    """Run multiple agents in parallel and return {agent_id: result} for each."""

    async def _safe_run(agent_id: str) -> tuple[str, dict]:
        try:
            result = await run_agent(agent_id, context)
            return agent_id, result
        except Exception as e:
            logger.error("agent %s failed: %s", agent_id, e)
            return agent_id, {"error": str(e)}

    tasks = [_safe_run(aid) for aid in step.agents]
    completed = await asyncio.gather(*tasks)

    return {agent_id: result for agent_id, result in completed}
