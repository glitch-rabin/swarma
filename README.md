# swarma

growth loops, automated.

**[swarma.dev](https://swarma.dev)**

---

<p align="center">
  <img src="brand/scenes/v2/05-van-studio.png" alt="swarma — growth loops, automated" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.2.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11+-green" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License">
  <img src="https://img.shields.io/pypi/v/swarma" alt="PyPI">
</p>

an agent without a team is just a prompt with no context. nobody hires a writer with no research team, no analytics, no strategy, no feedback loop.

swarma builds agent **teams** that run growth experiments, score results, issue verdicts, and evolve their own strategy. after enough cycles, you have a validated playbook of what actually works. self-hosted. runs on a laptop or a VPS.

one folder = one team. one cycle = one experiment. the playbook writes itself.

## swarma is right for you if

- you run growth experiments (hooks, landing pages, outreach, pricing, activation) and want to run 50x more of them
- you want agent teams that **learn and improve** through A/B testing, not just execute once
- you want a validated playbook of what works for your specific audience, not generic advice
- you care about self-hosted, no vendor lock-in, and owning your data
- you want swarms that get smarter every cycle, not pipelines that run once and forget

## quickstart

```bash
pip install swarma
swarma init
swarma cycle starter --topic "why do startups fail?"
```

three commands. python 3.11+ and an [OpenRouter](https://openrouter.ai/) API key. no GPU, no postgres, no docker.

or from source:

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma && pip install -e .
```

### MCP integration (Claude Code / Claude Desktop)

after installing, add to your MCP config (`.mcp.json`):

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

## the GROWS loop

every cycle follows GROWS -- five steps, no exceptions:

```
  Generate       Run         Observe       Weigh        Stack
 hypothesis --> experiment --> signal --> verdict --> playbook
     ^                                                  |
     └──────────────────────────────────────────────────┘
```

| Step | What happens |
|------|-------------|
| **G -- Generate** | Agent reads its `strategy.md`, proposes a hypothesis. "contrarian opening lines will outperform data-led hooks on saves." |
| **R -- Run** | Agent executes with the hypothesis active. Produces output -- research, copy, analysis, whatever the team does. |
| **O -- Observe** | A separate LLM scores the output against the agent's target metric (1-10 scale, forced decimals). Score + reasoning logged to `results.tsv`. |
| **W -- Weigh** | After `min_sample_size` cycles (default 5), swarma compares experiment average against baseline. >20% up = **keep**. >20% down = **discard**. In between = **inconclusive**. |
| **S -- Stack** | Validated patterns get written back to `strategy.md` and pushed to the shared playbook. Next cycle generates a new hypothesis from the evolved strategy. |

this is the same loop every growth team at Uber, Spotify, and Airbnb runs. swarma removes the human bandwidth bottleneck. a swarm runs 50 experiments while a human team runs 2.

## without swarma vs with swarma

| | Without | With swarma |
|---|---------|------------|
| **Experiments per week** | 2-5 (limited by human bandwidth) | 50+ (limited by API budget) |
| **Knowledge sharing** | Lives in Slack threads, dies there | Every result logged to `results.tsv`, strategies evolve per team |
| **Strategy evolution** | Manual review meetings, quarterly | Automatic after every experiment cycle |
| **Learning from failure** | "We tried that, it didn't work" (no record) | Logged, analyzed, anti-patterns tracked |
| **Cross-team learning** | Team A doesn't know what Team B learned | Optional shared playbook via QMD (cross-team knowledge) |
| **Starting point** | Blank page or generic templates | Pre-seeded strategies from real growth knowledge |

## generate a team from a goal

don't configure agents by hand. describe what you want and swarma builds the team.

```bash
swarma team create my-growth --from-goal "improve landing page conversion rate"
```

this calls an LLM to design a team with the right agents, flow, models, and a first experiment hypothesis. the generated team comes with:

- `team.yaml` -- goal, flow, budget
- `agents/*.yaml` -- individual agent configs with specific instructions
- `program.md` -- experiment patterns and constraints
- a first experiment ready to run

add business context for better results:

```bash
swarma team create growth-lab \
  --from-goal "optimize our signup funnel" \
  --context "B2B SaaS, 500 free users, 2% conversion to paid" \
  --budget 50
```

## teams as config

a team is a folder. no code required.

```
teams/my-squad/
├── team.yaml          # goal, flow, schedule, budget
├── program.md         # team context and constraints
└── agents/
    ├── researcher.yaml
    ├── writer.yaml
    └── strategy.md    # pre-seeded growth knowledge (evolves automatically)
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

models are configured per-agent in their YAML files. `swarma init` creates a `config.yaml` at `~/.swarma/instances/default/` with model routing defaults.

flow DSL supports sequential (`a -> b`), parallel (`a -> [b, c, d]`), and mixed pipelines.

## how the loop works (detailed)

1. agent reads its `strategy.md` before every run
2. produces output (research, copy, analysis -- whatever the team does)
3. a cheap LLM scores the output against the agent's metric (1-10 scale, forced decimals)
4. score + reasoning logged to `results.tsv`
5. after `min_sample_size` cycles (default 5), verdict is issued automatically
6. `strategy.md` updated with what was learned
7. next cycle uses the evolved strategy

**scoring**: each output gets evaluated by a separate LLM call using the cheapest model in your routing table. the evaluator sees the output, the current strategy, the last 5 scores, and the metric definition. returns a precise score (7.3, not 7) plus reasoning and a strategy suggestion.

**verdicts**: after enough samples, swarma compares the experiment average against baseline. >20% improvement = **keep** (pattern validated, strategy updated). >20% decline = **discard** (reverted). in between = **inconclusive** (logged, try again with more data).

after a few experiments, your `strategy.md` evolves from seed knowledge into validated patterns:

```markdown
## Validated (Exp 5)
contrarian opening + specific numbers in first line
> 23% improvement over baseline. keep this pattern.

## Inconclusive (Exp 2)
story-led hooks vs data-led hooks -- no significant difference (avg=8.1 vs baseline=7.9)
> next: increase sample size, results may be noise
```

## feed real metrics back

LLM self-eval is a starting proxy. for production, feed back real-world signals:

```bash
# log a single metric
swarma metric log hook-lab copywriter 4.2 --metric ctr_pct

# attach to a specific experiment
swarma metric log hook-lab copywriter 127 --metric impressions --exp 3

# bulk import from CSV
swarma metric import hook-lab metrics.csv

# view logged metrics
swarma metric show hook-lab
```

CSV format: `agent,value,metric_name,note`

metrics auto-attach to the agent's active experiment. the experiment loop uses external metrics alongside LLM scores when both are available.

## pre-seeded strategies

agents don't start from zero. each squad includes a `strategy.md` seeded with real growth knowledge -- validated patterns, anti-patterns, and hypotheses to test. the GROWS loop refines these over time.

example from the hook-lab strategy:

```markdown
### Validated Patterns

**Specificity wins**
- Hooks with specific numbers outperform vague claims by 2-3x on saves
- "47% of startups" > "most startups"

**Loss framing > gain framing**
- "You're losing $X/month" outperforms "You could save $X/month" on CTR
- Exception: aspirational audiences respond better to gain framing

### Patterns to Test
- [ ] First-person confession vs third-person case study
- [ ] Time-anchored ("In 2024...") vs timeless hooks
```

## 18 squad templates

ready-to-use squads in [`examples/`](examples/), each with pre-seeded strategies:

```bash
cp -r examples/hook-lab ~/.swarma/instances/default/teams/
swarma cycle hook-lab
```

**core growth squads:**

| squad | AARRR stage | what it tests | agents |
|-------|------------|--------------|--------|
| `hook-lab` | acquisition | opening lines -- what stops the scroll | 3 |
| `landing-lab` | acquisition | landing page copy and structure | 3 |
| `seo-engine` | acquisition | search presence and content ranking | 3 |
| `cold-outbound` | acquisition | outreach messaging and sequences | 3 |
| `channel-mix` | acquisition | multi-platform content strategy | 3 |
| `activation-flow` | activation | signup-to-value onboarding flows | 3 |
| `pricing-lab` | revenue | pricing presentation and packaging | 3 |
| `retention-squad` | retention | churn signals and win-back patterns | 3 |
| `referral-engine` | referral | viral loops and invite mechanics | 3 |
| `competitive-intel` | -- | market monitoring and positioning | 3 |

**2026 growth ops squads:**

| squad | what it tests | agents |
|-------|--------------|--------|
| `faceless-factory` | automated short-form video pipeline | 3 |
| `ad-creative-lab` | performance creative testing at scale | 3 |
| `ugc-factory` | user-generated content simulation | 3 |
| `programmatic-seo` | automated SEO content at scale | 3 |
| `newsletter-engine` | newsletter growth + retention | 3 |
| `acquisition-squad` | paid + organic acquisition loops | 3 |
| `community-engine` | community-led growth automation | 3 |
| `agentic-storefront` | AI-powered commerce optimization | 3 |

each includes a `program.md` with experiment patterns and a `strategy.md` with real growth knowledge as starting baseline.

## what swarma is not

| swarma is not... | Use this instead | The difference |
|-------------------|-----------------|----------------|
| **memory** | [honcho](https://github.com/plastic-labs/honcho) | swarma doesn't remember conversations. it runs experiment loops and builds playbooks. |
| **workflow automation** | n8n, Make, Zapier | those connect apps. swarma runs hypotheses through agent teams and learns from results. |
| **a prompt library** | [agency-agents](https://github.com/msitarzewski/agency-agents) (135 templates) | templates are a starting point. swarma teaches agents what works through feedback loops. templates go in, playbooks come out. |
| **agent orchestration** | CrewAI, AutoGen, LangGraph | those run pipelines. swarma adds the GROWS loop that makes pipelines *improve*. orchestration is step 1. learning is the whole game. |
| **a hosted service** | -- | swarma is self-hosted. your data stays on your machine. no accounts, no telemetry, no vendor lock-in. |

## works with

swarma is the engine. connect it to an operator for the full experience.

### Hermes

[Hermes](https://github.com/nousresearch/hermes-agent) by NousResearch is the operator layer swarma is designed for. Hermes has terminal access -- it can run `swarma cycle`, `swarma team create`, and read results directly. no MCP required.

swarma is the machine. Hermes is the executive. together they're the system from [the original article](https://x.com/glitch_).

### QMD cross-team knowledge

by default, each team learns individually via its own `strategy.md`. to learn **across** teams, wire in [QMD](https://github.com/tobi/qmd) -- a local knowledge engine by Tobi Lutke. BM25 + vector + rerank. runs on your machine, no GPU.

```yaml
# config.yaml
knowledge:
  engine: qmd
  qmd_endpoint: http://localhost:8181/mcp
```

with QMD: team A discovers loss framing beats gain framing, team B sees that pattern in its next cycle. without QMD: teams still learn individually. most users don't need this until running 3+ teams.

### REST API

```bash
swarma serve --port 8282        # 30+ endpoints, OpenAPI docs at /docs
```

## FAQ

**do I need Hermes to use swarma?**

no. swarma works standalone via CLI. Hermes adds the operator layer -- Telegram/Slack control, approval flows, scheduled cycles. it's how you get the full experience, but swarma runs experiments on its own.

**do I need QMD?**

no. QMD adds cross-team knowledge sharing. without it, each team learns individually via its own `strategy.md`. add QMD when you're running multiple teams and want them to learn from each other.

**what models does it use?**

any model on [OpenRouter](https://openrouter.ai/). swarma uses a routing table that maps task types (generation, evaluation, routing) to models. you configure this in the instance `config.yaml` created by `swarma init`, and can override per-agent.

**is this like CrewAI / AutoGen / LangGraph?**

those are orchestration frameworks -- they run agent pipelines. swarma adds the experiment loop on top. orchestration is "agent A passes output to agent B." swarma is "agent A passes output to agent B, the output gets scored, and the strategy evolves based on what works." the GROWS loop is the difference.

**can I use this for things other than growth marketing?**

the engine doesn't care what the team does. it cares about agents, metrics, and experiments. if you can define a north star metric, swarma can run experiments toward it.

**is my data sent anywhere?**

your prompts and outputs go to OpenRouter (which routes to the model provider). everything else -- strategies, experiment logs, playbooks, knowledge -- stays on your machine. no telemetry, no analytics, no phone-home.

## standing on

swarma exists because of three ideas from three people:

- **[autoresearch](https://github.com/karpathy/autoresearch)** by Andrej Karpathy -- automated research loops where agents iteratively refine their approach. swarma applies this to growth experiments instead of research papers.
- **[QMD](https://github.com/tobi/qmd)** by Tobi Lutke ([@tobi](https://x.com/tobi)) -- shared knowledge across agents. the insight that agents working on different problems should learn from each other.
- **[Hermes](https://github.com/nousresearch/hermes-agent)** by NousResearch ([@NousResearch](https://x.com/NousResearch)) -- the operator layer. an agent that directs teams of specialist agents through tool use. swarma is designed as infrastructure that Hermes operates.

## roadmap

**shipped:**

- [x] GROWS experiment loop (generate -> run -> observe -> weigh -> stack)
- [x] team generator (`swarma team create --from-goal`)
- [x] 18 squad templates covering full AARRR funnel + 2026 growth ops
- [x] pre-seeded strategy files with real growth knowledge
- [x] external metric ingestion (`swarma metric log/import/show`)
- [x] QMD cross-team wiring (verdict -> playbook -> shared knowledge)
- [x] MCP server (16 tools) for Hermes / Claude Code / any client
- [x] `pip install swarma` on PyPI (v0.2.0)

**next:**

- [ ] dashboard UI (experiment viewer, playbook, strategy evolution)
- [ ] setup wizard (guided onboarding for first-time users)
- [ ] expert reasoning lenses (bundled thinking frameworks)
- [ ] Hermes skill package
- [ ] squad marketplace (share and discover validated teams + playbooks)
- [ ] webhook metric ingestion (real-time analytics callbacks)
- [ ] observation-mode experiments (real-world signal primary, LLM eval secondary)

## contributing

swarma is early and moving fast. see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

short version: open an issue first for anything non-trivial. PRs welcome for bug fixes, new squad templates, and documentation. if you're building a squad that works, we want it in `examples/`.

## star history

<a href="https://www.star-history.com/?repos=glitch-rabin%2Fswarma&type=date&logscale=&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=glitch-rabin/swarma&type=date&theme=dark&logscale&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=glitch-rabin/swarma&type=date&logscale&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/image?repos=glitch-rabin/swarma&type=date&logscale&legend=top-left" />
 </picture>
</a>

## license

MIT
