"""Team generator -- describe what you want, get a working team.

Takes business context + intent ("what do you want to improve?") and
generates a full team config: team.yaml, agents/*.yaml, program.md,
and a first experiment hypothesis.

This is the bridge between "swarma init" and "my own team."
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# Models available for assignment (cheapest that fits the job)
AVAILABLE_MODELS = {
    "routing": {
        "model_id": "mistralai/mistral-nemo",
        "cost": "$0.02/M tokens",
        "good_for": "routing, scoring, classification, lightweight analysis",
    },
    "creative_writing": {
        "model_id": "qwen/qwen3.5-plus-02-15",
        "cost": "$0.26/M tokens",
        "good_for": "content writing, copywriting, synthesis, summarization",
    },
    "research": {
        "model_id": "perplexity/sonar-pro",
        "cost": "$0.30/M tokens",
        "good_for": "web research, news scanning, fact gathering",
    },
    "analysis": {
        "model_id": "qwen/qwen-2.5-72b-instruct",
        "cost": "$0.10/M tokens",
        "good_for": "research summarization, data analysis, pattern detection",
    },
    "reasoning": {
        "model_id": "deepseek/deepseek-r1",
        "cost": "$0.55/M tokens",
        "good_for": "strategic reasoning, complex decisions, experiment design",
    },
    "hard_decisions": {
        "model_id": "anthropic/claude-sonnet-4-6",
        "cost": "$3.00/M tokens",
        "good_for": "nuanced judgment, quality gates, final review",
    },
}

# Reference squads (names + what they do) for the LLM to pattern-match
REFERENCE_SQUADS = """
- hook-lab: tests message angles (contrarian vs consensus, story vs data, loss vs gain framing). 3 agents: researcher -> copywriter -> judge.
- channel-mix: optimizes multi-channel content strategy (email, linkedin, twitter). 4 agents: researcher -> strategist -> [content-writer, analytics].
- cold-outbound: personalizes outreach at scale. 3 agents: prospector -> writer -> scorer.
- competitive-intel: monitors competitors and market shifts. 3 agents: scanner -> analyst -> briefer.
- landing-lab: optimizes landing pages through A/B experiments. 4 agents: researcher -> copywriter -> designer -> analyst.
- pricing-lab: tests pricing strategies and packaging. 3 agents: researcher -> modeler -> analyst.
- referral-engine: designs and tests viral growth loops. 3 agents: researcher -> designer -> tracker.
- retention-squad: reduces churn through proactive engagement. 4 agents: monitor -> analyst -> [writer, alerter].
- seo-engine: builds organic search presence. 4 agents: keyword-researcher -> content-planner -> writer -> tracker.
- activation-flow: optimizes user onboarding and activation. 3 agents: researcher -> designer -> analyst.
"""

GENERATION_PROMPT = """You are the swarma team generator. Given a user's business context and what they want to improve, generate a complete team configuration.

## How swarma works
- Teams are pipelines of AI agents that run experiments
- Each agent has ONE metric it optimizes
- The loop: strategy.md -> execute -> measure -> verdict (keep/discard) -> update strategy
- Agents learn from their own results over time
- Flow DSL: "a -> b -> c" (sequential), "a -> [b, c] -> d" (parallel middle)

## Available models (assign cheapest that fits)
{models}

## Reference squad patterns
{squads}

## Rules
1. Pick 2-5 agents. More isn't better.
2. Each agent gets a specific role name (slug format: lowercase-with-dashes)
3. Flow must be a valid DSL string connecting all agents
4. First agent in flow should either be a researcher or triggered by schedule
5. Last agent (or branch) should measure/analyze results
6. Each agent's instructions should be specific and actionable (3-5 sentences)
7. program.md should define 2-3 concrete experiment patterns with variables to test
8. The first experiment should be a testable hypothesis with clear metric
9. Budget: assign based on model costs. $10-50/month is typical.
10. Use practitioner language, not corporate jargon

## Output format
Return ONLY a JSON object (no markdown, no explanation):

{{
  "name": "team-slug",
  "display_name": "Human-Readable Name",
  "goal": "One-sentence goal",
  "flow": "agent-a -> agent-b -> agent-c",
  "schedule": "cron expression or null",
  "budget_monthly": 30.0,
  "agents": {{
    "agent-slug": {{
      "name": "Human Name",
      "model_id": "provider/model-name",
      "max_tokens": 4096,
      "temperature": 0.7,
      "instructions": "Specific instructions for this agent.",
      "metric": "metric_name",
      "triggered_by": "other-agent-slug or null",
      "schedule": "cron or null"
    }}
  }},
  "program": "Full markdown content for program.md (experiment patterns, metrics, constraints)",
  "first_experiment": {{
    "hypothesis": "Testable hypothesis statement",
    "metric_name": "the_metric",
    "sample_size": 5
  }}
}}
"""

USER_PROMPT_TEMPLATE = """## Business context
{context}

## What I want to improve
{intent}

## Constraints
- Team name preference: {name}
- Monthly budget: ${budget}
- Schedule: {schedule}

Generate the team configuration."""


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try direct parse first
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Try extracting from markdown code block
    patterns = [
        r"```json\s*\n(.*?)\n\s*```",
        r"```\s*\n(.*?)\n\s*```",
        r"\{.*\}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(1) if match.lastindex else match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract valid JSON from LLM response:\n{text[:500]}")


def _validate_team_config(config: dict) -> list[str]:
    """Validate the generated config. Returns list of issues (empty = valid)."""
    issues = []

    if not config.get("name"):
        issues.append("Missing team name")
    if not config.get("goal"):
        issues.append("Missing team goal")
    if not config.get("flow"):
        issues.append("Missing flow definition")
    if not config.get("agents"):
        issues.append("Missing agents")

    agents = config.get("agents", {})
    if agents:
        # Check all agents in flow exist
        flow = config.get("flow", "")
        flow_agents = set(re.findall(r"[a-z][a-z0-9-]*", flow))
        defined_agents = set(agents.keys())

        # Remove flow keywords
        flow_agents -= {"->"}

        missing = flow_agents - defined_agents
        if missing:
            issues.append(f"Flow references undefined agents: {missing}")

        unused = defined_agents - flow_agents
        if unused:
            issues.append(f"Agents defined but not in flow: {unused}")

        for aid, agent in agents.items():
            if not agent.get("instructions"):
                issues.append(f"Agent '{aid}' has no instructions")
            if not agent.get("model_id"):
                issues.append(f"Agent '{aid}' has no model_id")

    if not config.get("first_experiment", {}).get("hypothesis"):
        issues.append("Missing first experiment hypothesis")

    return issues


def _write_team_files(config: dict, teams_dir: Path) -> Path:
    """Write the generated config to disk as team.yaml + agents/*.yaml + program.md."""
    team_name = config["name"]
    team_dir = teams_dir / team_name

    if team_dir.exists():
        raise FileExistsError(f"Team '{team_name}' already exists at {team_dir}")

    team_dir.mkdir(parents=True, exist_ok=True)
    agents_dir = team_dir / "agents"
    agents_dir.mkdir(exist_ok=True)

    # Write team.yaml (without embedded agents -- they go in agents/)
    team_yaml = {
        "name": config.get("display_name", team_name),
        "goal": config["goal"],
        "flow": config["flow"],
    }
    if config.get("schedule"):
        team_yaml["schedule"] = config["schedule"]
    if config.get("budget_monthly"):
        team_yaml["budget_monthly"] = config["budget_monthly"]

    with open(team_dir / "team.yaml", "w") as f:
        yaml.dump(team_yaml, f, default_flow_style=False, sort_keys=False)

    # Write individual agent configs
    agents = config.get("agents", {})
    for agent_id, agent_data in agents.items():
        agent_yaml = {
            "id": agent_id,
            "name": agent_data.get("name", agent_id),
            "model": {
                "model_id": agent_data["model_id"],
                "max_tokens": agent_data.get("max_tokens", 4096),
                "temperature": agent_data.get("temperature", 0.7),
            },
            "runtime": "llm",
            "instructions": agent_data["instructions"],
            "metric": agent_data.get("metric", "quality"),
        }
        if agent_data.get("triggered_by"):
            agent_yaml["triggered_by"] = agent_data["triggered_by"]
        if agent_data.get("schedule"):
            agent_yaml["schedule"] = agent_data["schedule"]

        with open(agents_dir / f"{agent_id}.yaml", "w") as f:
            yaml.dump(agent_yaml, f, default_flow_style=False, sort_keys=False)

    # Write program.md
    program_content = config.get("program", f"# {config.get('display_name', team_name)}\n\nNo program defined yet.\n")
    (team_dir / "program.md").write_text(program_content)

    return team_dir


async def generate_team(
    intent: str,
    router,
    instance_path: Path,
    context: str = "",
    name: str = "",
    budget: float = 30.0,
    schedule: str = "",
) -> dict:
    """Generate a full team from business context + intent.

    Args:
        intent: What the user wants to improve (the key question).
        router: ModelRouter instance for making LLM calls.
        instance_path: Path to the swarma instance directory.
        context: Business description, who you are, what you do.
        name: Optional team name (auto-generated if empty).
        budget: Monthly budget cap in USD.
        schedule: Cron schedule string (empty = manual trigger).

    Returns:
        dict with keys: team_dir, config, first_experiment, issues
    """
    # Build the system prompt
    models_text = "\n".join(
        f"- {role}: `{info['model_id']}` ({info['cost']}) -- {info['good_for']}"
        for role, info in AVAILABLE_MODELS.items()
    )
    system_prompt = GENERATION_PROMPT.format(
        models=models_text,
        squads=REFERENCE_SQUADS,
    )

    # Build the user prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(
        context=context or "(not provided -- infer from intent)",
        intent=intent,
        name=name or "(auto-generate a descriptive slug)",
        budget=budget,
        schedule=schedule or "manual (user triggers cycles)",
    )

    # Call the LLM (use strategic_reasoning task type)
    logger.info("generating team config for intent: %s", intent[:80])
    result = await router.complete(
        messages=[{"role": "user", "content": user_prompt}],
        task_type="strategic_reasoning",
        system_prompt=system_prompt,
        max_tokens=4000,
    )

    # Parse the response
    config = _extract_json(result.content)

    # Validate
    issues = _validate_team_config(config)
    if issues:
        logger.warning("generated config has issues: %s", issues)

    # If name was provided, override
    if name:
        config["name"] = name

    # Write to disk
    teams_dir = instance_path / "teams"
    teams_dir.mkdir(parents=True, exist_ok=True)
    team_dir = _write_team_files(config, teams_dir)

    return {
        "team_dir": str(team_dir),
        "team_name": config["name"],
        "display_name": config.get("display_name", config["name"]),
        "goal": config["goal"],
        "flow": config["flow"],
        "agents": list(config.get("agents", {}).keys()),
        "first_experiment": config.get("first_experiment"),
        "budget_monthly": config.get("budget_monthly", budget),
        "issues": issues,
        "config": config,
    }
