---
name: swarma
description: Growth experiment loop for AI agent teams -- generate teams from goals, run experiments, build validated playbooks. Use when you want agent swarms that learn and improve through A/B testing.
version: 0.2.0
author: swarma
license: MIT
compatibility: Requires Python 3.11+, pip, terminal access
metadata:
  repository: https://github.com/glitch-rabin/swarma
  hermes:
    tags: [experiments, learning, growth, agents, teams, pirate-funnels]
    category: productivity
    requires_toolsets: [terminal]
    required_environment_variables:
      - name: OPENROUTER_API_KEY
        prompt: "OpenRouter API key for LLM calls"
        help: https://openrouter.ai/keys
        required_for: running agent cycles
---

# swarma -- growth experiment loop for agent teams

## When to Use

- User wants to run growth experiments (hooks, landing pages, outreach, pricing, activation)
- User wants agent teams that improve over time through A/B testing, not just execute once
- User says something like "test what works", "optimize my funnel", "find the best hooks"
- User needs a validated playbook of what actually works for their specific audience/product

## What It Does

swarma gives you a dedicated experiment loop. describe a goal, it generates a team, seeds it with real growth knowledge, and runs:

```
strategy.md → execute → measure → verdict → updated strategy.md
```

Results live in swarma (SQLite + markdown files), not in your memory. The playbook grows automatically. You just set direction and review what worked.

## Onboarding Flow

When a user wants to set up swarma, the fastest path is the team generator. Don't make them configure agents manually.

### Step 1: Understand the goal

Ask:
- "What do you want to improve?" (conversion, engagement, outreach response rate, SEO rankings, etc.)
- "Who is your audience?" (B2B SaaS users, crypto community, enterprise buyers, etc.)
- "What does success look like?" (more signups, higher CTR, better reply rates, etc.)

### Step 2: Install and configure

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma && pip install -e .
swarma init --yes
```

Add the OpenRouter API key:
```bash
echo "OPENROUTER_API_KEY=sk-or-..." >> ~/.swarma/instances/default/.env
```

### Step 3: Generate the team from the goal

This is the key step. Use the team generator instead of picking templates.

```bash
swarma team create growth-lab \
  --from-goal "optimize landing page conversion for our B2B SaaS" \
  --context "developer tools company, 500 free users, 2% conversion to paid" \
  --budget 30
```

The generator:
1. Designs the team (2-5 agents with specific roles)
2. Picks the cheapest models that fit each role
3. Writes agent instructions and experiment patterns
4. Creates a first experiment hypothesis ready to run

Review what it generated:
```bash
swarma team show growth-lab
```

### Step 4: Run the first cycle

```bash
swarma cycle growth-lab
```

This runs the full pipeline: agents execute in flow order, outputs get scored, experiments track progress.

### Step 5: Connect as MCP server (optional)

So you can run cycles and query results without leaving your context:

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

**REST API** (for custom integrations):
```bash
swarma serve --port 8282    # OpenAPI docs at /docs
```

**Important**: when running as an MCP subprocess, `OPENROUTER_API_KEY` must be passed in the `env` block. The instance `.env` file is not inherited by subprocesses.

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

## Typical Workflow

Once swarma is running:

1. **Generate a team**: "create a team to test which hook angles work best for developer audiences"
2. **Run cycles**: `run_cycle` with the team name, or set up a cron schedule
3. **Feed real metrics**: `swarma metric log hook-lab copywriter 4.2 --metric ctr_pct`
4. **Read the playbook**: `get_playbook` to see what the experiments have validated
5. **Iterate**: refine the goal, adjust constraints, generate new teams for different funnel stages

## Key Concepts

**The loop is the product.** Every cycle, agents read their strategy, produce output, get scored, and the strategy evolves. After enough cycles, you have a validated playbook.

**Agents start with real knowledge.** Strategy files are pre-seeded with validated growth patterns. The experiment loop refines these -- it doesn't start from scratch.

**You are the executive.** Set goals, review playbooks, approve experiments. The swarm handles the messy work.

**External metrics close the gap.** LLM self-eval is a proxy. For production, feed back real signals via `swarma metric log`, CSV import, or webhooks.

## AARRR Funnel Coverage

| Stage | Squad | What it experiments on |
|-------|-------|----------------------|
| Acquisition | hook-lab, landing-lab, seo-engine, cold-outbound | hooks, landing pages, search, outreach |
| Activation | activation-flow | onboarding, time-to-value, empty states |
| Revenue | pricing-lab | pricing presentation, packaging, anchoring |
| Retention | retention-squad | churn signals, win-back, engagement |
| Referral | referral-engine | viral loops, incentives, invite mechanics |

## Pitfalls

- `OPENROUTER_API_KEY` must be in the MCP `env` config when running as a subprocess
- First run creates the SQLite database -- queries need at least one completed cycle
- Strategy files evolve after `min_sample_size` experiments (default: 3-5)
- Self-eval is the starting measurement -- feed real metrics for production decisions
- QMD needs to be running (`qmd serve`) before starting swarma for cross-team knowledge

## Verification

After setup, verify the loop works:
```bash
swarma cycle starter    # should show agent outputs + costs
swarma status           # should show the run in recent history
```
