"""Test script: run 5 cycles across 2 teams and prove the experiment loop closes.

Usage:
    cd projects/swarma
    python test_loop.py

This will:
1. Load the test instance from ~/.swarma/instances/test/
2. Run content-ops team (researcher -> writer) 5 times
3. Run quality-lab team (auditor) after each content-ops cycle
4. Print results.tsv, strategy.md evolution, and QMD artifacts after each cycle
"""

import asyncio
import logging
import os
import sys

# Add swarma to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from swarma.cli.helpers import build_engine, load_env, load_teams, get_instance_path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Quiet down httpx
logging.getLogger("httpx").setLevel(logging.WARNING)

INSTANCE = "test"
NUM_CYCLES = 5


async def main():
    instance_path = get_instance_path(INSTANCE)

    if not instance_path.exists():
        print(f"Instance not found: {instance_path}")
        print("Run the team config setup first.")
        sys.exit(1)

    load_env(instance_path)
    engine = build_engine(instance_path)

    teams = list(engine.teams.keys())
    print(f"\n{'='*60}")
    print(f"SWARMA EXPERIMENT LOOP TEST")
    print(f"{'='*60}")
    print(f"Instance: {instance_path}")
    print(f"Teams: {teams}")
    print(f"Cycles: {NUM_CYCLES}")
    print(f"{'='*60}\n")

    for cycle_num in range(1, NUM_CYCLES + 1):
        print(f"\n{'─'*60}")
        print(f"CYCLE {cycle_num}/{NUM_CYCLES}")
        print(f"{'─'*60}")

        # Run content-ops first (produces content)
        if "content-ops" in engine.teams:
            print(f"\n▸ Running content-ops...")
            try:
                result = await engine.run_cycle("content-ops")
                _print_result(result)
            except Exception as e:
                print(f"  ERROR: {e}")

        # Run quality-lab second (evaluates content from knowledge store)
        if "quality-lab" in engine.teams:
            print(f"\n▸ Running quality-lab...")
            try:
                result = await engine.run_cycle("quality-lab")
                _print_result(result)
            except Exception as e:
                print(f"  ERROR: {e}")

        # Print experiment state after each cycle
        _print_experiment_state(instance_path)

    # Final summary
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS")
    print(f"{'='*60}")
    _print_experiment_state(instance_path, verbose=True)

    # Print costs
    daily = engine.state.get_daily_cost()
    print(f"\nTotal cost today: ${daily:.4f}")

    await engine.close()
    print("\nDone.")


def _print_result(result: dict):
    """Print cycle result summary."""
    for agent_id, r in result.get("results", {}).items():
        content_preview = r.get("content", "")[:100].replace("\n", " ")
        cost = r.get("cost", 0)
        model = r.get("model", "?")
        if "/" in model:
            model = model.split("/")[-1]

        print(f"  {agent_id} ({model}): ${cost:.4f}")
        print(f"    output: {content_preview}...")

        eval_data = r.get("evaluation")
        if eval_data:
            if "verdict" in eval_data:
                print(f"    VERDICT: {eval_data['verdict']} (score: {eval_data.get('score', '?'):.1f})")
            elif "new_experiment" in eval_data:
                print(f"    NEW EXPERIMENT #{eval_data['new_experiment']} (baseline: {eval_data['baseline_score']:.1f})")
            elif "score" in eval_data:
                print(f"    score: {eval_data['score']:.1f} (sample {eval_data.get('samples', '?')}/{eval_data.get('needed', '?')})")

    errors = result.get("errors", {})
    if errors:
        for aid, err in errors.items():
            print(f"  {aid}: ERROR - {err}")

    print(f"  total: ${result.get('total_cost', 0):.4f} | {result.get('duration_seconds', 0):.1f}s")


def _print_experiment_state(instance_path, verbose=False):
    """Print current experiment state from results.tsv files."""
    teams_dir = instance_path / "teams"
    for team_dir in sorted(teams_dir.iterdir()):
        if not team_dir.is_dir():
            continue
        results_dir = team_dir / "results"
        if not results_dir.exists():
            continue

        for agent_dir in sorted(results_dir.iterdir()):
            if not agent_dir.is_dir():
                continue

            results_file = agent_dir / "results.tsv"
            strategy_file = agent_dir / "strategy.md"

            if results_file.exists():
                lines = results_file.read_text().strip().split("\n")
                data_lines = lines[1:]  # skip header
                if data_lines:
                    print(f"\n  [{team_dir.name}/{agent_dir.name}] results.tsv ({len(data_lines)} entries):")
                    for line in data_lines[-3:]:  # show last 3
                        parts = line.split("\t")
                        if len(parts) >= 4:
                            print(f"    {parts[0]} | score={parts[2]} | {parts[3]} | {parts[4][:50] if len(parts) > 4 else ''}")

            if verbose and strategy_file.exists():
                strategy = strategy_file.read_text()
                if "Validated" in strategy:
                    print(f"\n  [{team_dir.name}/{agent_dir.name}] strategy.md (evolved!):")
                    # Show just the validated sections
                    for line in strategy.split("\n"):
                        if "Validated" in line or line.startswith(">"):
                            print(f"    {line}")


if __name__ == "__main__":
    asyncio.run(main())
