"""SQLite state management for swarma.

Tracks agents, outputs, experiments, costs, plans, artifacts, and task queue.
"""

import json
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional


class StateDB:
    """Lightweight SQLite state store."""

    def __init__(self, db_path: str = "state.db"):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                output_type TEXT NOT NULL DEFAULT 'generic',
                content TEXT NOT NULL,
                external_url TEXT,
                external_id TEXT,
                experiment_id INTEGER,
                status TEXT DEFAULT 'drafted',
                created_at TEXT DEFAULT (datetime('now')),
                published_at TEXT,
                metrics_json TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            );

            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                hypothesis TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                baseline REAL,
                target REAL,
                sample_size_needed INTEGER DEFAULT 5,
                sample_size_current INTEGER DEFAULT 0,
                result REAL,
                verdict TEXT DEFAULT 'running',
                strategy_change TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                closed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS cost_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                team_id TEXT,
                agent_id TEXT,
                service TEXT NOT NULL,
                model TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                run_type TEXT NOT NULL,
                status TEXT DEFAULT 'started',
                input_json TEXT,
                output_json TEXT,
                error TEXT,
                started_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS pending_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                context_json TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                approved_at TEXT,
                rejected_at TEXT
            );

            CREATE TABLE IF NOT EXISTS artifact_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection TEXT NOT NULL,
                filename TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                team_id TEXT NOT NULL,
                title TEXT,
                metadata_json TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS task_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                team_id TEXT NOT NULL,
                context_json TEXT,
                priority INTEGER DEFAULT 3,
                status TEXT DEFAULT 'pending',
                result_summary TEXT,
                error TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                started_at TEXT,
                completed_at TEXT
            );
        """)
        self.conn.commit()

    # -- Outputs (generic, not "posts") --

    def create_output(self, team_id: str, agent_id: str, output_type: str,
                      content: str, experiment_id: Optional[int] = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO outputs (team_id, agent_id, output_type, content, experiment_id) VALUES (?, ?, ?, ?, ?)",
            (team_id, agent_id, output_type, content, experiment_id),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_output(self, output_id: int) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM outputs WHERE id = ?", (output_id,)).fetchone()
        return dict(row) if row else None

    def update_output_status(self, output_id: int, status: str, **kwargs):
        sets = ["status = ?"]
        vals = [status]
        for k, v in kwargs.items():
            sets.append(f"{k} = ?")
            vals.append(v)
        vals.append(output_id)
        self.conn.execute(
            f"UPDATE outputs SET {', '.join(sets)} WHERE id = ?", vals
        )
        self.conn.commit()

    def get_outputs(self, team_id: str, status: Optional[str] = None,
                    output_type: Optional[str] = None, limit: int = 50) -> list[dict]:
        query = "SELECT * FROM outputs WHERE team_id = ?"
        params: list = [team_id]
        if status:
            query += " AND status = ?"
            params.append(status)
        if output_type:
            query += " AND output_type = ?"
            params.append(output_type)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]

    # -- Experiments --

    def create_experiment(self, team_id: str, agent_id: str, hypothesis: str,
                          metric_name: str, baseline: Optional[float] = None,
                          target: Optional[float] = None,
                          sample_size: int = 5) -> int:
        cur = self.conn.execute(
            """INSERT INTO experiments
               (team_id, agent_id, hypothesis, metric_name, baseline, target, sample_size_needed)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (team_id, agent_id, hypothesis, metric_name, baseline, target, sample_size),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_active_experiments(self, team_id: str,
                               agent_id: Optional[str] = None) -> list[dict]:
        query = "SELECT * FROM experiments WHERE team_id = ? AND verdict = 'running'"
        params: list = [team_id]
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]

    def close_experiment(self, exp_id: int, result: float, verdict: str,
                         strategy_change: Optional[str] = None):
        self.conn.execute(
            """UPDATE experiments
               SET result = ?, verdict = ?, strategy_change = ?, closed_at = datetime('now')
               WHERE id = ?""",
            (result, verdict, strategy_change, exp_id),
        )
        self.conn.commit()

    # -- Cost tracking --

    def log_cost(self, team_id: str, agent_id: str, service: str,
                 model: str, input_tokens: int, output_tokens: int, cost: float):
        self.conn.execute(
            """INSERT INTO cost_log (date, team_id, agent_id, service, model, input_tokens, output_tokens, cost)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (date.today().isoformat(), team_id, agent_id, service, model,
             input_tokens, output_tokens, cost),
        )
        self.conn.commit()

    def get_daily_cost(self, day: Optional[str] = None) -> float:
        day = day or date.today().isoformat()
        row = self.conn.execute(
            "SELECT COALESCE(SUM(cost), 0) as total FROM cost_log WHERE date = ?", (day,),
        ).fetchone()
        return row["total"]

    def get_monthly_cost(self, year_month: Optional[str] = None) -> float:
        ym = year_month or date.today().strftime("%Y-%m")
        row = self.conn.execute(
            "SELECT COALESCE(SUM(cost), 0) as total FROM cost_log WHERE date LIKE ?",
            (f"{ym}%",),
        ).fetchone()
        return row["total"]

    # -- Agent runs --

    def start_run(self, team_id: str, agent_id: str, run_type: str,
                  input_data: Optional[dict] = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO agent_runs (team_id, agent_id, run_type, input_json) VALUES (?, ?, ?, ?)",
            (team_id, agent_id, run_type, json.dumps(input_data) if input_data else None),
        )
        self.conn.commit()
        return cur.lastrowid

    def complete_run(self, run_id: int, output: Optional[dict] = None,
                     error: Optional[str] = None):
        status = "error" if error else "completed"
        self.conn.execute(
            "UPDATE agent_runs SET status = ?, output_json = ?, error = ?, completed_at = datetime('now') WHERE id = ?",
            (status, json.dumps(output) if output else None, error, run_id),
        )
        self.conn.commit()

    # -- Pending plans --

    def save_plan(self, team_id: str, plan: dict,
                  context: Optional[dict] = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO pending_plans (team_id, plan_json, context_json) VALUES (?, ?, ?)",
            (team_id, json.dumps(plan), json.dumps(context) if context else None),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_pending_plans(self, team_id: Optional[str] = None) -> list[dict]:
        query = "SELECT * FROM pending_plans WHERE status = 'pending'"
        params: list = []
        if team_id:
            query += " AND team_id = ?"
            params.append(team_id)
        query += " ORDER BY created_at DESC"
        return [dict(r) for r in self.conn.execute(query, params).fetchall()]

    def get_plan(self, plan_id: int) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM pending_plans WHERE id = ?", (plan_id,)).fetchone()
        return dict(row) if row else None

    def approve_plan(self, plan_id: int):
        self.conn.execute(
            "UPDATE pending_plans SET status = 'approved', approved_at = datetime('now') WHERE id = ?",
            (plan_id,),
        )
        self.conn.commit()

    def reject_plan(self, plan_id: int):
        self.conn.execute(
            "UPDATE pending_plans SET status = 'rejected', rejected_at = datetime('now') WHERE id = ?",
            (plan_id,),
        )
        self.conn.commit()

    # -- Artifact log --

    def log_artifact(self, collection: str, filename: str, agent_id: str,
                     team_id: str, title: Optional[str] = None,
                     metadata: Optional[dict] = None):
        self.conn.execute(
            """INSERT INTO artifact_log (collection, filename, agent_id, team_id, title, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (collection, filename, agent_id, team_id, title,
             json.dumps(metadata) if metadata else None),
        )
        self.conn.commit()

    def search_artifacts(self, collection: Optional[str] = None,
                         agent_id: Optional[str] = None,
                         team_id: Optional[str] = None,
                         query: Optional[str] = None,
                         limit: int = 20) -> list[dict]:
        conditions: list[str] = []
        params: list = []
        if collection:
            conditions.append("collection = ?")
            params.append(collection)
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if team_id:
            conditions.append("team_id = ?")
            params.append(team_id)
        if query:
            conditions.append("(title LIKE ? OR filename LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM artifact_log {where} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def get_recent_artifacts(self, collection: str, limit: int = 10,
                             agent_id: Optional[str] = None) -> list[dict]:
        if agent_id:
            return [dict(r) for r in self.conn.execute(
                "SELECT * FROM artifact_log WHERE collection = ? AND agent_id = ? ORDER BY created_at DESC LIMIT ?",
                (collection, agent_id, limit),
            ).fetchall()]
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM artifact_log WHERE collection = ? ORDER BY created_at DESC LIMIT ?",
            (collection, limit),
        ).fetchall()]

    # -- Task queue --

    def enqueue_task(self, event_type: str, agent_id: str, team_id: str,
                     context: Optional[dict] = None, priority: int = 3) -> int:
        cur = self.conn.execute(
            """INSERT INTO task_queue (event_type, agent_id, team_id, context_json, priority)
               VALUES (?, ?, ?, ?, ?)""",
            (event_type, agent_id, team_id,
             json.dumps(context) if context else None, priority),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_pending_tasks(self, limit: int = 20) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM task_queue WHERE status = 'pending' ORDER BY priority ASC, created_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("context_json"):
                try:
                    d["context"] = json.loads(d["context_json"])
                except (json.JSONDecodeError, TypeError):
                    d["context"] = None
            else:
                d["context"] = None
            result.append(d)
        return result

    def update_task_status(self, task_id: int, status: str,
                           result_summary: Optional[str] = None,
                           error: Optional[str] = None):
        now = datetime.now().isoformat()
        if status == "processing":
            self.conn.execute(
                "UPDATE task_queue SET status = ?, started_at = ? WHERE id = ?",
                (status, now, task_id),
            )
        else:
            self.conn.execute(
                "UPDATE task_queue SET status = ?, completed_at = ?, result_summary = ?, error = ? WHERE id = ?",
                (status, now, result_summary, error, task_id),
            )
        self.conn.commit()

    def get_queue_stats(self) -> dict:
        pending = self.conn.execute(
            "SELECT COUNT(*) as n FROM task_queue WHERE status = 'pending'"
        ).fetchone()["n"]
        processing = self.conn.execute(
            "SELECT COUNT(*) as n FROM task_queue WHERE status = 'processing'"
        ).fetchone()["n"]
        return {"pending": pending, "processing": processing}

    def close(self):
        self.conn.close()
