# Running swarma with Hermes

## What Hermes Adds

swarma is an engine. It runs experiment cycles, tracks state, and builds playbooks. But it has no opinions about when to run, what to prioritize, or how to talk to you.

Hermes is the operator layer. When connected to swarma via MCP:

- **Operator judgment**: Hermes decides which squads to run, when, and in what order based on your goals and current context
- **Approval flow**: Experiments that need human sign-off surface through Hermes (Telegram, Slack, or CLI)
- **Sub-agent delegation**: Hermes can run swarma cycles as part of larger workflows (research -> generate hooks -> publish -> track)
- **Natural language control**: "run the hook lab on AI agents" instead of `swarma cycle hook-lab --topic "AI agents"`
- **Memory integration**: Hermes memory (QMD) + swarma knowledge store combine for cross-session learning

The relationship: Hermes is the executive, swarma is the machine.

## MCP Server Configuration

swarma exposes its engine as an MCP tool provider. Any MCP client can connect -- Hermes, Claude Desktop, Claude Code, or custom clients.

### Option 1: stdio Transport (recommended for local)

The MCP client spawns swarma as a subprocess. No network, no ports, no CORS.

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
      "env": {
        "OPENROUTER_API_KEY": "sk-or-..."
      }
    }
  }
}
```

**Important**: `OPENROUTER_API_KEY` must be in the `env` block. The instance `.env` file is not inherited by MCP subprocesses.

### Option 2: HTTP Transport (for remote / multi-client)

Run swarma as a persistent HTTP server. Multiple clients can connect.

Start the server:

```bash
swarma serve --mcp --http 8383
```

**Hermes** (`config.yaml`):

```yaml
mcp_servers:
  swarma:
    transport: http
    url: http://localhost:8383/mcp
```

For remote VPS deployments:

```yaml
mcp_servers:
  swarma:
    transport: http
    url: http://your-server-ip:8383/mcp
```

### Option 3: Both API + MCP

Run the REST API and MCP server simultaneously:

```bash
swarma serve --port 8282 --mcp --http 8383
```

This gives you:
- REST API on `:8282` (dashboard, webhooks, external integrations)
- MCP server on `:8383` (Hermes, Claude, other MCP clients)

## Available MCP Tools

The MCP server exposes 16 tools. Here are the key ones grouped by function:

### Engine Control

| Tool | Description |
|------|-------------|
| `swarma_run_cycle` | Run a full cycle for a team. The primary action. |
| `swarma_run_agent` | Run a single agent with optional context. |
| `swarma_health` | Check engine health: loaded teams, tools, experts count. |
| `swarma_status` | Get costs, recent runs, queue stats. |
| `swarma_costs` | Cost breakdown: today, this month, router total. |

### Teams and Agents

| Tool | Description |
|------|-------------|
| `swarma_list_teams` | List all teams with goals, agents, schedules. |
| `swarma_get_team` | Detailed info about a specific team. |
| `swarma_list_agents` | All agents across all teams. |
| `swarma_generate_team` | Generate a complete team from a goal description. |

### Experiment Loop

| Tool | Description |
|------|-------------|
| `swarma_list_plans` | Pending plans awaiting approval. |
| `swarma_approve_plan` | Approve a pending experiment plan. |
| `swarma_reject_plan` | Reject a pending plan with reason. |

### Knowledge and Outputs

| Tool | Description |
|------|-------------|
| `swarma_get_outputs` | Recent outputs, optionally filtered by team. |
| `swarma_list_tools` | Installed tools in the registry. |
| `swarma_list_experts` | All experts in the catalog. |
| `swarma_get_expert` | Detailed expert info by ID. |

## Workflow: Hermes as Operator

A typical Hermes + swarma interaction:

**You (via Telegram)**: "run the content squad on AI agent infrastructure"

**Hermes** (under the hood):

1. Calls `swarma_list_teams` to find the right team
2. Calls `swarma_run_cycle` with `team_id: "hook-lab"` and `topic: "AI agent infrastructure"`
3. Reads the cycle results
4. Summarizes: "Hook lab ran. Researcher found an angle on infrastructure costs. Copywriter produced 3 variations. Judge scored variation B highest (8.2). Strategy updated."

**You**: "what's worked so far?"

**Hermes**:

1. Calls `swarma_status` for recent activity
2. Calls `swarma_get_outputs` for recent outputs
3. Synthesizes a briefing from swarma state + its own memory

**You**: "approve the new experiment"

**Hermes**:

1. Calls `swarma_list_plans` to find pending plans
2. Calls `swarma_approve_plan` with the plan ID
3. Confirms: "Experiment #7 approved: testing loss framing vs gain framing on developer audience"

## Example: Full Cycle via Hermes

When Hermes calls `swarma_run_cycle`, this is what happens inside swarma:

```
swarma_run_cycle(team_id="hook-lab", topic="AI agents are overhyped")
  |
  +-- Load team config (team.yaml, program.md)
  +-- Parse flow: researcher -> copywriter -> judge
  |
  +-- Run researcher
  |     Read strategy.md + knowledge context
  |     Call LLM (mistral-nemo, 1500 tokens)
  |     Output: research brief with angle, proof points, emotional lever
  |     Self-eval: score against angle_specificity metric
  |     Log to results.tsv
  |
  +-- Run copywriter (receives researcher output as context)
  |     Read strategy.md + knowledge context
  |     Call LLM (qwen, 800 tokens)
  |     Output: 3 hook variations [A] [B] [C]
  |     Self-eval: score against hook_score metric
  |     Log to results.tsv
  |     Check experiment: 3/5 samples -> still running
  |
  +-- Run judge (receives copywriter output as context)
  |     Read strategy.md
  |     Call LLM (mistral-nemo, 500 tokens)
  |     Output: scored variations + winner + suggestion
  |
  +-- Return combined results to Hermes
```

Total cost: approximately $0.001-0.01 per cycle depending on models.

## QMD Integration

swarma has a built-in knowledge store that saves artifacts as markdown files on disk, indexed in SQLite. When QMD (Hermes' semantic search engine) is available, swarma uses it for:

- **Cross-team playbook search**: "what hooks worked for developer audiences?" searches validated patterns from ALL teams
- **Artifact indexing**: every cycle output, experiment result, and strategy change gets indexed
- **Context building**: agents pull relevant knowledge from QMD before each run

### How it works

1. swarma saves an artifact to `knowledge/{collection}/{timestamp}_{slug}.md`
2. swarma calls `qmd update {collection}` to trigger re-indexing (fire-and-forget)
3. On the next cycle, agents query QMD for relevant context via `knowledge.qmd_query()`

### QMD search via API

If QMD is running as an MCP server, swarma connects to it for semantic search:

```yaml
# In swarma config.yaml
knowledge:
  engine: qmd
  qmd_endpoint: http://localhost:8384/mcp
```

Without QMD, swarma falls back to local CLI search (`qmd search ...`) or SQLite metadata queries. The system works without QMD -- it just searches better with it.

### Memory overlap

Hermes has its own memory. swarma has its knowledge store. They complement each other:

- **Hermes memory**: operator-level context (your goals, preferences, conversation history)
- **swarma knowledge store**: experiment-level data (what worked, strategy evolution, cross-team patterns)

When Hermes runs a swarma cycle and reads the results, it can save insights to its own memory ("hook-lab: loss framing outperforms gain framing for developer audiences"). Next time you ask about content strategy, Hermes has both its own context and can query swarma's playbook.

## Troubleshooting

**"Engine not initialized"**: swarma couldn't find the instance. Check that `~/.swarma/instances/default/` exists and has a `config.yaml`. Run `swarma init` if needed.

**"OPENROUTER_API_KEY not found"**: The key must be in the MCP `env` block for stdio transport, or in the instance `.env` for HTTP transport. The instance `.env` is NOT inherited by subprocesses.

**MCP connection refused (HTTP)**: Check that `swarma serve --mcp --http 8383` is running. Verify the port is not blocked by a firewall.

**Slow first cycle**: The first run creates the SQLite database and initializes state. Subsequent cycles are faster.
