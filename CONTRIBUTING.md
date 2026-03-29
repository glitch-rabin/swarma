# Contributing to swarma

swarma is early and moving fast. if you're interested in experiment loops for agents, you're in the right place.

## getting started

```bash
# fork the repo on GitHub, then:
git clone https://github.com/YOUR-USERNAME/swarma.git
cd swarma
pip install -e ".[dev]"
```

this gives you an editable install with dev dependencies (pytest, ruff, pytest-asyncio).

set up your environment:

```bash
cp .env.template .env
# edit .env and add your OPENROUTER_API_KEY
```

verify the install:

```bash
swarma init --yes
swarma cycle starter --topic "test run"
```

if you see agent outputs and costs, you're good.

## project structure

```
swarma/
├── core/           # GROWS loop engine -- cycle runner, experiments, verdicts, state
├── cli/            # command-line interface (Typer) -- all `swarma *` commands
├── server/         # FastAPI app (30+ endpoints) + MCP server (24 tools)
├── adapters/       # LLM, HTTP, subprocess, Hermes plugin interfaces
├── flow/           # flow DSL parser + executor (sequential, parallel, mixed)
├── tools/          # tool registry + definitions for agents
├── experts/        # expert reasoning lens infrastructure
├── templates/      # jinja2 prompt templates
└── examples/       # bundled squad templates (18 squads)

examples/           # squad templates (also bundled into package)
docs/               # quickstart, API reference, hermes integration, squad docs
```

**key modules:**

| file | what it does |
|------|-------------|
| `core/cycle.py` | CycleRunner + Engine -- the GROWS loop lives here |
| `core/experiment.py` | ExperimentEngine -- verdict logic (keep/discard/inconclusive) |
| `core/generator.py` | team generator (`--from-goal`) |
| `core/state.py` | StateDB -- SQLite persistence |
| `core/router.py` | ModelRouter -- OpenRouter model selection |
| `server/mcp.py` | MCP server for Hermes / Claude Code |
| `server/app.py` | REST API (FastAPI) |
| `flow/parser.py` | flow DSL (`a -> b`, `a -> [b, c, d]`) |

## what to work on

**high impact, easy to start:**

- new squad templates (see guidelines below)
- documentation improvements
- bug fixes

**medium effort:**

- new CLI commands
- adapter improvements
- flow DSL extensions

**big features (open an issue first):**

- new experiment strategies
- alternative model routers
- dashboard UI

check the [roadmap in README.md](README.md#roadmap) for what's planned.

## making changes

### code changes

1. create a branch: `git checkout -b fix/your-fix` or `git checkout -b feat/your-feature`
2. make your changes
3. run tests: `pytest`
4. run linting: `ruff check .`
5. commit with a clear message
6. push and open a PR

### squad templates

this is the easiest way to contribute. if you built a squad that works, we want it.

create a folder in `examples/`:

```
examples/your-squad/
├── team.yaml          # team config
├── program.md         # mission + experiment patterns
└── agents/
    ├── agent-1.yaml   # agent config
    ├── agent-2.yaml
    └── strategy.md    # seed knowledge
```

**team.yaml** must include:

```yaml
name: your-squad
goal: what this team optimizes for
flow: "agent-1 -> agent-2"          # or parallel: "agent-1 -> [agent-2, agent-3]"
schedule: "0 8 * * 1-5"             # optional cron
```

**each agent.yaml** must include:

```yaml
id: agent-1
name: Agent One
instructions: |
  what this agent does. be specific.
metric:
  name: your_metric
  target: 8.0
experiment_config:
  min_sample_size: 5
  auto_propose: true
```

**strategy.md** must include real seed knowledge -- validated patterns, anti-patterns, and hypotheses to test. not placeholder text. this is what makes swarma squads useful on day one.

**program.md** should describe the squad's mission, what experiments it runs, and any constraints.

**before submitting**: run at least 3 cycles and confirm the experiment loop works:

```bash
cp -r examples/your-squad ~/.swarma/instances/default/teams/
swarma cycle your-squad
swarma cycle your-squad
swarma cycle your-squad
```

### documentation

docs live in `docs/`. the main files:

- `quickstart.md` -- getting started guide
- `api.md` -- REST API reference
- `hermes.md` -- Hermes integration
- `squads.md` -- squad template reference

keep the same voice: lowercase, direct, no fluff. show don't tell. code examples over explanations.

## code style

- **python 3.11+** -- use modern syntax (match statements, type unions with `|`, etc.)
- **ruff** for linting -- 100 character line length, target python 3.11
- **keep it simple** -- no over-engineering, no premature abstractions
- **no new heavy dependencies** without discussion

run before committing:

```bash
ruff check .
ruff format .
```

## testing

```bash
pytest                    # run all tests
pytest -x                 # stop on first failure
pytest -k "test_cycle"    # run specific tests
```

the integration test (`test_loop.py`) runs 5 cycles across 2 teams and validates the full GROWS loop. requires a valid `OPENROUTER_API_KEY`.

if you're adding a feature, add tests. if you're fixing a bug, add a test that reproduces it.

## pull requests

- **open an issue first** for anything non-trivial. describe what you want to change and why.
- **one PR per change** -- don't bundle unrelated fixes.
- **clear description** -- what changed, why, and how to test it.
- **keep PRs small** -- easier to review, faster to merge.

### PR title format

```
fix: description of the fix
feat: description of the feature
docs: description of the doc change
squad: new squad-name template
```

## what we merge

- bug fixes with tests
- squad templates with real seed knowledge and 3+ successful cycles
- documentation improvements
- features that are on the roadmap or discussed in an issue

## what we don't merge

- features nobody asked for (open an issue first)
- breaking changes without discussion
- code that adds heavy dependencies without justification
- anything that phones home, adds telemetry, or sends data anywhere
- PRs that don't pass linting or tests
- squad templates with placeholder/generic strategy files

## questions?

open an issue or start a discussion on GitHub.
