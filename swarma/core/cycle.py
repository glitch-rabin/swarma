"""Cycle runner -- the main execution loop for a team.

A cycle:
1. Parses the team's flow definition
2. Instantiates agents
3. Executes the flow (sequential + parallel steps)
4. Logs results, costs, artifacts
5. Returns a summary

This is the generic version of agent-army's orchestrator.run_daily_cycle().
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from .agent import Agent
from .config import AgentConfig, TeamConfig
from .heartbeat import Heartbeat
from .knowledge import KnowledgeStore
from .router import ModelRouter
from .state import StateDB
from ..flow.parser import parse_flow
from ..flow.executor import execute_flow
from ..adapters.registry import AdapterRegistry
from ..experts.catalog import ExpertCatalog
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class CycleRunner:
    """Runs a team's flow once (a single cycle)."""

    def __init__(
        self,
        team: TeamConfig,
        router: ModelRouter,
        state: StateDB,
        knowledge: Optional[KnowledgeStore] = None,
        heartbeat: Optional[Heartbeat] = None,
        agent_classes: Optional[dict[str, type]] = None,
        tool_registry: Optional[ToolRegistry] = None,
        adapter_registry: Optional[AdapterRegistry] = None,
        expert_catalog: Optional[ExpertCatalog] = None,
    ):
        self.team = team
        self.router = router
        self.state = state
        self.knowledge = knowledge
        self.heartbeat = heartbeat
        self.tool_registry = tool_registry
        self.adapter_registry = adapter_registry
        self.expert_catalog = expert_catalog
        self._agent_classes = agent_classes or {}
        self._agents: dict[str, Agent] = {}

        # Instantiate agents from team config
        for agent_id, agent_config in team.agents.items():
            agent_cls = self._agent_classes.get(agent_id, Agent)
            self._agents[agent_id] = agent_cls(
                config=agent_config,
                team=team,
                router=router,
                state=state,
                knowledge=knowledge,
                tool_registry=tool_registry,
                adapter_registry=adapter_registry,
                expert_catalog=expert_catalog,
            )

    async def run(self, context: Optional[dict] = None) -> dict:
        """Execute one cycle of the team's flow.

        Returns:
            Dict with results, costs, errors, and cycle metadata.
        """
        cycle_start = datetime.now()
        flow_str = self.team.flow

        if not flow_str:
            logger.warning("team %s has no flow defined, running all agents sequentially", self.team.id)
            flow_str = " -> ".join(self.team.agents.keys())

        flow = parse_flow(flow_str)
        logger.info("running cycle for team '%s': %s", self.team.id, flow)

        # Check that all agents in flow exist
        missing = [a for a in flow.all_agents if a not in self._agents]
        if missing:
            logger.warning("agents in flow but not configured: %s", missing)

        # Execute the flow
        result = await execute_flow(
            flow=flow,
            run_agent=self._run_agent,
            initial_context=context or {"cycle_start": cycle_start.isoformat()},
        )

        # Build cycle summary
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()

        summary = {
            "team_id": self.team.id,
            "flow": str(flow),
            "started_at": cycle_start.isoformat(),
            "completed_at": cycle_end.isoformat(),
            "duration_seconds": duration,
            "agents_run": list(result["results"].keys()),
            "errors": result["errors"],
            "results": {
                agent_id: {
                    "content": r.get("content", "")[:200],
                    "model": r.get("model", ""),
                    "cost": r.get("cost", 0),
                }
                for agent_id, r in result["results"].items()
            },
            "total_cost": sum(
                r.get("cost", 0) for r in result["results"].values()
            ),
        }

        # Save cycle log as artifact
        if self.knowledge:
            self.knowledge.save(
                collection="cycle-logs",
                content=self._format_cycle_log(summary),
                agent_id="cycle-runner",
                team_id=self.team.id,
                title=f"Cycle {cycle_start.strftime('%Y-%m-%d %H:%M')}",
            )

        logger.info(
            "cycle complete: team=%s agents=%d errors=%d cost=$%.4f duration=%.1fs",
            self.team.id, len(result["results"]), len(result["errors"]),
            summary["total_cost"], duration,
        )

        return summary

    async def _run_agent(self, agent_id: str, context: Optional[dict] = None) -> dict:
        """Run a single agent with error handling and logging."""
        agent = self._agents.get(agent_id)
        if not agent:
            return {"error": f"Agent '{agent_id}' not found in team '{self.team.id}'"}

        run_id = agent.log_run("cycle", context)
        logger.info("running agent: %s/%s", self.team.id, agent_id)

        try:
            result = await agent.run(context)
            agent.complete_run(run_id, result)

            # Save output as artifact
            content = result.get("content", "")
            if content and self.knowledge:
                agent.save_artifact(
                    collection="agent-outputs",
                    content=content,
                    title=f"{agent_id} cycle output",
                )

            # Close the experiment loop: evaluate -> log -> verdict -> strategy update
            if content and agent.config.metric.name:
                try:
                    eval_result = await agent.evaluate_output(result)
                    if eval_result:
                        result["evaluation"] = eval_result
                        logger.info("experiment loop: %s/%s -> %s",
                                    self.team.id, agent_id, eval_result)
                except Exception as e:
                    logger.warning("experiment evaluation failed for %s: %s", agent_id, e)

            return result

        except Exception as e:
            error_msg = str(e)
            agent.complete_run(run_id, error=error_msg)
            logger.error("agent %s/%s failed: %s", self.team.id, agent_id, error_msg)
            return {"error": error_msg}

    def _format_cycle_log(self, summary: dict) -> str:
        """Format cycle summary as markdown."""
        lines = [
            f"# Cycle: {summary['team_id']}",
            f"**Started:** {summary['started_at']}",
            f"**Duration:** {summary['duration_seconds']:.1f}s",
            f"**Total cost:** ${summary['total_cost']:.4f}",
            "",
            "## Agents Run",
        ]
        for agent_id in summary["agents_run"]:
            r = summary["results"].get(agent_id, {})
            lines.append(f"- **{agent_id}** ({r.get('model', 'unknown')}): ${r.get('cost', 0):.4f}")
            preview = r.get("content", "")[:100]
            if preview:
                lines.append(f"  > {preview}...")

        if summary["errors"]:
            lines.append("\n## Errors")
            for agent_id, error in summary["errors"].items():
                lines.append(f"- **{agent_id}**: {error}")

        return "\n".join(lines)


class Engine:
    """Top-level engine that manages multiple teams and scheduling.

    This is what `swarma run` starts.
    """

    def __init__(
        self,
        teams: dict[str, TeamConfig],
        router: ModelRouter,
        state: StateDB,
        knowledge: Optional[KnowledgeStore] = None,
        tool_registry: Optional[ToolRegistry] = None,
        adapter_registry: Optional[AdapterRegistry] = None,
        expert_catalog: Optional[ExpertCatalog] = None,
    ):
        self.teams = teams
        self.router = router
        self.state = state
        self.knowledge = knowledge
        self.tool_registry = tool_registry
        self.adapter_registry = adapter_registry
        self.expert_catalog = expert_catalog
        self._runners: dict[str, CycleRunner] = {}

        for team_id, team in teams.items():
            self._runners[team_id] = CycleRunner(
                team=team,
                router=router,
                state=state,
                knowledge=knowledge,
                tool_registry=tool_registry,
                adapter_registry=adapter_registry,
                expert_catalog=expert_catalog,
            )

    async def run_cycle(self, team_id: str, context: Optional[dict] = None) -> dict:
        """Run a single cycle for a team."""
        runner = self._runners.get(team_id)
        if not runner:
            raise ValueError(f"Unknown team: {team_id}. Available: {list(self._runners)}")
        return await runner.run(context)

    async def run_all(self, context: Optional[dict] = None) -> dict:
        """Run cycles for all teams (sequentially)."""
        results = {}
        for team_id in self._runners:
            results[team_id] = await self.run_cycle(team_id, context)
        return results

    async def close(self):
        await self.router.close()
        if self.adapter_registry:
            await self.adapter_registry.close_all()
        self.state.close()
