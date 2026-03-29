"""Base agent class. All agents inherit from this.

An agent has:
- A config (model, tools, metric, schedule, runtime)
- A system prompt (assembled from team + agent config + lenses + strategy + knowledge)
- Access to the router for LLM calls
- Access to state DB for tracking
- An experiment engine for its own learning loop
- Optional tool registry for function calling
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import AgentConfig, TeamConfig
from .experiment import Experiment as ExperimentObj, ExperimentEngine
from .router import CompletionResult, ModelRouter
from .state import StateDB

logger = logging.getLogger(__name__)


class Agent:
    """Base agent. Override `run()` for custom behavior.

    Default `run()` sends the context as a user message to the LLM
    and returns the response. This is sufficient for most agents --
    only override for agents that need multi-step logic.
    """

    MAX_TOOL_ROUNDS = 5  # prevent infinite tool call loops

    def __init__(
        self,
        config: AgentConfig,
        team: TeamConfig,
        router: ModelRouter,
        state: StateDB,
        knowledge=None,
        tool_registry=None,
        adapter_registry=None,
        expert_catalog=None,
    ):
        self.config = config
        self.team = team
        self.router = router
        self.state = state
        self.knowledge = knowledge
        self.tool_registry = tool_registry
        self.adapter_registry = adapter_registry
        self.expert_catalog = expert_catalog
        self.experiment_engine = ExperimentEngine(team.path, config.id)

    @property
    def agent_id(self) -> str:
        return self.config.id

    @property
    def team_id(self) -> str:
        return self.team.id

    def build_system_prompt(self) -> str:
        """Assemble the full system prompt from components."""
        parts = []

        # 1. Role and identity
        parts.append(f"# {self.config.name}")
        parts.append(f"You are the {self.config.name} for team '{self.team.id}'.")

        # 2. Team goal
        if self.team.goal:
            parts.append(f"## Team Goal\n{self.team.goal}")

        # 3. Team program (detailed context)
        if self.team.program_md:
            parts.append("## Team Program")
            parts.append(self.team.program_md)

        # 4. Brand kit (for agents that produce content)
        if self.team.brand_kit_md:
            parts.append("## Brand Kit")
            parts.append(self.team.brand_kit_md)

        # 5. Agent-specific instructions (inline or from file)
        if self.config.instructions:
            parts.append("## Your Instructions")
            parts.append(self.config.instructions)
        elif self.config.system_prompt_file:
            prompt_path = Path(self.team.path) / self.config.system_prompt_file
            if prompt_path.exists():
                parts.append("## Agent Instructions")
                parts.append(prompt_path.read_text())

        # 6. Reasoning lenses (expert frameworks)
        lenses = list(self.config.lenses) if self.config.lenses else []

        # Resolve expert_lenses IDs from catalog
        if self.config.expert_lenses and self.expert_catalog:
            from ..experts.composer import compose_lenses
            experts = self.expert_catalog.get_multiple(self.config.expert_lenses)
            lenses.extend(compose_lenses(experts))

        if lenses:
            parts.append("## Reasoning Lenses")
            for lens in lenses:
                parts.append(f"### {lens.get('expert', 'Unknown')}")
                parts.append(lens.get('instruction', ''))

        # 7. Current strategy (the editable thing)
        strategy = self.experiment_engine.get_strategy()
        parts.append("## Current Strategy")
        parts.append(strategy)

        # 8. Recent results
        results = self.experiment_engine.get_results(limit=10)
        if results:
            parts.append("## Recent Results (last 10)")
            parts.append("date\toutput_id\tmetric\tstatus\tdescription")
            for r in results:
                parts.append(f"{r.date}\t{r.output_id}\t{r.metric_value:.4f}\t{r.status}\t{r.description}")

        # 9. Knowledge context
        if self.knowledge:
            try:
                knowledge_ctx = self.knowledge.get_agent_context(self.agent_id, self.team_id)
                if knowledge_ctx and knowledge_ctx != "No prior context available.":
                    parts.append("## Knowledge Context")
                    parts.append(knowledge_ctx)
            except Exception as e:
                logger.warning("failed to load knowledge context for %s: %s", self.agent_id, e)

        return "\n\n".join(parts)

    def _get_tool_definitions(self) -> Optional[list[dict]]:
        """Get OpenAI-compatible tool definitions for this agent's assigned tools."""
        if not self.tool_registry or not self.config.tools:
            return None

        team_tools = self.team.tools or []
        defs = self.tool_registry.get_definitions(
            self.tool_registry.get_agent_tools(
                self.config.tools, team_tools
            ).keys()
        )
        return defs if defs else None

    async def _execute_tool_call(self, name: str, arguments: dict) -> str:
        """Execute a tool call and return the result as a string."""
        if not self.tool_registry:
            return json.dumps({"error": f"No tool registry available"})

        result = await self.tool_registry.execute(name, **arguments)
        if result.success:
            return result.content
        return json.dumps({"error": result.error or "Tool execution failed"})

    async def complete(
        self,
        messages: list[dict],
        task_type: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> CompletionResult:
        """Make an LLM call using this agent's configured model.

        If the agent has tools assigned, injects tool definitions into the call
        and handles the tool call loop: LLM requests tool -> execute -> return
        result -> LLM continues, up to MAX_TOOL_ROUNDS.
        """
        tool_defs = self._get_tool_definitions()
        sys_prompt = system_prompt or self.build_system_prompt()
        working_messages = list(messages)

        total_input = 0
        total_output = 0
        total_cost = 0.0
        final_result = None

        for round_num in range(self.MAX_TOOL_ROUNDS + 1):
            result = await self.router.complete(
                messages=working_messages,
                task_type=task_type or "creative_writing",
                model_override=self.config.model.model_id,
                max_tokens=self.config.model.max_tokens,
                temperature=self.config.model.temperature,
                system_prompt=sys_prompt,
                tools=tool_defs,
            )

            total_input += result.input_tokens
            total_output += result.output_tokens
            total_cost += result.cost_estimate
            final_result = result

            # Check if the LLM wants to call tools
            raw = result.raw_response
            choice = raw.get("choices", [{}])[0]
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls")

            if not tool_calls:
                # No tool calls -- we're done
                break

            # Append the assistant message with tool_calls
            working_messages.append(message)

            # Execute each tool call and append results
            for tc in tool_calls:
                fn = tc.get("function", {})
                tool_name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}

                logger.info("tool call: %s/%s -> %s(%s)",
                            self.team_id, self.agent_id, tool_name,
                            list(args.keys()))

                tool_result = await self._execute_tool_call(tool_name, args)

                working_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": tool_result,
                })

            if round_num == self.MAX_TOOL_ROUNDS:
                logger.warning("agent %s hit max tool rounds (%d)",
                               self.agent_id, self.MAX_TOOL_ROUNDS)

        # Log aggregated cost
        self.state.log_cost(
            team_id=self.team_id,
            agent_id=self.agent_id,
            service="openrouter",
            model=final_result.model,
            input_tokens=total_input,
            output_tokens=total_output,
            cost=total_cost,
        )

        # Return the final result with aggregated totals
        final_result.input_tokens = total_input
        final_result.output_tokens = total_output
        final_result.cost_estimate = total_cost
        return final_result

    async def run(self, context: Optional[dict] = None) -> dict:
        """Execute this agent's primary task.

        For LLM runtime: sends context as user message via router.
        For other runtimes (hermes, http, process): dispatches via adapter.
        Override for multi-step agents.
        """
        # Non-LLM runtimes dispatch via adapter
        if self.config.runtime != "llm" and self.adapter_registry:
            return await self._run_via_adapter(context)

        # Default LLM path
        ctx = context or {}
        task = ctx.get("task", ctx.get("topic", "Execute your primary task."))

        if isinstance(task, dict):
            task = json.dumps(task, indent=2)

        result = await self.complete(
            messages=[{"role": "user", "content": str(task)}],
        )

        return {
            "agent_id": self.agent_id,
            "content": result.content,
            "model": result.model,
            "cost": result.cost_estimate,
        }

    async def _run_via_adapter(self, context: Optional[dict] = None) -> dict:
        """Execute via a runtime adapter (hermes, http, process)."""
        ctx = context or {}
        task = ctx.get("task", ctx.get("topic", "Execute your primary task."))

        if isinstance(task, dict):
            task = json.dumps(task, indent=2)

        adapter = self.adapter_registry.get_adapter(
            runtime=self.config.runtime,
            runtime_config=getattr(self.config, "runtime_config", None),
        )

        brief = {
            "task": str(task),
            "context": ctx,
            "system_prompt": self.build_system_prompt(),
            "tools": self.config.tools,
            "model": self.config.model.model_id,
            "max_tokens": self.config.model.max_tokens,
            "temperature": self.config.model.temperature,
        }

        result = await adapter.execute(brief)

        # Log cost
        self.state.log_cost(
            team_id=self.team_id,
            agent_id=self.agent_id,
            service=self.config.runtime,
            model=result.model,
            input_tokens=result.metadata.get("input_tokens", 0),
            output_tokens=result.metadata.get("output_tokens", 0),
            cost=result.cost_estimate,
        )

        return {
            "agent_id": self.agent_id,
            "content": result.content,
            "model": result.model,
            "cost": result.cost_estimate,
            "error": result.error,
        }

    async def evaluate_output(self, output: dict) -> Optional[dict]:
        """Self-evaluate output against the agent's metric. Closes the experiment loop.

        After each run:
        1. Scores output using a cheap LLM call
        2. Logs score to results.tsv
        3. If active experiment has enough samples, issues verdict
        4. Updates strategy.md on keep/discard
        5. If no active experiment, creates one (baseline)
        """
        content = output.get("content", "")
        if not content or not self.config.metric.name:
            return None

        # Score the output with a cheap model -- rubric forces variance
        strategy_preview = self.experiment_engine.get_strategy()[:500]
        recent = self.experiment_engine.get_results(limit=5)
        recent_scores = [r.metric_value for r in recent] if recent else []
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0

        eval_prompt = (
            f"You are a strict quality evaluator. Score this output for: {self.config.metric.name}\n\n"
            f"SCORING RUBRIC (be harsh, use precise decimals like 6.3 or 7.8):\n"
            f"- 9-10: Exceptional. Publishable as-is. Unique data, specific numbers, perfect structure.\n"
            f"- 7-8: Good but flawed. Clear value, missing some specificity or structural issues.\n"
            f"- 5-6: Average. Generic insights, weak hook, or vague claims without data.\n"
            f"- 3-4: Below average. No data, sounds like marketing copy, no clear takeaway.\n"
            f"- 1-2: Poor. Completely vague, no value.\n\n"
            f"Output to evaluate:\n{content[:2000]}\n\n"
            f"Current strategy:\n{strategy_preview}\n\n"
        )
        if recent_scores:
            eval_prompt += (
                f"Previous scores: {[f'{s:.1f}' for s in recent_scores[-3:]]}, avg={recent_avg:.1f}\n"
                f"Is THIS output better or worse than previous ones? Be discriminating.\n\n"
            )
        eval_prompt += (
            f"Respond ONLY with a JSON object (use precise decimals, NOT round numbers):\n"
            f'{{"score": <float with decimal like 7.3>, "reasoning": "<1 specific sentence>", '
            f'"strategy_suggestion": "<1 specific actionable change to try next>"}}'
        )

        try:
            result = await self.router.complete(
                messages=[{"role": "user", "content": eval_prompt}],
                task_type="routing",  # cheapest model
                max_tokens=200,
                temperature=0.2,
            )
        except Exception as e:
            logger.warning("evaluation LLM call failed for %s: %s", self.agent_id, e)
            return None

        # Parse score from response
        try:
            json_match = re.search(r'\{.*\}', result.content, re.DOTALL)
            if json_match:
                eval_data = json.loads(json_match.group())
                score = float(eval_data.get("score", 5.0))
            else:
                score = 5.0
                eval_data = {"score": score, "reasoning": "parse error", "strategy_suggestion": ""}
        except (json.JSONDecodeError, ValueError):
            score = 5.0
            eval_data = {"score": score, "reasoning": "parse error", "strategy_suggestion": ""}

        # Log result to results.tsv
        output_id = output.get("output_id", f"cycle-{datetime.now().strftime('%Y%m%d%H%M')}")
        self.experiment_engine.log_result(
            output_id=output_id,
            metric_value=score,
            status="measured",
            description=eval_data.get("reasoning", ""),
        )

        logger.info("evaluated %s/%s: score=%.1f reason=%s",
                     self.team_id, self.agent_id, score,
                     eval_data.get("reasoning", "")[:60])

        # Check for active experiment
        active_exps = self.state.get_active_experiments(self.team_id, self.agent_id)

        if active_exps:
            exp = active_exps[0]
            new_count = (exp["sample_size_current"] or 0) + 1

            # Update sample count
            self.state.conn.execute(
                "UPDATE experiments SET sample_size_current = ? WHERE id = ?",
                (new_count, exp["id"])
            )
            self.state.conn.commit()

            # Check if enough samples for verdict
            all_results = self.experiment_engine.get_results(limit=100)
            recent_results = all_results[-new_count:]

            exp_obj = ExperimentObj(
                id=exp["id"], agent_id=exp["agent_id"], team_id=exp["team_id"],
                hypothesis=exp["hypothesis"], metric_name=exp["metric_name"],
                baseline=exp["baseline"], target=exp["target"],
                sample_size_needed=exp["sample_size_needed"],
                sample_size_current=new_count, result=None, verdict="running",
            )

            verdict = self.experiment_engine.evaluate_experiment(exp_obj, recent_results)

            if verdict in ("keep", "discard", "inconclusive"):
                avg = sum(r.metric_value for r in recent_results) / len(recent_results)
                strategy_change = eval_data.get("strategy_suggestion", "")

                self.state.close_experiment(
                    exp["id"], result=avg, verdict=verdict,
                    strategy_change=strategy_change,
                )
                self.experiment_engine.save_experiment_log(exp_obj, verdict, recent_results)

                # Ratchet strategy based on verdict
                if verdict == "keep":
                    current = self.experiment_engine.get_strategy()
                    updated = (
                        current + f"\n\n## Validated (Exp {exp['id']})\n"
                        f"{exp['hypothesis']}\n"
                        f"> {strategy_change}"
                    )
                    self.experiment_engine.update_strategy(updated)
                    logger.info("KEEP: experiment %d for %s -- strategy updated", exp["id"], self.agent_id)
                elif verdict == "inconclusive":
                    # No clear signal -- try a different approach
                    current = self.experiment_engine.get_strategy()
                    updated = (
                        current + f"\n\n## Inconclusive (Exp {exp['id']})\n"
                        f"Tried: {exp['hypothesis']} -- no significant change (avg={avg:.1f} vs baseline={exp['baseline']})\n"
                        f"> Next: {strategy_change}"
                    )
                    self.experiment_engine.update_strategy(updated)
                    logger.info("INCONCLUSIVE: experiment %d for %s -- strategy updated with learning", exp["id"], self.agent_id)
                else:
                    logger.info("DISCARD: experiment %d for %s -- reverting", exp["id"], self.agent_id)

                # Save evaluation to knowledge store
                if self.knowledge:
                    self.save_artifact(
                        collection="experiment-results",
                        content=(
                            f"# Experiment {exp['id']} Verdict: {verdict.upper()}\n\n"
                            f"**Agent:** {self.agent_id}\n"
                            f"**Hypothesis:** {exp['hypothesis']}\n"
                            f"**Baseline:** {exp['baseline']}\n"
                            f"**Result:** {avg:.2f}\n"
                            f"**Samples:** {new_count}\n"
                            f"**Strategy change:** {strategy_change}\n"
                        ),
                        title=f"Experiment {exp['id']} {verdict}",
                    )

                    # Cross-team learning: save validated patterns to playbook
                    # so ALL teams can search and benefit from this experiment
                    if verdict == "keep":
                        improvement = ((avg - (exp['baseline'] or 1)) / max(exp['baseline'] or 1, 0.01)) * 100
                        self.knowledge.save(
                            collection="playbook",
                            content=(
                                f"# [KEEP] {exp['hypothesis']}\n\n"
                                f"**Source:** {self.team_id}/{self.agent_id} (Experiment {exp['id']})\n"
                                f"**Metric:** {exp['metric_name']}\n"
                                f"**Baseline:** {exp['baseline']:.1f} → **Result:** {avg:.1f} "
                                f"({improvement:+.0f}%)\n"
                                f"**Samples:** {new_count}\n"
                                f"**Confidence:** {'high' if new_count >= 5 else 'medium'}\n\n"
                                f"## Pattern\n{strategy_change}\n"
                            ),
                            agent_id=self.agent_id,
                            team_id=self.team_id,
                            title=f"playbook-{exp['metric_name']}-exp{exp['id']}",
                            metadata={"verdict": "keep", "improvement_pct": round(improvement, 1)},
                        )
                        logger.info("playbook: saved validated pattern from exp %d to cross-team knowledge", exp["id"])
                    elif verdict == "discard":
                        self.knowledge.save(
                            collection="playbook",
                            content=(
                                f"# [DISCARD] {exp['hypothesis']}\n\n"
                                f"**Source:** {self.team_id}/{self.agent_id} (Experiment {exp['id']})\n"
                                f"**Metric:** {exp['metric_name']}\n"
                                f"**Baseline:** {exp['baseline']:.1f} → **Result:** {avg:.1f}\n"
                                f"**Samples:** {new_count}\n\n"
                                f"## Anti-pattern\nThis approach underperformed. Avoid: {exp['hypothesis']}\n"
                            ),
                            agent_id=self.agent_id,
                            team_id=self.team_id,
                            title=f"playbook-antipattern-exp{exp['id']}",
                            metadata={"verdict": "discard"},
                        )
                        logger.info("playbook: saved anti-pattern from exp %d to cross-team knowledge", exp["id"])

                return {"verdict": verdict, "score": avg, "experiment_id": exp["id"]}

            return {"score": score, "samples": new_count, "needed": exp["sample_size_needed"]}

        elif self.config.experiment_config.auto_propose:
            # No active experiment -- create one using this run as baseline
            suggestion = eval_data.get("strategy_suggestion", "baseline measurement")
            exp_id = self.state.create_experiment(
                team_id=self.team_id,
                agent_id=self.agent_id,
                hypothesis=suggestion,
                metric_name=self.config.metric.name,
                baseline=score,
                sample_size=self.config.experiment_config.min_sample_size,
            )
            self.state.conn.execute(
                "UPDATE experiments SET sample_size_current = 1 WHERE id = ?", (exp_id,)
            )
            self.state.conn.commit()
            logger.info("new experiment %d for %s: baseline=%.1f hypothesis=%s",
                         exp_id, self.agent_id, score, suggestion[:60])
            return {"new_experiment": exp_id, "baseline_score": score}

        return {"score": score}

    def save_artifact(
        self,
        collection: str,
        content: str,
        title: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[str]:
        """Save an artifact to the knowledge store."""
        if not self.knowledge:
            return None

        return self.knowledge.save(
            collection=collection,
            content=content,
            agent_id=self.agent_id,
            team_id=self.team_id,
            title=title,
            metadata=metadata,
        )

    def log_run(self, run_type: str, input_data: Optional[dict] = None) -> int:
        return self.state.start_run(self.team_id, self.agent_id, run_type, input_data)

    def complete_run(self, run_id: int, output: Optional[dict] = None,
                     error: Optional[str] = None):
        self.state.complete_run(run_id, output, error)
