---
name: swarma
description: Growth experiment loop for AI agent teams. Generate teams from goals, run GROWS experiments, build validated playbooks. Agents that learn and improve through A/B testing, not just execute once.
version: 0.2.0
license: MIT
compatibility: Python 3.11+, pip, terminal access
metadata:
  repository: https://github.com/glitch-rabin/swarma
  website: https://swarma.dev
  hermes:
    tags: [experiments, learning, growth, agents, teams, swarms, pirate-funnels, AARRR, playbook]
    category: productivity
    requires_toolsets: [terminal]
    required_environment_variables:
      - name: OPENROUTER_API_KEY
        prompt: "OpenRouter API key for LLM calls"
        help: https://openrouter.ai/keys
        required_for: running agent cycles
---

# swarma -- growth experiment loop for agent teams

## When to Use This Skill

Use swarma when the user wants to:

- Run growth experiments (hooks, landing pages, outreach, pricing, activation, retention)
- Build agent teams that **learn and improve** through A/B testing, not just execute once
- Get a validated playbook of what actually works for their specific audience/product
- Test ideas at scale (50+ experiments/week instead of 2-5)
- Replace "we tried that, it didn't work" with logged, analyzed, searchable experiment data

**Trigger phrases**: "test what works", "optimize my funnel", "find the best hooks", "run experiments", "A/B test", "what's working", "build a playbook", "growth experiments", "improve conversion"

**Do NOT use when**: user wants workflow automation (use n8n/Make), conversation memory (use honcho), or one-shot agent pipelines (use CrewAI/AutoGen). swarma is specifically for experiment loops that improve over time.

---

## Quick Reference

### Commands at a Glance

| Command | What it does | When to use |
|---------|-------------|-------------|
| `swarma init` | Create instance + starter team | First-time setup |
| `swarma cycle <team>` | Run one experiment cycle | Testing, manual runs |
| `swarma cycle <team> --topic "..."` | Run cycle with a specific topic | Ad-hoc experiments |
| `swarma team create <name> --from-goal "..."` | Generate team from a goal | Starting a new experiment area |
| `swarma team show <name>` | Inspect a team's config | Reviewing what was generated |
| `swarma team list` | Show all teams | Overview |
| `swarma status` | Costs, recent runs, experiments | Health check |
| `swarma metric log <team> <agent> <value>` | Log external metric | Feeding real-world data |
| `swarma metric import <team> <csv>` | Bulk import metrics | Batch data ingestion |
| `swarma metric show <team>` | View logged metrics | Reviewing performance |
| `swarma serve --port 8282` | Start REST API | External integrations |
| `swarma serve --mcp` | Start MCP server | Claude Code / Hermes integration |
| `swarma run` | Start scheduled engine | Continuous operation |
| `swarma expert list` | Browse reasoning lenses | Exploring expert frameworks |

### Decision: Which Squad Template?

| User wants to improve... | Use this squad | AARRR stage |
|--------------------------|---------------|-------------|
| Opening lines / hooks | `hook-lab` | Acquisition |
| Landing page copy | `landing-lab` | Acquisition |
| SEO rankings | `seo-engine` | Acquisition |
| Cold outreach response rates | `cold-outbound` | Acquisition |
| Multi-platform content | `channel-mix` | Acquisition |
| Signup-to-value onboarding | `activation-flow` | Activation |
| Pricing and packaging | `pricing-lab` | Revenue |
| Churn and retention | `retention-squad` | Retention |
| Viral loops and referrals | `referral-engine` | Referral |
| Market positioning | `competitive-intel` | -- |
| Short-form video pipeline | `faceless-factory` | Acquisition |
| Ad creative testing | `ad-creative-lab` | Acquisition |
| UGC content simulation | `ugc-factory` | Acquisition |
| Programmatic SEO | `programmatic-seo` | Acquisition |
| Newsletter growth | `newsletter-engine` | Retention |
| Paid + organic loops | `acquisition-squad` | Acquisition |
| Community-led growth | `community-engine` | Retention |
| AI commerce optimization | `agentic-storefront` | Revenue |

### Decision: Generate vs Template?

| Situation | Approach |
|-----------|----------|
| User has a specific, well-defined goal | `swarma team create --from-goal` (let AI design the team) |
| Goal matches an existing squad template | Copy template, then customize |
| User wants to experiment broadly | Start with `hook-lab` (most general) |
| User doesn't know where to start | Ask about their funnel bottleneck, then pick |

---

## The GROWS Loop (Core Concept)

Every experiment cycle follows five steps:

```
  Generate       Run         Observe       Weigh        Stack
 hypothesis --> experiment --> signal --> verdict --> playbook
     ^                                                  |
     └──────────────────────────────────────────────────┘
```

| Step | What happens | Where in code |
|------|-------------|---------------|
| **G -- Generate** | Agent reads `strategy.md`, proposes a hypothesis | `core/cycle.py` |
| **R -- Run** | Agent executes with hypothesis active, produces output | `flow/executor.py` |
| **O -- Observe** | Separate cheap LLM scores output (1-10, forced decimals) | `core/agent.py` |
| **W -- Weigh** | After 5 cycles, compare average vs baseline. >20% = keep/discard | `core/experiment.py` |
| **S -- Stack** | Validated patterns written to `strategy.md` + playbook | `core/agent.py` |

**Key numbers:**
- Verdict threshold: 20% improvement to keep, 20% decline to discard
- Default `min_sample_size`: 5 cycles before verdict
- Scoring: 1-10 scale with forced decimals (7.3, not 7)

---

## Setup Guide

### Platform: Claude Code / Claude Desktop

```bash
pip install swarma
swarma init
```

Add to `.mcp.json`:

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

**Important**: `OPENROUTER_API_KEY` must be in the MCP `env` block. The instance `.env` is not inherited by subprocesses.

### Platform: Hermes (via terminal)

Hermes has terminal access -- it can run swarma CLI commands directly. No MCP required.

```bash
pip install swarma
swarma init
```

Then tell Hermes: *"run `swarma cycle hook-lab --topic 'AI agents are overhyped'`"*

Hermes reads terminal output and acts on results. For structured access, add MCP:

```yaml
# hermes config.yaml
mcp_servers:
  swarma:
    transport: stdio
    command: swarma
    args: ["serve", "--mcp"]
    env:
      OPENROUTER_API_KEY: "sk-or-..."
```

### Platform: OpenClaw

```bash
pip install swarma
swarma init
```

Configure as MCP tool or use terminal access depending on your OpenClaw setup.

### Platform: CLI (standalone)

```bash
pip install swarma
swarma init                                        # creates instance + starter team
swarma cycle starter --topic "why do startups fail?"   # run one cycle
swarma status                                      # check costs, runs, experiments
```

### From source

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma && pip install -e .
swarma init
```

### Environment setup

After `swarma init`, add your API key:

```bash
echo "OPENROUTER_API_KEY=sk-or-..." >> ~/.swarma/instances/default/.env
```

Get a key at [openrouter.ai/keys](https://openrouter.ai/keys).

Optional (for cross-team knowledge):

```bash
# Only needed when running 3+ teams
echo "QMD_ENDPOINT=http://localhost:8181/mcp" >> ~/.swarma/instances/default/.env
```

---

## Onboarding Flow

When a user wants to set up swarma, follow this sequence. The team generator is the fastest path -- don't make users configure agents manually.

### Step 1: Understand the goal

Ask:
- "What do you want to improve?" (conversion, engagement, outreach response rate, SEO rankings, etc.)
- "Who is your audience?" (B2B SaaS users, crypto community, enterprise buyers, etc.)
- "What does success look like?" (more signups, higher CTR, better reply rates, etc.)

### Step 2: Install

```bash
pip install swarma
swarma init --yes
```

### Step 3: Generate the team

This is the key step. Use the team generator instead of picking templates.

```bash
swarma team create growth-lab \
  --from-goal "optimize landing page conversion for our B2B SaaS" \
  --context "developer tools company, 500 free users, 2% conversion to paid" \
  --budget 30
```

The generator:
1. Designs the team (2-5 agents with specific roles)
2. Picks models that fit each role
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

Expected output:

```
Running cycle: growth-lab
  flow: researcher -> copywriter -> judge
  agents: ['researcher', 'copywriter', 'judge']

                              Cycle: growth-lab
  Agent      Model              Cost       Output Preview
  researcher sonar-pro          $0.000384  **Topic:** 52% of executives...
  copywriter qwen3.5-plus-02-15 $0.000746  [A] We sent 4,382 cold emails...
  judge      mistral-nemo       $0.000416  **Hook Variations:** A: "Did...

  duration: 43.9s | total cost: $0.001546 | agents: 3
```

### Step 5: Run more cycles and review

```bash
swarma cycle growth-lab                    # run another cycle
swarma cycle growth-lab --topic "specific angle"  # with a topic
swarma status                              # check progress
```

After 5 cycles, the experiment engine issues its first verdict. The strategy file evolves automatically.

---

## Day-to-Day Usage

### Running experiments

```bash
# Single cycle
swarma cycle hook-lab

# With a specific topic
swarma cycle hook-lab --topic "AI agents are commoditizing"

# Continuous (teams with cron schedules run automatically)
swarma run

# Continuous with API server
swarma run --port 8282
```

### Feeding real metrics

LLM self-eval is a starting proxy. For production, feed back real-world signals:

```bash
# Log a single metric
swarma metric log hook-lab copywriter 4.2 --metric ctr_pct

# Attach to a specific experiment
swarma metric log hook-lab copywriter 127 --metric impressions --exp 3

# Add a note
swarma metric log hook-lab copywriter 5.1 --metric ctr_pct --note "from linkedin analytics"

# Bulk import from CSV
swarma metric import hook-lab metrics.csv

# View logged metrics
swarma metric show hook-lab
```

CSV format: `agent,value,metric_name,note`

```csv
copywriter,4.2,ctr_pct,week 1
copywriter,5.1,ctr_pct,week 2
researcher,7.8,relevance_score,
```

### Using squad templates

```bash
# Copy a template to your instance
cp -r "$(python -c "import swarma; print(swarma.__path__[0])")/examples/hook-lab" \
  ~/.swarma/instances/default/teams/hook-lab

# Or if you cloned the repo
cp -r examples/hook-lab ~/.swarma/instances/default/teams/hook-lab

# Run it
swarma cycle hook-lab --topic "why most startups fail"
```

### Checking status

```bash
swarma status
```

Shows: all teams, recent runs, costs (today + this month), pending plans, queue stats.

---

## MCP Tools Reference

When connected via MCP, these 16 tools are available:

| Tool | Description | Parameters |
|------|-------------|------------|
| `swarma_health` | Check if swarma is running | -- |
| `swarma_list_teams` | List all configured teams | -- |
| `swarma_get_team` | Get team details (agents, flow, schedule) | `team_id` |
| `swarma_list_agents` | List agents in a team | `team_id` |
| `swarma_run_agent` | Run a single agent with optional context | `team_id`, `agent_id`, `context?` |
| `swarma_run_cycle` | Run a full cycle for a team | `team_id`, `topic?` |
| `swarma_status` | Instance status (costs, runs, experiments) | -- |
| `swarma_costs` | Cost breakdown (today, this month) | -- |
| `swarma_list_plans` | Show pending experiment plans | `team_id?` |
| `swarma_approve_plan` | Approve a pending experiment plan | `plan_id` |
| `swarma_reject_plan` | Reject a pending plan | `plan_id`, `reason?` |
| `swarma_get_outputs` | Recent outputs from agents | `team_id?`, `agent_id?`, `limit?` |
| `swarma_list_tools` | List available agent tools | -- |
| `swarma_list_experts` | Browse expert reasoning lenses | -- |
| `swarma_get_expert` | Get expert details by ID | `expert_id` |
| `swarma_generate_team` | Generate a new team from a goal | `name`, `goal`, `context?`, `budget?` |

### Common MCP Workflows

**"What's been happening?"**
1. `swarma_status` -- overview
2. `swarma_get_outputs` -- recent agent outputs
3. `swarma_list_plans` -- pending experiments

**"Run an experiment"**
1. `swarma_run_cycle` with team_id and optional topic
2. `swarma_get_outputs` to review results

**"Start a new experiment area"**
1. `swarma_generate_team` with goal and context
2. `swarma_get_team` to review what was generated
3. `swarma_run_cycle` to kick it off

**"What's working?"**
1. `swarma_get_outputs` for recent results
2. Read the team's `strategy.md` for validated patterns

---

## Team Configuration Reference

A team is a folder. No code required.

```
teams/my-squad/
├── team.yaml          # goal, flow, schedule, budget
├── program.md         # team context and constraints
└── agents/
    ├── researcher.yaml
    ├── writer.yaml
    └── strategy.md    # pre-seeded growth knowledge (evolves automatically)
```

### team.yaml

```yaml
name: my-squad
goal: find what works.
flow: "researcher -> writer"        # sequential
# flow: "researcher -> [writer, analyst]"  # parallel
schedule: "0 8 * * 1-5"            # optional: weekdays at 8am
budget: 30                          # optional: monthly budget in $
```

### agent.yaml

```yaml
id: writer
name: Writer
instructions: |
  turn research into a post. max 200 words.
  hook in the first line. practitioner voice.
model: qwen/qwen3.5-plus-02-15     # optional: override default routing
metric:
  name: content_quality
  target: 8.0
experiment_config:
  min_sample_size: 5
  auto_propose: true
```

### strategy.md (evolves automatically)

Starts with seed knowledge, grows with every validated experiment:

```markdown
### Validated Patterns

**Specificity wins**
- Hooks with specific numbers outperform vague claims by 2-3x on saves
- "47% of startups" > "most startups"

### Anti-patterns (Discarded)
- Generic inspirational openings: -23% vs baseline. Discard.

### Patterns to Test
- [ ] First-person confession vs third-person case study
- [ ] Time-anchored ("In 2024...") vs timeless hooks
```

### Flow DSL

```yaml
# Sequential: a runs, output passes to b
flow: "researcher -> writer"

# Parallel: a runs, then b and c run concurrently
flow: "researcher -> [writer, analyst]"

# Mixed: sequential then parallel then sequential
flow: "researcher -> [writer, analyst] -> judge"
```

---

## Cross-Team Knowledge (QMD)

By default, each team learns individually via its own `strategy.md`. To share knowledge across teams, wire in QMD:

```yaml
# ~/.swarma/instances/default/config.yaml
knowledge:
  engine: qmd
  qmd_endpoint: http://localhost:8181/mcp
```

With QMD: team A discovers loss framing beats gain framing, team B sees that pattern in its next cycle. Anti-patterns are shared too.

**You don't need QMD** until running 3+ teams. Most users start without it.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "No API key found" | Missing `OPENROUTER_API_KEY` | Add to `~/.swarma/instances/default/.env` |
| MCP subprocess can't find key | Instance `.env` not inherited | Pass key in MCP config `env` block |
| "No teams found" | Empty instance | Run `swarma init` or copy a squad template |
| Experiments not issuing verdicts | Not enough cycles | Need `min_sample_size` (default 5) completed cycles |
| Strategy file not evolving | No verdict yet | Run more cycles, check `swarma status` |
| `swarma cycle` shows $0.000000 cost | Model returned empty | Check API key validity, try `swarma cycle starter` |
| QMD not connecting | QMD not running | Start with `qmd serve` before swarma |
| Results.tsv empty | No cycles completed | Run at least one cycle first |

---

## Verification

After setup, verify everything works:

```bash
# 1. Run a cycle
swarma cycle starter --topic "test run"
# Expected: table showing agent outputs + costs

# 2. Check status
swarma status
# Expected: teams listed, recent run shown, costs displayed

# 3. Check a real squad (if installed)
swarma team show hook-lab
# Expected: team config with agents, flow, metrics
```

If all three pass, the GROWS loop is operational.

---

## What swarma Is Not

| swarma is not... | Use this instead | The difference |
|-------------------|-----------------|----------------|
| **memory** | honcho | swarma doesn't remember conversations. it runs experiment loops. |
| **workflow automation** | n8n, Make, Zapier | those connect apps. swarma runs hypotheses and learns from results. |
| **a prompt library** | agency-agents | swarma teaches agents what works through feedback. templates go in, playbooks come out. |
| **agent orchestration** | CrewAI, AutoGen, LangGraph | those run pipelines. swarma adds the GROWS loop that makes pipelines improve. |
| **a hosted service** | -- | self-hosted. your data stays on your machine. |
