# API Reference

## Starting the Server

```bash
swarma serve --port 8282
```

API docs (Swagger UI) at `http://localhost:8282/docs`.

The server requires an initialized instance with at least one team. If the instance is missing, the server starts but all endpoints return 503.

## Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Engine health check. Returns loaded teams, tools, expert count. |

```bash
curl http://localhost:8282/health
```

```json
{
  "status": "ok",
  "teams": ["hook-lab", "cold-outbound"],
  "tools": ["web_search", "scrape_url"],
  "experts": 43
}
```

---

### Teams

| Method | Path | Description |
|--------|------|-------------|
| GET | `/teams` | List all teams with agents, goals, schedules, budgets. |
| GET | `/teams/{team_id}` | Detailed team info including all agent configs. |
| POST | `/teams/generate` | Generate a complete team from a goal description using AI. |

```bash
curl http://localhost:8282/teams
```

```bash
curl http://localhost:8282/teams/hook-lab
```

**Generate a team:**

```bash
curl -X POST http://localhost:8282/teams/generate \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "optimize LinkedIn engagement for developer audience",
    "context": "B2B developer tools, 500 free users",
    "name": "linkedin-lab",
    "budget": 30.0
  }'
```

Returns the generated team config, agent list, flow, and first experiment hypothesis.

---

### Agents

| Method | Path | Description |
|--------|------|-------------|
| GET | `/agents` | List all agents across all teams. |
| GET | `/agents/{team_id}/{agent_id}` | Agent detail: config, recent runs, experiments, instructions. |
| GET | `/agents/{team_id}/{agent_id}/strategy` | Read the agent's current strategy.md file. |
| POST | `/agents/{team_id}/{agent_id}/run` | Run a single agent with optional context. |

```bash
curl http://localhost:8282/agents
```

**Get agent detail:**

```bash
curl http://localhost:8282/agents/hook-lab/copywriter
```

Returns model config, instructions, metric, recent runs, and experiment history.

**Read agent strategy:**

```bash
curl http://localhost:8282/agents/hook-lab/copywriter/strategy
```

```json
{
  "content": "# Hook Strategy\n\n## Seed Knowledge...",
  "path": "/home/user/.swarma/instances/default/teams/hook-lab/results/copywriter/strategy.md"
}
```

**Run a single agent:**

```bash
curl -X POST http://localhost:8282/agents/hook-lab/researcher/run \
  -H "Content-Type: application/json" \
  -d '{"context": {"topic": "AI agents in e-commerce"}}'
```

---

### Cycles

| Method | Path | Description |
|--------|------|-------------|
| POST | `/cycle` | Trigger a full cycle for a team. Runs all agents in flow order. |

```bash
curl -X POST http://localhost:8282/cycle \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "hook-lab",
    "topic": "AI agents are overhyped"
  }'
```

The `topic` field is optional. If omitted, agents use their default task from instructions.

Response:

```json
{
  "team_id": "hook-lab",
  "results": {
    "researcher": {
      "agent_id": "researcher",
      "content": "## Research Brief\n\n**Topic**: ...",
      "model": "mistralai/mistral-nemo",
      "cost": 0.000012
    },
    "copywriter": {
      "agent_id": "copywriter",
      "content": "[A] 73% of AI agent startups...",
      "model": "qwen/qwen3.5-plus-02-15",
      "cost": 0.000045
    },
    "judge": {
      "agent_id": "judge",
      "content": "## Scores\n\nVariation A: ...",
      "model": "mistralai/mistral-nemo",
      "cost": 0.000008
    }
  },
  "agents_run": ["researcher", "copywriter", "judge"],
  "duration_seconds": 4.2,
  "total_cost": 0.000065,
  "errors": {}
}
```

---

### Experiments

| Method | Path | Description |
|--------|------|-------------|
| GET | `/experiments` | List all experiments. Filter by `status` and/or `team_id` query params. |
| POST | `/experiments` | Create a new experiment manually. |
| GET | `/experiments/{exp_id}` | Get experiment detail including linked outputs. |
| PUT | `/experiments/{exp_id}/verdict` | Close an experiment with a verdict. |

**List experiments:**

```bash
curl "http://localhost:8282/experiments"
```

Filter by status (`running`, `keep`, `discard`, `inconclusive`):

```bash
curl "http://localhost:8282/experiments?status=running"
```

Filter by team:

```bash
curl "http://localhost:8282/experiments?team_id=hook-lab"
```

**Create an experiment:**

```bash
curl -X POST http://localhost:8282/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "hook-lab",
    "agent_id": "copywriter",
    "hypothesis": "loss framing outperforms gain framing for developer audiences",
    "metric_name": "hook_score",
    "baseline": 6.5,
    "target": 8.0,
    "sample_size": 5
  }'
```

```json
{"id": 7, "status": "created"}
```

**Get experiment detail:**

```bash
curl http://localhost:8282/experiments/7
```

Returns the experiment record plus all linked outputs.

**Close an experiment with verdict:**

```bash
curl -X PUT http://localhost:8282/experiments/7/verdict \
  -H "Content-Type: application/json" \
  -d '{
    "verdict": "keep",
    "result": 8.2,
    "strategy_change": "Use loss framing as default for developer-targeted hooks"
  }'
```

Valid verdicts: `keep`, `discard`, `inconclusive`.

When verdict is `keep`, the hypothesis gets appended to the agent's `strategy.md` and saved to the cross-team playbook. When `discard`, it's logged as an anti-pattern.

---

### Playbook

| Method | Path | Description |
|--------|------|-------------|
| GET | `/playbook` | Get all validated patterns (kept experiments) and anti-patterns (discarded). |
| GET | `/playbook/search` | Semantic search across the cross-team playbook via QMD. |

**Get the playbook:**

```bash
curl http://localhost:8282/playbook
```

Filter by team:

```bash
curl "http://localhost:8282/playbook?team_id=hook-lab"
```

```json
{
  "patterns": [
    {
      "id": 3,
      "hypothesis": "specific numbers in hooks increase save rate",
      "metric": "hook_score",
      "result": 8.4,
      "baseline": 6.5,
      "improvement": 29.2,
      "agent_id": "copywriter",
      "team_id": "hook-lab",
      "closed_at": "2026-03-28T14:30:00",
      "strategy_change": "Always include at least one specific number in the first sentence",
      "verdict": "keep"
    }
  ],
  "count": 1
}
```

**Semantic search:**

```bash
curl "http://localhost:8282/playbook/search?q=hooks%20for%20developers&limit=5"
```

Requires QMD to be running. Returns semantically relevant patterns from the knowledge store.

---

### Metrics (External)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/metrics` | Push an external metric score into the experiment loop. |

```bash
curl -X POST http://localhost:8282/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "hook-lab/copywriter",
    "output_id": "post-2026-03-28",
    "score": 4.2,
    "description": "CTR from LinkedIn analytics"
  }'
```

The `agent` field accepts either `agent_id` (searches all teams) or `team_id/agent_id` format.

---

### Plans (Approval Flow)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/plans` | List pending plans awaiting approval. |
| POST | `/plans/{plan_id}` | Approve or reject a plan. |

```bash
curl http://localhost:8282/plans
```

**Approve:**

```bash
curl -X POST http://localhost:8282/plans/5 \
  -H "Content-Type: application/json" \
  -d '{"action": "approve", "reason": "looks good"}'
```

**Reject:**

```bash
curl -X POST http://localhost:8282/plans/5 \
  -H "Content-Type: application/json" \
  -d '{"action": "reject", "reason": "too risky"}'
```

---

### Outputs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/outputs` | Recent outputs from all teams. Filter by `team_id`, set `limit`. |

```bash
curl "http://localhost:8282/outputs?team_id=hook-lab&limit=10"
```

---

### Tools

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tools` | List all installed tools in the registry. |
| POST | `/tools` | Install a new tool. |

```bash
curl http://localhost:8282/tools
```

**Install a tool:**

```bash
curl -X POST http://localhost:8282/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web_search",
    "type": "builtin",
    "description": "Search the web"
  }'
```

---

### Experts

| Method | Path | Description |
|--------|------|-------------|
| GET | `/experts` | List all experts in the catalog (id, name, domain). |
| GET | `/experts/{expert_id}` | Detailed expert info: thesis, beliefs, questions, frameworks count. |

```bash
curl http://localhost:8282/experts
```

```bash
curl http://localhost:8282/experts/7
```

---

### Knowledge

| Method | Path | Description |
|--------|------|-------------|
| GET | `/knowledge/status` | Knowledge store status: QMD connection, artifact counts by collection. |

```bash
curl http://localhost:8282/knowledge/status
```

```json
{
  "status": "connected",
  "total_artifacts": 147,
  "collections": {
    "content-drafts": 45,
    "research-scans": 38,
    "experiment-results": 32,
    "playbook": 18,
    "decisions": 14
  }
}
```

---

### Costs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/costs` | Cost breakdown: today, this month, router total. |

```bash
curl http://localhost:8282/costs
```

```json
{
  "today": 0.0234,
  "this_month": 1.47,
  "router_total": 3.82
}
```

---

### Status

| Method | Path | Description |
|--------|------|-------------|
| GET | `/status` | Combined status: costs, recent runs, queue stats. |

```bash
curl http://localhost:8282/status
```

---

### Activity

| Method | Path | Description |
|--------|------|-------------|
| GET | `/activity` | Unified activity feed (runs + experiments), sorted by time. Set `limit`. |

```bash
curl "http://localhost:8282/activity?limit=20"
```

---

### Setup Wizard

| Method | Path | Description |
|--------|------|-------------|
| POST | `/setup/deploy` | Deploy a new team from the setup wizard UI. Creates team dir, agents, optional first experiment. |

```bash
curl -X POST http://localhost:8282/setup/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-team",
    "goal": "test hook angles for B2B",
    "agents": [
      {"id": "researcher", "model": "mistralai/mistral-nemo"},
      {"id": "writer", "model": "qwen/qwen3.5-plus-02-15"}
    ],
    "flow": "researcher -> writer",
    "hypothesis": "data-led hooks outperform story-led for B2B"
  }'
```

---

### Dashboard Pages

These serve the static dashboard HTML. Not API endpoints -- browser navigation.

| Path | Page |
|------|------|
| `/dashboard` | Main dashboard |
| `/setup` | Setup wizard |
| `/experiments-view` | Experiments list |
| `/playbook-view` | Playbook viewer |
| `/agents-view` | Agents overview |
| `/agent/{team_id}/{agent_id}` | Agent detail page |
| `/flow-view` | Flow visualization |
| `/knowledge-view` | Knowledge store browser |
| `/settings-view` | Settings |
