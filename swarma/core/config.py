"""Config loader for swarma instances, teams, and agents.

Supports YAML (primary) and JSON configs. Loads from instance directory
structure (~/.swarma/instances/{name}/).
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ModelConfig:
    provider: str = "openrouter"
    model_id: str = "qwen/qwen3.5-plus-02-15"
    fallback: Optional[str] = None
    max_tokens: int = 2000
    temperature: float = 0.7


@dataclass
class ExperimentConfig:
    editable_file: str = "strategy.md"
    results_file: str = "results.tsv"
    min_sample_size: int = 5
    auto_propose: bool = True


@dataclass
class MetricConfig:
    name: str = ""
    target: Optional[float] = None
    measurement_window_hours: int = 24


@dataclass
class AgentConfig:
    id: str = ""
    name: str = ""
    team: str = ""
    model: ModelConfig = field(default_factory=ModelConfig)
    instructions: str = ""
    system_prompt_file: Optional[str] = None
    runtime: str = "llm"  # llm | hermes | http | process
    runtime_config: dict = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    metric: MetricConfig = field(default_factory=MetricConfig)
    schedule: Optional[str] = None
    triggered_by: Optional[str] = None
    experiment_config: ExperimentConfig = field(default_factory=ExperimentConfig)
    lenses: list[dict] = field(default_factory=list)
    expert_lenses: list[int] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        """Load from a dict (parsed from YAML or JSON)."""
        model_data = data.get("model", {})
        if isinstance(model_data, str):
            model = ModelConfig(model_id=model_data)
        else:
            model = ModelConfig(
                provider=model_data.get("provider", "openrouter"),
                model_id=model_data.get("model_id", "qwen/qwen3.5-plus-02-15"),
                fallback=model_data.get("fallback"),
                max_tokens=model_data.get("max_tokens", 2000),
                temperature=model_data.get("temperature", 0.7),
            )

        metric_data = data.get("metric", {})
        if isinstance(metric_data, str):
            metric = MetricConfig(name=metric_data)
        else:
            metric = MetricConfig(
                name=metric_data.get("name", ""),
                target=metric_data.get("target"),
                measurement_window_hours=metric_data.get("measurement_window_hours", 24),
            )

        exp_data = data.get("experiment_config", data.get("experiment", {}))
        experiment = ExperimentConfig(
            editable_file=exp_data.get("editable_file", exp_data.get("editable", "strategy.md")),
            results_file=exp_data.get("results_file", exp_data.get("results", "results.tsv")),
            min_sample_size=exp_data.get("min_sample_size", exp_data.get("min_samples", 5)),
            auto_propose=exp_data.get("auto_propose", True),
        )

        return cls(
            id=data.get("id", data.get("name", "")),
            name=data.get("name", data.get("id", "")),
            team=data.get("team", ""),
            model=model,
            instructions=data.get("instructions", ""),
            system_prompt_file=data.get("system_prompt_file"),
            runtime=data.get("runtime", "llm"),
            runtime_config=data.get("runtime_config", {}),
            tools=data.get("tools", []),
            metric=metric,
            schedule=data.get("schedule"),
            triggered_by=data.get("triggered_by"),
            experiment_config=experiment,
            lenses=data.get("lenses", []),
            expert_lenses=data.get("expert_lenses", []),
        )

    @classmethod
    def from_file(cls, path: str) -> "AgentConfig":
        """Load from a YAML or JSON file."""
        p = Path(path)
        with open(p) as f:
            if p.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        return cls.from_dict(data)


@dataclass
class TeamConfig:
    id: str = ""
    name: str = ""
    path: str = ""
    goal: str = ""
    program_md: str = ""
    brand_kit_md: str = ""
    schedule: Optional[str] = None
    budget_monthly: Optional[float] = None
    flow: str = ""
    tools: list[str] = field(default_factory=list)
    agents: dict[str, AgentConfig] = field(default_factory=dict)

    @classmethod
    def from_directory(cls, team_dir: str) -> "TeamConfig":
        """Load team config from a directory.

        Supports two layouts:
          1. YAML-first: team.yaml + agents/*.yaml
          2. Legacy: program.md + brand-kit.md + agents/*.json
        """
        team_path = Path(team_dir)
        team_id = team_path.name

        # Try YAML config first
        team_yaml = team_path / "team.yaml"
        team_yml = team_path / "team.yml"

        goal = ""
        schedule = None
        budget = None
        flow = ""
        tools = []
        name = team_id

        if team_yaml.exists() or team_yml.exists():
            yaml_path = team_yaml if team_yaml.exists() else team_yml
            with open(yaml_path) as f:
                data = yaml.safe_load(f) or {}
            goal = data.get("goal", "")
            schedule = data.get("schedule")
            budget = data.get("budget_monthly")
            flow = data.get("flow", "")
            tools = data.get("tools", [])
            name = data.get("name", team_id)

        # Load program.md (team context / instructions)
        program_path = team_path / "program.md"
        program_md = program_path.read_text() if program_path.exists() else ""

        # Load brand-kit.md
        brand_kit_path = team_path / "brand-kit.md"
        brand_kit_md = brand_kit_path.read_text() if brand_kit_path.exists() else ""

        # Load all agent configs (YAML or JSON)
        agents = {}
        agents_dir = team_path / "agents"
        if agents_dir.exists():
            for config_file in sorted(agents_dir.iterdir()):
                if config_file.suffix in (".yaml", ".yml", ".json"):
                    agent = AgentConfig.from_file(str(config_file))
                    agent.team = team_id
                    if not agent.id:
                        agent.id = config_file.stem
                    if not agent.name:
                        agent.name = agent.id
                    agents[agent.id] = agent

        return cls(
            id=team_id,
            name=name,
            path=str(team_path),
            goal=goal,
            program_md=program_md,
            brand_kit_md=brand_kit_md,
            schedule=schedule,
            budget_monthly=budget,
            flow=flow,
            tools=tools,
            agents=agents,
        )


@dataclass
class InstanceConfig:
    """Top-level swarma instance config."""
    name: str = "default"
    path: str = ""
    models: dict = field(default_factory=dict)
    knowledge: dict = field(default_factory=dict)
    tools: dict = field(default_factory=dict)
    runtimes: dict = field(default_factory=dict)

    @classmethod
    def from_file(cls, config_path: str) -> "InstanceConfig":
        """Load from config.yaml."""
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        instance = data.get("instance", {})
        return cls(
            name=instance.get("name", "default"),
            path=str(Path(config_path).parent),
            models=data.get("models", {}),
            knowledge=data.get("knowledge", {}),
            tools=data.get("tools", {}),
            runtimes=data.get("runtimes", {}),
        )


def _expand_env(value: str) -> str:
    """Expand ${VAR} references in string values."""
    if isinstance(value, str) and "${" in value:
        import re
        def _replace(m):
            return os.environ.get(m.group(1), m.group(0))
        return re.sub(r"\$\{(\w+)\}", _replace, value)
    return value


def load_all_teams(teams_dir: str) -> dict[str, TeamConfig]:
    """Load all team configs from a teams/ directory."""
    teams = {}
    teams_path = Path(teams_dir)

    if not teams_path.exists():
        return teams

    for team_dir in sorted(teams_path.iterdir()):
        if team_dir.is_dir() and not team_dir.name.startswith("_"):
            team = TeamConfig.from_directory(str(team_dir))
            teams[team.id] = team

    return teams
