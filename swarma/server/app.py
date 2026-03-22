"""FastAPI server for swarma instances.

Exposes the engine over HTTP so dashboards, Hermes, and external
tools can trigger cycles, read state, and manage agents.

Usage:
    swarma run --port 8282           # start engine + API
    uvicorn swarma.server.app:app    # standalone API (needs engine setup)
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# --- Request/Response models ---

class CycleRequest(BaseModel):
    team_id: str
    topic: Optional[str] = None


class AgentRunRequest(BaseModel):
    context: Optional[dict] = None


class PlanAction(BaseModel):
    action: str  # approve | reject
    reason: Optional[str] = None


class ToolInstallRequest(BaseModel):
    name: str
    type: str = "builtin"
    provider: Optional[str] = None
    endpoint: Optional[str] = None
    method: str = "GET"
    description: str = ""
    credentials: Optional[dict] = None


class MetricPushRequest(BaseModel):
    agent: str  # agent_id (or team/agent)
    output_id: str
    score: float
    description: Optional[str] = None
    team_id: Optional[str] = None


class ExperimentCreateRequest(BaseModel):
    team_id: str
    agent_id: str = "growth-lead"
    hypothesis: str
    metric_name: str = "engagement_rate"
    baseline: Optional[float] = None
    target: Optional[float] = None
    sample_size: int = 5


class ExperimentVerdictRequest(BaseModel):
    verdict: str  # keep | discard | inconclusive
    result: float = 0.0
    strategy_change: Optional[str] = None


# --- App factory ---

def create_app(engine=None) -> FastAPI:
    """Create the FastAPI app, optionally injecting an engine.

    If engine is None, it will be built from env vars on startup.
    """
    app = FastAPI(
        title="swarma",
        description="Learning agent swarms API",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store engine on app state
    app.state.engine = engine

    def _engine():
        if app.state.engine is None:
            raise HTTPException(503, "Engine not initialized")
        return app.state.engine

    # --- Health ---

    @app.get("/health")
    async def health():
        eng = _engine()
        return {
            "status": "ok",
            "teams": list(eng.teams.keys()),
            "tools": eng.tool_registry.list_names() if eng.tool_registry else [],
            "experts": eng.expert_catalog.count if eng.expert_catalog else 0,
        }

    # --- Teams ---

    @app.get("/teams")
    async def list_teams():
        eng = _engine()
        return {
            tid: {
                "name": t.name,
                "goal": t.goal,
                "flow": t.flow,
                "schedule": t.schedule,
                "budget_monthly": t.budget_monthly,
                "agents": list(t.agents.keys()),
                "tools": t.tools,
            }
            for tid, t in eng.teams.items()
        }

    @app.get("/teams/{team_id}")
    async def get_team(team_id: str):
        eng = _engine()
        team = eng.teams.get(team_id)
        if not team:
            raise HTTPException(404, f"Team '{team_id}' not found")
        return {
            "id": team.id,
            "name": team.name,
            "goal": team.goal,
            "flow": team.flow,
            "schedule": team.schedule,
            "budget_monthly": team.budget_monthly,
            "agents": {
                aid: {
                    "name": a.name,
                    "model": a.model.model_id,
                    "runtime": a.runtime,
                    "tools": a.tools,
                    "expert_lenses": a.expert_lenses,
                    "schedule": a.schedule,
                    "triggered_by": a.triggered_by,
                }
                for aid, a in team.agents.items()
            },
            "tools": team.tools,
        }

    # --- Agents ---

    @app.get("/agents")
    async def list_agents():
        eng = _engine()
        agents = {}
        for tid, t in eng.teams.items():
            for aid, a in t.agents.items():
                agents[f"{tid}/{aid}"] = {
                    "team": tid,
                    "name": a.name,
                    "model": a.model.model_id,
                    "runtime": a.runtime,
                }
        return agents

    @app.post("/agents/{team_id}/{agent_id}/run")
    async def run_agent(team_id: str, agent_id: str, req: AgentRunRequest):
        eng = _engine()
        runner = eng._runners.get(team_id)
        if not runner:
            raise HTTPException(404, f"Team '{team_id}' not found")

        agent = runner._agents.get(agent_id)
        if not agent:
            raise HTTPException(404, f"Agent '{agent_id}' not found in team '{team_id}'")

        try:
            result = await agent.run(req.context)
            return result
        except Exception as e:
            raise HTTPException(500, str(e))

    # --- Cycles ---

    @app.post("/cycle")
    async def run_cycle(req: CycleRequest):
        eng = _engine()
        context = {}
        if req.topic:
            context = {"topic": req.topic, "task": req.topic}

        try:
            result = await eng.run_cycle(req.team_id, context or None)
            return result
        except ValueError as e:
            raise HTTPException(404, str(e))
        except Exception as e:
            raise HTTPException(500, str(e))

    # --- State / Status ---

    @app.get("/status")
    async def get_status():
        eng = _engine()
        state = eng.state

        daily = state.get_daily_cost()
        monthly = state.get_monthly_cost()

        runs = state.conn.execute(
            "SELECT agent_id, status, started_at FROM agent_runs ORDER BY id DESC LIMIT 10"
        ).fetchall()

        return {
            "costs": {"today": daily, "this_month": monthly},
            "recent_runs": [
                {"agent_id": r["agent_id"], "status": r["status"], "started_at": r["started_at"]}
                for r in runs
            ],
            "queue": state.get_queue_stats(),
        }

    @app.get("/costs")
    async def get_costs():
        eng = _engine()
        return {
            "today": eng.state.get_daily_cost(),
            "this_month": eng.state.get_monthly_cost(),
            "router_total": eng.router.total_cost,
        }

    # --- External Metrics ---

    @app.post("/metrics")
    async def push_metric(req: MetricPushRequest):
        """Push an external metric score into the experiment loop.

        Use this to feed real signals (analytics, human ratings, API metrics)
        back into an agent's results.tsv instead of relying on self-eval.
        """
        eng = _engine()

        # Resolve team_id if not provided
        team_id = req.team_id
        agent_id = req.agent
        if "/" in agent_id:
            team_id, agent_id = agent_id.split("/", 1)

        if not team_id:
            # Find the agent across all teams
            for tid, t in eng.teams.items():
                if agent_id in t.agents:
                    team_id = tid
                    break

        if not team_id:
            raise HTTPException(404, f"Agent '{req.agent}' not found in any team")

        # Find the agent's experiment engine and log the result
        runner = eng._runners.get(team_id)
        if not runner:
            raise HTTPException(404, f"Team '{team_id}' not found")

        agent = runner._agents.get(agent_id)
        if not agent:
            raise HTTPException(404, f"Agent '{agent_id}' not found in team '{team_id}'")

        if not hasattr(agent, 'experiment_engine') or not agent.experiment_engine:
            raise HTTPException(400, f"Agent '{agent_id}' has no experiment engine configured")

        description = req.description or f"external metric: {req.score}"
        agent.experiment_engine.log_result(req.output_id, req.score, "measured", description)

        return {
            "status": "logged",
            "agent": f"{team_id}/{agent_id}",
            "output_id": req.output_id,
            "score": req.score,
        }

    # --- Plans (approval flow) ---

    @app.get("/plans")
    async def get_plans():
        eng = _engine()
        plans = eng.state.get_pending_plans()
        return {"pending": len(plans), "plans": plans}

    @app.post("/plans/{plan_id}")
    async def action_plan(plan_id: int, action: PlanAction):
        eng = _engine()
        if action.action == "approve":
            eng.state.approve_plan(plan_id)
        elif action.action == "reject":
            eng.state.reject_plan(plan_id)
        else:
            raise HTTPException(400, f"Invalid action: {action.action}. Use 'approve' or 'reject'.")
        return {"status": "ok", "plan_id": plan_id, "action": action.action}

    # --- Outputs ---

    @app.get("/outputs")
    async def get_outputs(team_id: Optional[str] = None, limit: int = 20):
        eng = _engine()
        query = "SELECT * FROM outputs ORDER BY id DESC LIMIT ?"
        params = [limit]
        if team_id:
            query = "SELECT * FROM outputs WHERE team_id = ? ORDER BY id DESC LIMIT ?"
            params = [team_id, limit]
        rows = eng.state.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    # --- Tools ---

    @app.get("/tools")
    async def list_tools():
        eng = _engine()
        if not eng.tool_registry:
            return {}
        return {
            name: {
                "type": (eng.tool_registry.get_config(name).type
                         if eng.tool_registry.get_config(name) else "unknown"),
            }
            for name in eng.tool_registry.list_names()
        }

    @app.post("/tools")
    async def install_tool(req: ToolInstallRequest):
        eng = _engine()
        if not eng.tool_registry:
            raise HTTPException(503, "Tool registry not available")

        try:
            eng.tool_registry.install_from_dict(req.name, {
                "type": req.type,
                "provider": req.provider,
                "endpoint": req.endpoint,
                "method": req.method,
                "description": req.description,
                "credentials": req.credentials or {},
            })
            return {"status": "installed", "name": req.name}
        except Exception as e:
            raise HTTPException(400, str(e))

    # --- Experts ---

    @app.get("/experts")
    async def list_experts():
        eng = _engine()
        if not eng.expert_catalog:
            return []
        return [
            {"id": e.id, "name": e.name, "domain": e.domain}
            for e in eng.expert_catalog.list_all()
        ]

    @app.get("/experts/{expert_id}")
    async def get_expert(expert_id: int):
        eng = _engine()
        if not eng.expert_catalog:
            raise HTTPException(503, "Expert catalog not loaded")
        expert = eng.expert_catalog.get(expert_id)
        if not expert:
            raise HTTPException(404, f"Expert {expert_id} not found")
        return {
            "id": expert.id,
            "name": expert.name,
            "domain": expert.domain,
            "core_thesis": expert.core_thesis,
            "operating_beliefs": expert.operating_beliefs,
            "key_questions": expert.key_questions,
            "frameworks": len(expert.frameworks),
        }

    # --- Experiments ---

    @app.get("/experiments")
    async def list_experiments(status: Optional[str] = None, team_id: Optional[str] = None):
        eng = _engine()
        query = "SELECT * FROM experiments"
        conditions = []
        params = []
        if status:
            conditions.append("verdict = ?")
            params.append(status)
        if team_id:
            conditions.append("team_id = ?")
            params.append(team_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC"
        rows = eng.state.conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            # Alias DB column names to what the dashboard expects
            d["current_sample"] = d.get("sample_size_current", 0)
            d["sample_size"] = d.get("sample_size_needed", 5)
            # Compute improvement percentage
            if d.get("baseline") and d.get("result"):
                d["improvement_pct"] = round(
                    (d["result"] - d["baseline"]) / d["baseline"] * 100, 1
                )
            else:
                d["improvement_pct"] = None
            results.append(d)
        return results

    @app.post("/experiments")
    async def create_experiment(req: ExperimentCreateRequest):
        eng = _engine()
        exp_id = eng.state.create_experiment(
            team_id=req.team_id,
            agent_id=req.agent_id,
            hypothesis=req.hypothesis,
            metric_name=req.metric_name,
            baseline=req.baseline,
            target=req.target,
            sample_size=req.sample_size,
        )
        return {"id": exp_id, "status": "created"}

    @app.get("/experiments/{exp_id}")
    async def get_experiment(exp_id: int):
        eng = _engine()
        row = eng.state.conn.execute(
            "SELECT * FROM experiments WHERE id = ?", (exp_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, f"Experiment {exp_id} not found")
        exp = dict(row)
        # Get linked outputs
        outputs = eng.state.conn.execute(
            "SELECT id, agent_id, output_type, status, created_at FROM outputs WHERE experiment_id = ? ORDER BY id DESC",
            (exp_id,),
        ).fetchall()
        exp["outputs"] = [dict(o) for o in outputs]
        return exp

    @app.put("/experiments/{exp_id}/verdict")
    async def set_experiment_verdict(exp_id: int, req: ExperimentVerdictRequest):
        eng = _engine()
        eng.state.close_experiment(exp_id, req.result, req.verdict, req.strategy_change)
        return {"id": exp_id, "verdict": req.verdict}

    # --- Playbook (validated patterns from strategy files) ---

    @app.get("/playbook")
    async def get_playbook(team_id: Optional[str] = None):
        eng = _engine()
        # Get all kept experiments as validated patterns
        query = "SELECT * FROM experiments WHERE verdict = 'keep'"
        params = []
        if team_id:
            query += " AND team_id = ?"
            params.append(team_id)
        query += " ORDER BY closed_at DESC"
        rows = eng.state.conn.execute(query, params).fetchall()
        patterns = []
        for r in rows:
            d = dict(r)
            patterns.append({
                "id": d["id"],
                "hypothesis": d["hypothesis"],
                "metric": d["metric_name"],
                "result": d["result"],
                "baseline": d["baseline"],
                "improvement": (
                    round((d["result"] - d["baseline"]) / d["baseline"] * 100, 1)
                    if d["baseline"] and d["result"] else None
                ),
                "agent_id": d["agent_id"],
                "team_id": d["team_id"],
                "closed_at": d["closed_at"],
                "strategy_change": d["strategy_change"],
            })
        return {"patterns": patterns, "count": len(patterns)}

    # --- Activity log ---

    @app.get("/activity")
    async def get_activity(limit: int = 50):
        eng = _engine()
        # Combine agent_runs + experiments into a unified activity feed
        runs = eng.state.conn.execute(
            "SELECT id, team_id, agent_id, run_type as type, status, started_at as timestamp, 'run' as source FROM agent_runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        exps = eng.state.conn.execute(
            "SELECT id, team_id, agent_id, hypothesis as type, verdict as status, created_at as timestamp, 'experiment' as source FROM experiments ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        # Merge and sort by timestamp
        activity = [dict(r) for r in runs] + [dict(r) for r in exps]
        activity.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return activity[:limit]

    # --- Agent detail ---

    @app.get("/agents/{team_id}/{agent_id}")
    async def get_agent_detail(team_id: str, agent_id: str):
        eng = _engine()
        team = eng.teams.get(team_id)
        if not team:
            raise HTTPException(404, f"Team '{team_id}' not found")
        agent_cfg = team.agents.get(agent_id)
        if not agent_cfg:
            raise HTTPException(404, f"Agent '{agent_id}' not found in team '{team_id}'")

        # Recent runs
        runs = eng.state.conn.execute(
            "SELECT * FROM agent_runs WHERE team_id = ? AND agent_id = ? ORDER BY id DESC LIMIT 20",
            (team_id, agent_id),
        ).fetchall()

        # Experiments
        experiments = eng.state.conn.execute(
            "SELECT * FROM experiments WHERE team_id = ? AND agent_id = ? ORDER BY id DESC",
            (team_id, agent_id),
        ).fetchall()

        return {
            "id": agent_id,
            "team_id": team_id,
            "name": agent_cfg.name,
            "model": agent_cfg.model.model_id,
            "runtime": agent_cfg.runtime,
            "tools": agent_cfg.tools,
            "expert_lenses": agent_cfg.expert_lenses,
            "instructions": agent_cfg.instructions,
            "schedule": agent_cfg.schedule,
            "triggered_by": agent_cfg.triggered_by,
            "metric": {
                "name": agent_cfg.metric.name if agent_cfg.metric else None,
                "target": agent_cfg.metric.target if agent_cfg.metric else None,
            } if agent_cfg.metric else None,
            "recent_runs": [dict(r) for r in runs],
            "experiments": [dict(r) for r in experiments],
        }

    @app.get("/agents/{team_id}/{agent_id}/strategy")
    async def get_agent_strategy(team_id: str, agent_id: str):
        eng = _engine()
        # Try to read strategy.md from the team results directory
        team = eng.teams.get(team_id)
        if not team:
            raise HTTPException(404, f"Team '{team_id}' not found")
        # Strategy file path convention
        instance_dir = Path(eng.state.db_path).parent
        strategy_path = instance_dir / "teams" / team_id / "results" / agent_id / "strategy.md"
        if strategy_path.exists():
            return {"content": strategy_path.read_text(), "path": str(strategy_path)}
        return {"content": "# Strategy\n\nNo strategy file found yet. Run an experiment to start learning.", "path": None}

    # --- Knowledge status ---

    @app.get("/knowledge/status")
    async def get_knowledge_status():
        eng = _engine()
        # Artifact counts by collection
        collections = eng.state.conn.execute(
            "SELECT collection, COUNT(*) as count FROM artifact_log GROUP BY collection"
        ).fetchall()
        total = eng.state.conn.execute(
            "SELECT COUNT(*) as n FROM artifact_log"
        ).fetchone()["n"]

        qmd_status = "disconnected"
        if hasattr(eng, 'knowledge') and eng.knowledge:
            qmd_status = "connected" if eng.knowledge.qmd_endpoint else "local-only"

        return {
            "status": qmd_status,
            "total_artifacts": total,
            "collections": {r["collection"]: r["count"] for r in collections},
        }

    # --- Dashboard (static files) ---

    dashboard_dir = Path(__file__).parent.parent / "dashboard" / "static"
    if dashboard_dir.exists():
        def _serve(filename):
            """Helper to serve a dashboard HTML file."""
            path = dashboard_dir / filename
            if path.exists():
                return FileResponse(path)
            raise HTTPException(404, f"Page not found: {filename}")

        @app.get("/dashboard")
        async def dashboard():
            return _serve("index.html")

        @app.get("/setup")
        async def setup():
            return _serve("setup.html")

        @app.get("/experiments-view")
        async def experiments_view():
            return _serve("experiments.html")

        @app.get("/playbook-view")
        async def playbook_view():
            return _serve("playbook.html")

        @app.get("/agents-view")
        async def agents_view():
            return _serve("agents.html")

        @app.get("/agent/{team_id}/{agent_id}")
        async def agent_detail_view(team_id: str, agent_id: str):
            return _serve("agent-detail.html")

        @app.get("/flow-view")
        async def flow_view():
            return _serve("flow.html")

        @app.get("/knowledge-view")
        async def knowledge_view():
            return _serve("knowledge.html")

        @app.get("/settings-view")
        async def settings_view():
            return _serve("settings.html")

        app.mount("/static", StaticFiles(directory=str(dashboard_dir)), name="static")

    return app
