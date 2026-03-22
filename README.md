# swarma

the experiment loop for AI agent teams.

**[swarma.dev](https://swarma.dev)**

---

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

your agents run tasks. swarma makes them run A/B tests instead.

define a hypothesis and a metric. swarma handles the loop: run experiments, score results, issue verdicts, update strategies. after enough cycles, you have a validated playbook of what actually works -- not what you assumed would work.

```
strategy.md → execute → measure → verdict → updated strategy.md
     ↑                                              |
     └──────────────────────────────────────────────┘
```

this is the [karpathy autoresearch pattern](https://github.com/karpathy/autoresearch) applied to agent teams -- except the agents optimize real workflows, not training runs.

## why this exists

every growth team at Uber, Spotify, Facebook, Airbnb runs the same loop: hypothesize, test, measure, learn, repeat. the ones that win aren't smarter -- they just run more experiments and actually listen to the data. the playbook that emerges after thousands of cycles is the real asset. not the team, not the tools, not the clever ideas. the compounded learnings.

after 10 years building and scaling growth teams, the pattern is obvious: most teams ship what feels right instead of testing what works. they skip the measurement step. they don't close the loop. the strategy never evolves because nobody writes down what they learned.

AI agent teams have the same problem, except worse. agents don't remember what worked last week. they don't compare approaches. they don't build on previous wins. every run starts from zero.

swarma is the system I wished existed -- the experiment infrastructure that growth teams at scale take for granted, packaged so any agent team can use it. same loop, same rigor, same compounding. just without the 50-person team and the 6-month runway to build it internally.

## quickstart

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma
pip install -e .
```

```bash
swarma init                    # creates instance + starter team
swarma cycle starter           # run one cycle, see it work
swarma status                  # costs, runs, experiments
```

python 3.11+ and an [openrouter](https://openrouter.ai/) API key. no GPU, no postgres, no docker. runs on a laptop or a $5 VPS.

## how the loop works

1. agent reads its `strategy.md` before every run
2. produces output (content, research, analysis -- whatever the team does)
3. a cheap LLM scores the output against the agent's metric (1-10 scale, forced decimals)
4. score + reasoning logged to `results.tsv`
5. after `min_sample_size` cycles (default 3-5), verdict is issued automatically
6. `strategy.md` updated with what was learned
7. next cycle uses the evolved strategy

**scoring**: each output gets evaluated by a separate LLM call using the cheapest model in your routing table. the evaluator sees the output, the current strategy, the last 5 scores, and the metric definition. returns a precise score (7.3, not 7) plus reasoning and a strategy suggestion.

**verdicts**: after enough samples, swarma compares the experiment average against baseline. >20% improvement = **keep** (pattern validated, strategy updated). >20% decline = **discard** (reverted). in between = **inconclusive** (logged, try again with more data).

after a few experiments, your `strategy.md` looks like this:

```markdown
## Validated (Exp 5)
contrarian opening + specific numbers in first line
> 23% improvement over baseline. keep this pattern.

## Inconclusive (Exp 2)
story-led hooks vs data-led hooks -- no significant difference (avg=8.1 vs baseline=7.9)
> next: increase sample size, results may be noise
```

the playbook grows. the team gets smarter. you don't touch anything.

## teams as config

a team is a folder. no code required.

```
teams/my-squad/
├── team.yaml          # goal, flow, schedule, budget
├── program.md         # team context and constraints
└── agents/
    ├── researcher.yaml
    └── writer.yaml
```

```yaml
# team.yaml
name: my-squad
goal: find what works.
flow: "researcher -> writer"
schedule: "0 8 * * 1-5"
```

```yaml
# agents/writer.yaml
id: writer
name: Writer
instructions: |
  turn research into a post. max 200 words.
  hook in the first line. practitioner voice.
metric:
  name: content_quality
  target: 8.0
experiment_config:
  min_sample_size: 5
  auto_propose: true
```

models, tools, and expert lenses are configured in `config.yaml`. agents inherit defaults or override per-agent.

flow DSL supports sequential (`a -> b`), parallel (`a -> [b, c, d]`), and mixed pipelines.

## 10 example squads

ready-to-use squads in [`examples/`](examples/). copy one into your instance and run it:

```bash
cp -r examples/hook-lab ~/.swarma/instances/default/teams/
swarma cycle hook-lab
```

| squad | what it tests |
|-------|--------------|
| `hook-lab` | opening lines -- what stops the scroll |
| `format-wars` | carousel vs text vs thread vs image |
| `voice-finder` | tone variations until engagement peaks |
| `cta-optimizer` | call-to-action placement and phrasing |
| `topic-radar` | which subjects your audience actually cares about |
| `timing-lab` | posting time and frequency experiments |
| `repurpose-engine` | how to recycle top performers across platforms |
| `thread-lab` | thread structure and hook patterns |
| `newsletter-lab` | subject lines, send times, format |
| `defi-alpha` | research depth vs speed for crypto content |

each includes a `program.md` with real experiment patterns and metric guidance.

## integrations

### hermes agent

swarma exposes an MCP server. connect it to [hermes](https://github.com/nousresearch/hermes-agent) and your agent gets a dedicated experiment team that learns while it sleeps.

```yaml
# hermes config.yaml
mcp_servers:
  swarma:
    transport: stdio
    command: swarma
    args: ["serve", "--mcp"]
```

hermes stays clean -- sets direction, approves plans, asks "what did we learn?" swarma does the messy work.

### claude code / claude desktop

```json
{
  "mcpServers": {
    "swarma": {
      "command": "swarma",
      "args": ["serve", "--mcp"]
    }
  }
}
```

### REST API

```bash
swarma serve --port 8282        # 30+ endpoints, OpenAPI docs at /docs
```

### any MCP client

```bash
swarma serve --mcp              # stdio
swarma serve --mcp --mcp-port 8383   # HTTP
```

**note**: when running as MCP subprocess, pass `OPENROUTER_API_KEY` in your MCP config's `env` block -- the instance `.env` is not inherited by subprocesses.

## knowledge layer (QMD)

agents learn individually via strategy.md. to learn *across* teams, add [QMD](https://github.com/glitch-rabin/qmd) -- a search engine that indexes all agent outputs. BM25 + vector + rerank. no GPU required.

```bash
pip install qmd
qmd init
qmd serve                          # http://localhost:8181
```

```yaml
# config.yaml
knowledge:
  engine: qmd
  qmd_endpoint: http://localhost:8181/mcp
```

every agent output gets indexed automatically. agents search what other agents learned. the experiment loop gets shared memory.

without QMD, swarma uses local SQLite (metadata only). with QMD, full semantic search across all outputs, strategies, and results.

## what swarma is not

- **not memory** -- [honcho](https://github.com/plastic-labs/honcho) does memory. swarma does learning loops.
- **not automation** -- n8n/make do workflows. swarma runs experiments.
- **not a prompt library** -- [agency-agents](https://github.com/msitarzewski/agency-agents) has 135 templates. swarma teaches them what works.
- **not orchestration** -- crewai/autogen run pipelines. swarma adds the feedback loop that makes pipelines improve.

## roadmap

- [ ] expert reasoning lenses (composable thinking frameworks)
- [ ] dashboard UI (experiment viewer, playbook, strategy evolution)
- [ ] external metric ingestion (webhooks, analytics callbacks)
- [ ] squad marketplace
- [ ] `pip install swarma` on PyPI

## contributing

swarma is early. if you're interested in experiment loops for agents, open an issue or PR.

## license

MIT
