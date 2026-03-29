"""Experiment loop engine -- Karpathy autoresearch pattern.

The core loop:
  Agent reads strategy.md (editable) → proposes experiment → executes
  → measures → ratchets (keep/discard) → logs to results.tsv

Every agent has one metric. Every experiment changes one thing.
"""

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Experiment:
    id: int
    agent_id: str
    team_id: str
    hypothesis: str
    metric_name: str
    baseline: Optional[float]
    target: Optional[float]
    sample_size_needed: int
    sample_size_current: int
    result: Optional[float]
    verdict: str  # running | keep | discard | inconclusive


@dataclass
class ExperimentResult:
    date: str
    output_id: str
    metric_value: float
    status: str  # keep | discard | inconclusive | pending
    description: str


class ExperimentEngine:
    """Manages the experiment loop for a single agent."""

    VERDICT_THRESHOLD = 0.20  # 20% improvement = meaningful

    def __init__(self, team_dir: str, agent_id: str):
        self.agent_dir = Path(team_dir) / "results" / agent_id
        self.agent_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.agent_dir / "results.tsv"
        self.strategy_file = self.agent_dir / "strategy.md"
        self.experiments_dir = self.agent_dir / "experiments"
        self.experiments_dir.mkdir(exist_ok=True)

        if not self.results_file.exists():
            self.results_file.write_text("date\toutput_id\tmetric_value\tstatus\tdescription\n")

        if not self.strategy_file.exists():
            self.strategy_file.write_text("# Current Strategy\n\nNo strategy set yet. First experiment pending.\n")

    def get_strategy(self) -> str:
        return self.strategy_file.read_text()

    def update_strategy(self, new_strategy: str):
        self.strategy_file.write_text(new_strategy)

    def get_results(self, limit: int = 50) -> list[ExperimentResult]:
        """Read recent results from results.tsv."""
        results = []
        if not self.results_file.exists():
            return results

        with open(self.results_file, newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                try:
                    results.append(ExperimentResult(
                        date=row.get("date", ""),
                        output_id=row.get("output_id", row.get("post_id", "")),
                        metric_value=float(row.get("metric_value", 0)),
                        status=row.get("status", ""),
                        description=row.get("description", ""),
                    ))
                except (ValueError, KeyError):
                    continue

        return results[-limit:]

    def log_result(self, output_id: str, metric_value: float,
                   status: str, description: str):
        """Append a result to results.tsv."""
        with open(self.results_file, "a", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                output_id,
                f"{metric_value:.4f}",
                status,
                description,
            ])

    def evaluate_experiment(self, experiment: Experiment,
                            results: list[ExperimentResult]) -> str:
        """Determine verdict based on collected results.

        Returns: 'keep' | 'discard' | 'inconclusive' | 'running'
        """
        if len(results) < experiment.sample_size_needed:
            return "running"

        avg_metric = sum(r.metric_value for r in results) / len(results)

        if experiment.baseline is None or experiment.baseline == 0:
            # No baseline or zero baseline -- can't compute relative improvement
            return "keep" if experiment.baseline is None else "inconclusive"

        improvement = (avg_metric - experiment.baseline) / experiment.baseline

        if improvement > self.VERDICT_THRESHOLD:
            return "keep"
        elif improvement < -self.VERDICT_THRESHOLD:
            return "discard"
        else:
            return "inconclusive"

    def save_experiment_log(self, experiment: Experiment, verdict: str,
                            results: list[ExperimentResult]):
        """Save detailed experiment log to experiments/ directory."""
        exp_file = self.experiments_dir / f"exp-{experiment.id:03d}.md"
        avg = sum(r.metric_value for r in results) / len(results) if results else 0

        content = f"""# Experiment {experiment.id}: {experiment.hypothesis}

**Agent:** {experiment.agent_id}
**Metric:** {experiment.metric_name}
**Baseline:** {experiment.baseline}
**Result:** {avg:.4f}
**Verdict:** {verdict}
**Sample size:** {len(results)} / {experiment.sample_size_needed}

## Results

| Date | Output ID | Metric | Description |
|------|-----------|--------|-------------|
"""
        for r in results:
            content += f"| {r.date} | {r.output_id} | {r.metric_value:.4f} | {r.description} |\n"

        if verdict == "keep":
            content += f"\n## Strategy Update\nKept: {experiment.hypothesis}\n"
        elif verdict == "discard":
            content += f"\n## Strategy Reverted\nDiscarded: {experiment.hypothesis}\n"
        else:
            content += f"\n## Inconclusive\nNot enough signal. Consider extending or redesigning.\n"

        exp_file.write_text(content)
