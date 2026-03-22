# swarma

the experiment loop for AI agent teams.

---

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

your agents run tasks. do they learn from them?

swarma adds a persistent learning loop to any AI agent. each agent gets one metric, one editable strategy file, and a feedback cycle that evolves based on measured results. the playbook writes itself.

not memory. not automation. not orchestration. just:

```
strategy.md → execute → measure → verdict → updated strategy.md
     ↑                                              |
     └──────────────────────────────────────────────┘
```

this is the [karpathy autoresearch pattern](https://github.com/karpathy/autoresearch) applied to agent teams -- except the agents optimize real workflows, not training runs.

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

you need python 3.11+ and an [openrouter](https://openrouter.ai/) API key. that's it. no GPU, no postgres, no docker. runs on a laptop or a $5 VPS.

## how the loop works

1. agent reads its `strategy.md` before every run
2. produces output (content, research, analysis -- whatever the team does)
3. scores the output against its metric
4. logs to `results.tsv`
5. after enough samples, issues a verdict: **keep**, **discard**, or **inconclusive**
6. updates `strategy.md` with what it learned
7. next cycle uses the evolved strategy

**strategy.md** after a few experiments:
```markdown
## Inconclusive (Exp 2)
story-led hooks vs data-led hooks -- no significant difference (avg=8.1 vs baseline=7.9)
> next: increase sample size, results may be noise

## Validated (Exp 5)
contrarian opening + specific numbers in first line
> 23% improvement over baseline. keep this pattern.
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

## works with hermes

swarma exposes an MCP server. connect it to [hermes agent](https://github.com/nousresearch/hermes-agent) and your hermes gets a dedicated experiment team that learns while it sleeps.

```yaml
# hermes config.yaml
mcp_servers:
  swarma:
    transport: stdio
    command: swarma
    args: ["serve", "--mcp"]
```

hermes stays clean -- sets direction, approves plans, asks "what did we learn?" swarma does the messy work: running experiments, tracking scores, evolving strategies. no context window pollution.

## works with anything

**claude code / claude desktop:**
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

**REST API:**
```bash
swarma serve --port 8282        # 30+ endpoints, OpenAPI docs at /docs
```

**any MCP client:**
```bash
swarma serve --mcp              # stdio
swarma serve --mcp --mcp-port 8383   # HTTP
```

## example squads

10 ready-to-use squads in [`examples/`](examples/). copy one into your instance and run it:

```bash
cp -r examples/hook-lab ~/.swarma/instances/default/teams/
swarma cycle hook-lab
```

each squad includes a `program.md` with real experiment patterns and metric guidance.

## what swarma is not

- **not memory** -- [honcho](https://github.com/plastic-labs/honcho) does memory. swarma does learning loops.
- **not automation** -- n8n/make do workflows. swarma runs experiments.
- **not a prompt library** -- [agency-agents](https://github.com/msitarzewski/agency-agents) has 135 templates. swarma teaches them what works.
- **not orchestration** -- crewai/autogen run pipelines. swarma adds the feedback loop that makes pipelines improve.

## coming soon

- expert reasoning lenses (30 composable thinking frameworks)
- dashboard UI (experiment viewer, playbook, strategy evolution)
- external metric ingestion (webhooks, analytics callbacks)
- squad marketplace
- `pip install swarma` on PyPI

## contributing

swarma is early. if you're interested in experiment loops for agents, open an issue or PR.

## license

MIT
