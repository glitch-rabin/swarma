# Quickstart: Your First Swarm in 5 Minutes

## Install

```bash
pip install swarma
```

Requires Python 3.11+.

## Initialize

```bash
swarma init
```

This prompts for your OpenRouter API key and creates an instance at `~/.swarma/instances/default/` with:

```
~/.swarma/instances/default/
  config.yaml     # model routing, instance settings
  .env            # OPENROUTER_API_KEY
  teams/
    starter/      # a minimal 2-agent team for testing
      team.yaml
      agents/
        thinker.yaml
        writer.yaml
  knowledge/      # artifact storage (auto-populated)
  logs/
```

The starter team is a simple `thinker -> writer` flow using Mistral Nemo (cheap). It exists to confirm the pipeline works.

To skip prompts and use defaults:

```bash
swarma init --yes
```

You can set the API key after init:

```bash
echo "OPENROUTER_API_KEY=sk-or-..." >> ~/.swarma/instances/default/.env
```

Get a key at [openrouter.ai/keys](https://openrouter.ai/keys).

## Run Your First Cycle

```bash
swarma cycle starter --topic "why do startups fail?"
```

This runs one cycle of the starter team: the thinker generates an observation, the writer turns it into a social post. You'll see a table with each agent's output, model used, and cost.

Expected output:

```
Running cycle: starter
  flow: thinker -> writer
  agents: ['thinker', 'writer']

          Cycle: starter
  Agent    Model          Cost       Output Preview
  thinker  mistral-nemo   $0.000012  Most startups don't fail because of the idea...
  writer   mistral-nemo   $0.000018  everyone's building features. nobody's buildi...

  duration: 3.2s | total cost: $0.000030 | agents: 2
```

## Copy a Real Squad

The starter team is a smoke test. For real work, use a pre-built squad. Copy `hook-lab` (a hook testing lab with researcher, copywriter, and judge):

```bash
cp -r "$(python -c "import swarma; print(swarma.__path__[0])")/examples/hook-lab" \
  ~/.swarma/instances/default/teams/hook-lab
```

Or if you cloned the repo:

```bash
cp -r examples/hook-lab ~/.swarma/instances/default/teams/hook-lab
```

## Run the Squad

```bash
swarma cycle hook-lab --topic "AI agents are overhyped"
```

This runs the full `researcher -> copywriter -> judge` flow:

1. **Researcher** finds a specific angle with proof points and emotional levers
2. **Copywriter** writes 3 hook variations (data-led, story-led, contrarian-led)
3. **Judge** scores each variation on pattern interrupt, specificity, curiosity gap, credibility, and save-worthiness

Each agent reads its `strategy.md` before executing. After scoring, the strategy file evolves. This is the GROWS Loop: Generate hypothesis, Run experiment, Observe signal, Weigh verdict, Stack playbook.

## Feed Real Metrics

LLM self-eval is a proxy. Feed back real-world data to close the loop:

```bash
swarma metric log hook-lab copywriter 4.2 --metric ctr_pct
```

This logs a CTR of 4.2% for the copywriter agent. If there's an active experiment, the metric auto-attaches to it.

Attach to a specific experiment:

```bash
swarma metric log hook-lab copywriter 5.1 --metric ctr_pct --exp 3
```

Add a note:

```bash
swarma metric log hook-lab copywriter 127 --metric impressions --note "from linkedin analytics"
```

Bulk import from CSV:

```bash
swarma metric import hook-lab metrics.csv
```

CSV format: `agent,value,metric_name,note`

```csv
copywriter,4.2,ctr_pct,week 1
copywriter,5.1,ctr_pct,week 2
researcher,7.8,relevance_score,
```

View logged metrics:

```bash
swarma metric show hook-lab
```

## Check Status

```bash
swarma status
```

Shows all teams, recent runs, costs (today + this month), pending plans, and queue stats.

## Start the API Server

```bash
swarma serve --port 8282
```

API docs at `http://localhost:8282/docs`.

## Run Continuously

For scheduled execution (teams with cron schedules run automatically):

```bash
swarma run
```

This starts the engine with APScheduler. Teams with a `schedule` field in `team.yaml` (e.g., `"0 8 * * 1-5"` for weekdays at 8am) run automatically. Teams without a schedule are manual-trigger only.

Run with the API server:

```bash
swarma run --port 8282
```

Run a single team:

```bash
swarma run --team hook-lab
```

## Generate a Team from a Goal

Skip manual configuration entirely. Describe what you want to improve:

```bash
swarma team create growth-lab \
  --from-goal "optimize landing page conversion for our B2B SaaS" \
  --context "developer tools company, 500 free users, 2% conversion to paid" \
  --budget 30
```

The generator designs agents, picks models, writes instructions, creates a `program.md` with experiment patterns, and proposes the first experiment. Review and run:

```bash
swarma team show growth-lab
swarma cycle growth-lab
```

## What Happens Each Cycle

Each cycle runs the GROWS Loop:

1. **Generate**: Agent reads `strategy.md` + knowledge context + team program
2. **Run**: Produces output (hook, copy, analysis, etc.)
3. **Observe**: Output gets scored (self-eval via cheap LLM, or external metric)
4. **Weigh**: If enough samples collected, issues verdict (keep / discard / inconclusive)
5. **Stack**: Validated patterns get appended to `strategy.md` and saved to the cross-team playbook

The strategy file is the learning mechanism. It starts with seed knowledge and grows with every experiment that passes the 20% improvement threshold.

## Next Steps

- [Pre-built Squad Templates](squads.md) -- 18 squads covering the full AARRR funnel
- [API Reference](api.md) -- all endpoints, curl examples
- [Running with Hermes](hermes.md) -- operator layer, Telegram/Slack, MCP integration
