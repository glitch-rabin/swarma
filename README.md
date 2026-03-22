# swarma

**English** | [中文](README_CN.md) | [日本語](README_JA.md)

agent teams that learn what works.

---

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

swarma is a framework for building autonomous agent teams that run experiments and improve their own strategies over time. every agent has one metric, one editable strategy, and a learning loop that ratchets forward based on measured results.

this is the [karpathy autoresearch pattern](https://github.com/karpathy/autoresearch) applied to agent teams -- except the agents optimize real workflows, not training runs.

## how it works

```
strategy.md → execute → measure → verdict → updated strategy.md
     ↑                                              |
     └──────────────────────────────────────────────┘
```

1. each agent reads its `strategy.md` before every run
2. produces output (content, research, analysis -- whatever the team does)
3. evaluates the output against its metric
4. logs the score to `results.tsv`
5. after enough samples, issues a verdict: **keep**, **discard**, or **inconclusive**
6. updates `strategy.md` with what it learned
7. next cycle starts with the evolved strategy

## quickstart

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma
pip install -e .
```

```bash
# scaffold an instance with a starter team
swarma init

# add your API key
echo "OPENROUTER_API_KEY=sk-or-..." > ~/.swarma/instances/default/.env

# run one cycle
swarma run --once

# or run continuously with scheduling + API server
swarma run --port 8000
```

## what you need

- python 3.11+
- an [openrouter](https://openrouter.ai/) API key
- that's it. no GPU, no postgres, no docker.

SQLite for state, markdown files on disk for knowledge. runs on a laptop or a $5 VPS.

## teams as config

a team is a folder with YAML configs. no code required.

```
teams/hook-lab/
├── team.yaml              # goal, flow, schedule, budget
├── program.md             # team context and constraints
└── agents/
    ├── researcher.yaml    # model, metric, instructions
    ├── copywriter.yaml
    └── judge.yaml
```

**team.yaml**
```yaml
name: Hook Lab
goal: find the message angles that make people stop scrolling.
flow: "researcher -> copywriter -> judge"
schedule: "0 8 * * 1-5"   # weekdays 8am
budget_monthly: 30.0
```

**agent config**
```yaml
id: copywriter
name: Hook Writer
model:
  model_id: qwen/qwen3.5-plus-02-15
  max_tokens: 800
  temperature: 0.7
instructions: |
  you write hooks. not posts, not articles -- just the opening
  that makes someone stop. write 3 variations:
  A: data-led. B: story-led. C: contrarian-led.
  max 2 sentences per hook. include at least one specific detail.
metric:
  name: hook_score
  target: 8.5
experiment_config:
  min_sample_size: 5
  auto_propose: true
```

## example squads

10 growth squads in [`examples/`](examples/), organized the way a real growth org structures teams -- by funnel stage, not by job title:

| Funnel Stage | Squad | Flow | What it optimizes |
|-------------|-------|------|-------------------|
| **Acquisition** | `hook-lab` | researcher -> copywriter -> judge | message testing (hooks, angles, CTAs) |
| | `channel-mix` | strategist -> [linkedin, twitter, email] | multi-channel distribution testing |
| | `cold-outbound` | researcher -> copywriter -> personalization-engine | outbound messaging sequences |
| | `seo-engine` | keyword-researcher -> content-writer -> seo-auditor | programmatic content + ranking |
| **Activation** | `activation-flow` | researcher -> sequence-designer -> evaluator | onboarding + first-value-moment |
| **Revenue** | `pricing-lab` | researcher -> analyst -> page-writer | monetization experiments |
| | `landing-lab` | researcher -> copywriter -> critic | conversion rate optimization |
| **Retention** | `retention-squad` | signal-monitor -> analyst -> outreach-writer | churn prevention + re-engagement |
| **Referral** | `referral-engine` | analyst -> loop-designer -> outreach-writer | viral loop optimization |
| **Intelligence** | `competitive-intel` | scanner -> analyst -> briefer | market monitoring + signals |

each squad includes a `program.md` with real growth frameworks, experiment patterns, and metric guidance -- not generic "produce quality content" instructions.

`swarma init --template hook-lab` scaffolds from any example.

## the experiment loop

every agent with a `metric` defined gets an automatic learning loop:

```
teams/hook-lab/results/copywriter/
├── strategy.md              # editable, evolves over time
├── results.tsv              # append-only score log
└── experiments/
    └── exp-001.md           # detailed experiment log
```

**strategy.md** evolves after each experiment:
```markdown
# Current Strategy

No strategy set yet. First experiment pending.

## Inconclusive (Exp 2)
Tried: story-led hooks vs data-led hooks -- no significant difference (avg=8.1 vs baseline=7.9)
> Next: test with longer sample size, results may be noise

## Validated (Exp 5)
contrarian opening + specific numbers in first line
> 23% improvement over baseline. keep this pattern.
```

the playbook grows. the team gets smarter. you don't touch anything.

## measurement

by default, agents self-evaluate using a cheap LLM call. this is good enough for prototyping and getting the loop running.

for production, wire in real signals:

```yaml
# agent config -- external metric callback
metric:
  name: linkedin_saves
  target: 50
  source: webhook    # accepts POST with {output_id, score}
```

```bash
# push real analytics back into the loop
curl -X POST http://localhost:8282/metrics \
  -d '{"agent": "writer", "output_id": "cycle-001", "score": 47}'
```

self-eval gets you iterating. external signals get you optimizing for what actually matters.

## flow DSL

define agent pipelines:

```yaml
# sequential
flow: "researcher -> writer"

# parallel
flow: "researcher -> [linkedin-writer, twitter-writer, visual-designer]"

# mixed
flow: "[research-analyst, intelligence-agent] -> growth-lead -> [linkedin-writer, twitter-writer] -> analytics"
```

parallel steps run via `asyncio.gather()`. output from step N becomes context for step N+1.

## multi-model routing

swarma routes to the right model for the task via [openrouter](https://openrouter.ai/). 300+ models, pay per token.

```yaml
# default routing table in config.yaml (override per agent)
models:
  routing:
    cheap: mistralai/mistral-nemo
    writing: qwen/qwen3.5-plus-02-15
    research: perplexity/sonar-pro
    reasoning: deepseek/deepseek-r1
    planning: anthropic/claude-sonnet-4-6
```

each agent can override the model in its config. cost is tracked per agent, per team, per day.

## shared knowledge + QMD

all teams share a knowledge store. agents write artifacts (markdown files with YAML frontmatter), indexed for search.

by default, knowledge uses SQLite metadata queries -- functional, zero setup. for production, connect [QMD](https://github.com/tobi/qmd) (by Tobi Lutke) to unlock full semantic search:

```yaml
# config.yaml
knowledge:
  qmd_endpoint: http://localhost:8181    # BM25 + vector + rerank
  collections: [research, content, experiments, briefs]
```

with QMD connected, agents get:
- **BM25 + vector + rerank** search across all artifacts from all teams
- **collection-scoped queries** (e.g. only search `research` artifacts)
- **cross-team knowledge transfer** -- team A's research automatically feeds team B's decisions

knowledge compounds across the entire instance. without QMD, it still works -- just with simpler metadata matching.

## runtime adapters

agents don't have to be LLM calls. swarma supports four runtimes:

| Runtime | Use Case | Config |
|---------|----------|--------|
| `llm` (default) | direct LLM via openrouter | model in agent yaml |
| `hermes` | [hermes agent](https://github.com/nousresearch/hermes-agent) with full tool access | endpoint + api_key |
| `http` | any HTTP endpoint that accepts JSON | endpoint + headers |
| `process` | local CLI command, stdin/stdout JSON | command + timeout |

## integration paths

swarma connects to your stack in two directions: agents **call out** via runtime adapters, and external systems **call in** via MCP or REST.

**hermes agent** -- the deepest integration. hermes agents get full tool access while swarma handles orchestration + learning. or flip it: connect hermes TO swarma's MCP server and trigger cycles from telegram/discord.

**claude code / claude desktop** -- add swarma as an MCP server. claude gets tools to run cycles, check experiments, read the playbook, approve plans.

```json
{
  "mcpServers": {
    "swarma": {
      "command": "swarma",
      "args": ["serve", "--mcp", "--instance", "my-swarm"]
    }
  }
}
```

**any MCP client** -- stdio or HTTP transport:

```bash
swarma serve --mcp                          # stdio
swarma serve --mcp --mcp-port 8383          # HTTP
```

**REST API** -- full control via HTTP. OpenAPI docs at `/docs`.

```bash
swarma serve --port 8282
```

## architecture

```
swarma/
├── core/           # agent, cycle runner, experiment loop, state, config, knowledge
├── flow/           # DSL parser + async executor
├── adapters/       # llm, hermes, http, process runtimes
├── tools/          # 3-layer registry (instance > team > agent)
├── experts/        # reasoning framework catalog + composer
├── server/         # FastAPI REST + MCP protocol server
└── cli/            # init, run, serve, status, team, tool commands
```

**state**: SQLite (outputs, experiments, cost_log, agent_runs, pending_plans, artifact_log, task_queue)

**knowledge**: markdown files on disk, indexed in SQLite, optionally searchable via QMD

**scheduling**: APScheduler for cron-based team cycles + event-driven heartbeat queue

## design choices

**self-eval as default.** agents score their own output using a cheap model. this is deliberately not perfect -- it gets the loop running with zero setup. production use should wire in external signals (analytics, human ratings, API metrics). the loop is the same either way; only the signal source changes.

**markdown on disk.** strategy files, knowledge artifacts, experiment logs -- all readable, editable, diffable, git-friendly. no proprietary format, no database lock-in. `cat strategy.md` tells you exactly what the agent knows.

**openrouter over direct provider APIs.** one API key, 300+ models, per-token billing. swap models by changing a string in YAML. no SDK changes, no credential rotation.

**YAML teams, not code.** defining a team shouldn't require Python. a non-coder with LLM assistance can create, modify, and understand team configs. the framework handles wiring.

**budget tracking, not enforcement.** cost is tracked per agent, per team, per day. `budget_monthly` in team config is currently informational -- it doesn't hard-stop cycles. enforcement is planned but not shipped. check `swarma status` to see spend.

**no context window management yet.** strategy files, knowledge retrieval, and expert lenses all compete for tokens in the prompt. for now, keep strategy files short and knowledge queries focused. tiered context loading (L0/L1/L2) is on the roadmap.

## what swarma is not

- **not a chatbot framework** -- agents run autonomously on schedules, not in response to user messages
- **not a memory engine** -- [honcho](https://github.com/plastic-labs/honcho) does memory. swarma does orchestration + learning.
- **not a prompt library** -- [agency-agents](https://github.com/msitarzewski/agency-agents) has 135 agent templates. swarma runs them and teaches them what works.
- **not a simulation engine** -- [mirofish](https://github.com/666ghj/MiroFish) simulates populations. swarma optimizes real workflows.

## roadmap

- [x] growth squad templates (10 squads mapped to AARRR funnel stages)
- [ ] dashboard UI (experiment viewer, playbook, agent detail)
- [ ] external metric ingestion (webhooks, analytics callbacks)
- [ ] hermes agent integration package
- [ ] tiered context loading (L0/L1/L2, inspired by [openviking](https://github.com/volcengine/OpenViking))
- [ ] `pip install swarma` on PyPI

## contributing

swarma is early. if you're interested in agent learning loops, growth experiment frameworks, or multi-model orchestration, open an issue or PR.

## license

MIT
