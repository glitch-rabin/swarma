---
name: swarma
description: Experiment loop for AI agent teams -- run cycles, check experiments, read the evolving playbook
version: 0.1.0
metadata:
  hermes:
    tags: [experiments, learning, growth, agents, teams]
    category: productivity
    requires_toolsets: [terminal]
    required_environment_variables:
      - name: OPENROUTER_API_KEY
        prompt: "OpenRouter API key for LLM calls"
        help: https://openrouter.ai/keys
        required_for: running agent cycles
---

# swarma -- experiment loop for agent teams

## When to Use

- You want agent teams that improve over time, not just execute once
- You need to run growth experiments, content testing, or research workflows on a schedule
- You want experiment results and strategy evolution tracked outside your main context

## What It Does

swarma gives you a dedicated experiment loop. each agent gets one metric, one strategy file, and a feedback cycle:

```
strategy.md → execute → measure → verdict → updated strategy.md
```

Results live in swarma (SQLite + markdown files), not in your memory. Query what teams learned via MCP tools without polluting your context window.

## Setup

```bash
# Install (one time)
git clone https://github.com/glitch-rabin/swarma.git
cd swarma && pip install -e .

# Initialize
swarma init

# Verify
swarma cycle starter
```

## Available MCP Tools

Once connected via MCP, you get these tools:

| Tool | What it does |
|------|-------------|
| `run_cycle` | Run a cycle for a team |
| `list_teams` | Show all configured teams |
| `get_status` | Instance status (costs, runs, experiments) |
| `list_experiments` | All experiments with status and verdicts |
| `get_playbook` | Validated patterns from strategy files |
| `get_agent_strategy` | Read an agent's current strategy.md |
| `list_outputs` | Recent outputs from agents |
| `approve_plan` | Approve a pending experiment plan |
| `reject_plan` | Reject a pending plan |
| `push_metric` | Push external metric data into the loop |

## Typical Workflow

1. **Set direction**: "run the hook-lab team and test contrarian vs data-led hooks"
2. **Check progress**: `get_status` or `list_experiments` to see what's running
3. **Read learnings**: `get_playbook` to see validated patterns across all teams
4. **Approve plans**: review and approve/reject proposed experiments
5. **Push real data**: `push_metric` to feed real analytics back into the loop

## Key Concept

You (hermes) are the executive. swarma is the department. You set goals and review results. The department runs experiments 24/7 and evolves its own strategies. The messy work (500 hook variations, inconclusive experiments, strategy rewrites) stays in swarma. You just see what worked.

## Knowledge Layer (QMD)

swarma includes a knowledge layer powered by [QMD](https://github.com/glitch-rabin/qmd) -- a search engine that indexes agent outputs for cross-team retrieval. BM25 + vector + rerank. no GPU required.

### setup

```bash
pip install qmd
qmd init
qmd serve                    # runs on http://localhost:8181
```

### connect to swarma

in your instance `config.yaml`, set the knowledge engine:

```yaml
knowledge:
  engine: qmd
  qmd_endpoint: http://localhost:8181/mcp
```

once connected, every agent output gets indexed automatically. agents can search what other agents learned -- the experiment loop gets a shared memory layer across teams.

without QMD, swarma falls back to local SQLite search (metadata only, no semantic search). with QMD, you get full-text + vector search across all agent outputs, strategies, and experiment results.

## Pitfalls

- swarma needs an OpenRouter API key in `~/.swarma/instances/default/.env`
- First run creates the SQLite database -- subsequent queries require at least one completed cycle
- Strategy files only start evolving after `min_sample_size` experiments (default: 3-5)
- Self-eval is the default measurement -- good for prototyping, wire in real signals for production
- QMD needs to be running (`qmd serve`) before starting swarma if you want semantic search

## Verification

After setup, verify the loop works:
```bash
swarma cycle starter    # should show agent outputs + costs
swarma status           # should show the run in recent history
```
