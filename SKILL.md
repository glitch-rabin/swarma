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

- User wants agent teams that improve over time, not just execute once
- User needs to run growth experiments, content testing, or research workflows
- User wants experiment results and strategy evolution tracked outside your context

## What It Does

swarma gives you a dedicated experiment loop. each agent gets one metric, one strategy file, and a feedback cycle:

```
strategy.md → execute → measure → verdict → updated strategy.md
```

Results live in swarma (SQLite + markdown files), not in your memory. Query what teams learned via MCP tools without polluting your context window.

## Onboarding Flow

When a user asks you to set up swarma, interview them first. Don't jump straight to install.

### Step 1: Understand the goal

Ask:
- "What do you want to experiment on?" (content hooks, outreach sequences, ad copy, research, pricing, etc.)
- "What does success look like?" (more engagement, higher conversion, better quality scores, etc.)

### Step 2: Understand the setup

Ask:
- "Do you have an OpenRouter API key?" (required -- get one at https://openrouter.ai/keys)
- "Do you have a model preference?" (swarma works with any model via OpenRouter -- cheap models work fine for experimentation)
- "Where should this run?" (laptop, VPS, server -- swarma is lightweight, no GPU needed)

### Step 3: Pick a starting squad

Based on their goal, suggest one of the 10 example squads:
- **hook-lab** -- testing content hooks (3 agents: researcher, copywriter, judge)
- **channel-mix** -- multi-platform content (4 agents: strategist + 3 writers)
- **cold-outbound** -- outreach optimization (3 agents: researcher, copywriter, personalization)
- **seo-engine** -- search optimization (3 agents: keyword researcher, writer, auditor)
- **activation-flow** -- user onboarding (3 agents: researcher, sequence designer, evaluator)
- **pricing-lab** -- pricing experiments (3 agents: researcher, analyst, page writer)
- **landing-lab** -- landing page copy (3 agents: researcher, copywriter, critic)
- **retention-squad** -- churn prevention (3 agents: signal monitor, analyst, outreach writer)
- **referral-engine** -- referral loop design (3 agents: analyst, loop designer, outreach writer)
- **competitive-intel** -- market monitoring (3 agents: scanner, analyst, briefer)

Or start with the built-in **starter** team (thinker -> writer) to verify the install works.

### Step 4: Install and configure

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma && pip install -e .
swarma init --yes
```

Add the OpenRouter API key:
```bash
echo "OPENROUTER_API_KEY=sk-or-..." >> ~/.swarma/instances/default/.env
```

Verify it works:
```bash
swarma cycle starter
```

If the user chose a squad, copy it in:
```bash
cp -r examples/hook-lab ~/.swarma/instances/default/teams/
swarma cycle hook-lab
```

### Step 5: Connect as MCP server

Add swarma to your MCP config so you can run cycles and query results without leaving your context:

**Hermes** (`config.yaml`):
```yaml
mcp_servers:
  swarma:
    transport: stdio
    command: swarma
    args: ["serve", "--mcp"]
    env:
      OPENROUTER_API_KEY: "sk-or-..."
```

**Claude Code / Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "swarma": {
      "command": "swarma",
      "args": ["serve", "--mcp"],
      "env": { "OPENROUTER_API_KEY": "sk-or-..." }
    }
  }
}
```

**REST API** (for dashboards or custom integrations):
```bash
swarma serve --port 8282    # OpenAPI docs at /docs
```

**Important**: when running as an MCP subprocess, `OPENROUTER_API_KEY` must be passed in the `env` block of your MCP config. The instance `.env` file is not inherited by subprocesses.

## Available MCP Tools

Once connected, you get these tools:

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

Once swarma is running and connected:

1. **Set direction**: "run the hook-lab team and test contrarian vs data-led hooks"
2. **Check progress**: `get_status` or `list_experiments` to see what's running
3. **Read learnings**: `get_playbook` to see validated patterns across all teams
4. **Approve plans**: review and approve/reject proposed experiments
5. **Push real data**: `push_metric` to feed real analytics back into the loop

## Key Concept

You are the executive. swarma is the department. You set goals and review results. The department runs experiments and evolves its own strategies. The messy work (500 hook variations, inconclusive experiments, strategy rewrites) stays in swarma. You just see what worked.

## Knowledge Layer (QMD)

swarma includes a knowledge layer powered by [QMD](https://github.com/glitch-rabin/qmd) -- a search engine that indexes agent outputs for cross-team retrieval. BM25 + vector + rerank. no GPU required.

### setup

```bash
pip install qmd
qmd init
qmd serve                    # runs on http://localhost:8181
```

### connect to swarma

in the instance `config.yaml`, set the knowledge engine:

```yaml
knowledge:
  engine: qmd
  qmd_endpoint: http://localhost:8181/mcp
```

once connected, every agent output gets indexed automatically. agents can search what other agents learned -- the experiment loop gets a shared memory layer across teams.

without QMD, swarma falls back to local SQLite search (metadata only, no semantic search). with QMD, you get full-text + vector search across all agent outputs, strategies, and experiment results.

## Pitfalls

- `OPENROUTER_API_KEY` must be in the MCP `env` config when running as a subprocess (not just in the instance `.env`)
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
