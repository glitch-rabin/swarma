"""Flow DSL parser.

Parses pipeline definitions like:
    "researcher -> planner -> [writer, designer] -> analytics"

into an execution graph (list of steps, where each step is either
a single agent or a parallel group).

Grammar:
    flow     = step (" -> " step)*
    step     = agent | parallel
    parallel = "[" agent ("," agent)* "]"
    agent    = identifier (alphanumeric + hyphens)

Examples:
    "a -> b -> c"                       # sequential
    "a -> [b, c] -> d"                  # parallel middle
    "a -> [b, c, d]"                    # parallel at end
    "[a, b] -> c"                       # parallel at start
    "research -> plan -> [write, design, video] -> analyze -> report"
"""

import re
from dataclasses import dataclass, field


@dataclass
class FlowStep:
    """A single step in the flow. Either one agent or multiple in parallel."""
    agents: list[str]
    parallel: bool = False

    @property
    def is_parallel(self) -> bool:
        return len(self.agents) > 1

    def __repr__(self):
        if self.is_parallel:
            return f"[{', '.join(self.agents)}]"
        return self.agents[0] if self.agents else "empty"


@dataclass
class Flow:
    """Parsed flow definition -- ordered list of steps."""
    steps: list[FlowStep] = field(default_factory=list)
    raw: str = ""

    def __repr__(self):
        return " -> ".join(repr(s) for s in self.steps)

    def __len__(self):
        return len(self.steps)

    def __iter__(self):
        return iter(self.steps)

    @property
    def all_agents(self) -> list[str]:
        """All agent IDs in the flow, in order."""
        agents = []
        for step in self.steps:
            agents.extend(step.agents)
        return agents


def parse_flow(flow_str: str) -> Flow:
    """Parse a flow DSL string into a Flow object.

    Args:
        flow_str: e.g. "researcher -> planner -> [writer, designer] -> analytics"

    Returns:
        Flow with ordered steps.

    Raises:
        ValueError: If the flow string is invalid.
    """
    if not flow_str or not flow_str.strip():
        return Flow(steps=[], raw="")

    raw = flow_str.strip()

    # Normalize arrow spacing: "a->b", "a ->b", "a-> b" all become "a -> b"
    raw = re.sub(r"\s*->\s*", " -> ", raw)

    # Split on " -> " (the arrow separator)
    # But we need to handle brackets, so we can't just split naively
    steps = []
    current = ""
    in_bracket = False

    for char in raw:
        if char == "[":
            in_bracket = True
            current += char
        elif char == "]":
            in_bracket = False
            current += char
        elif not in_bracket and current.endswith(" -") and char == ">":
            # We hit " ->" -- finish current step (remove trailing " -")
            step_str = current[:-2].strip()
            if step_str:
                steps.append(_parse_step(step_str))
            current = ""
        elif not in_bracket and current.endswith(" ->") and char == " ":
            # " -> " complete -- already handled above
            current += char
        else:
            current += char

    # Don't forget the last step
    last = current.strip()
    # Clean up any leading " " or ">" from arrow parsing
    last = re.sub(r"^[\s>]+", "", last).strip()
    if last:
        steps.append(_parse_step(last))

    return Flow(steps=steps, raw=raw)


def _parse_step(step_str: str) -> FlowStep:
    """Parse a single step (either 'agent' or '[agent1, agent2]')."""
    step_str = step_str.strip()

    if step_str.startswith("[") and step_str.endswith("]"):
        # Parallel group
        inner = step_str[1:-1]
        agents = [a.strip() for a in inner.split(",") if a.strip()]
        if not agents:
            raise ValueError(f"Empty parallel group: {step_str}")
        return FlowStep(agents=agents, parallel=True)
    else:
        # Single agent
        agent = step_str.strip()
        if not agent:
            raise ValueError(f"Empty agent name in step: {step_str}")
        if not re.match(r"^[a-zA-Z0-9_-]+$", agent):
            raise ValueError(f"Invalid agent name: '{agent}'. Use alphanumeric, hyphens, underscores.")
        return FlowStep(agents=[agent])


def flow_to_string(flow: Flow) -> str:
    """Convert a Flow back to its DSL string representation."""
    parts = []
    for step in flow.steps:
        if step.is_parallel:
            parts.append(f"[{', '.join(step.agents)}]")
        else:
            parts.append(step.agents[0])
    return " -> ".join(parts)
