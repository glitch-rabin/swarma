"""Knowledge store -- the memory layer that makes agents learn across cycles.

Artifacts are markdown files on disk, indexed in SQLite for fast metadata
queries. Optional QMD integration for semantic search (BM25 + vector + rerank).
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class KnowledgeStore:
    """Write artifacts to disk, track in SQLite, optionally search via QMD."""

    def __init__(self, base_dir: str, state_db, qmd_endpoint: Optional[str] = None):
        self.base_dir = Path(base_dir)
        self.state = state_db
        self.qmd_endpoint = qmd_endpoint
        self._qmd_session_id: Optional[str] = None
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_collection(self, collection: str):
        """Create collection directory if it doesn't exist."""
        (self.base_dir / collection).mkdir(parents=True, exist_ok=True)

    def save(
        self,
        collection: str,
        content: str,
        agent_id: str,
        team_id: str,
        title: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Save an artifact and optionally trigger QMD indexing.

        Returns the file path of the saved artifact.
        """
        self._ensure_collection(collection)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = (title or agent_id).lower().replace(" ", "-")[:50]
        filename = f"{timestamp}_{slug}.md"
        filepath = self.base_dir / collection / filename

        frontmatter = f"""---
agent: {agent_id}
team: {team_id}
collection: {collection}
created: {datetime.now().isoformat()}
title: {title or f'{agent_id} output'}
---

"""
        filepath.write_text(frontmatter + content)

        self.state.log_artifact(
            collection=collection,
            filename=filename,
            agent_id=agent_id,
            team_id=team_id,
            title=title,
            metadata=metadata,
        )

        self._qmd_update(collection)

        logger.info("saved artifact: %s/%s (%d chars)", collection, filename, len(content))
        return str(filepath)

    def _qmd_update(self, collection: str):
        """Trigger QMD to re-index a collection. Fire-and-forget."""
        try:
            subprocess.Popen(
                ["qmd", "update", collection],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass  # QMD not installed, that's fine
        except Exception as e:
            logger.debug("qmd update failed: %s", e)

    def _qmd_search_sync(self, query: str, collection: Optional[str] = None,
                         limit: int = 10) -> list[dict]:
        """Search QMD via CLI (synchronous)."""
        cmd = ["qmd", "search", query, "--json", "-n", str(limit)]
        if collection:
            cmd.extend(["-c", collection])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            stdout = result.stdout.strip()
            if result.returncode == 0 and stdout:
                json_start = stdout.find("[")
                if json_start >= 0:
                    return json.loads(stdout[json_start:])
            return []
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return []

    async def qmd_query(self, query: str, collection: Optional[str] = None,
                        limit: int = 10) -> list[dict]:
        """Semantic search via QMD MCP endpoint."""
        if not self.qmd_endpoint:
            return self._qmd_search_sync(query, collection, limit)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if not self._qmd_session_id:
                    resp = await client.post(self.qmd_endpoint, json={
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "swarma", "version": "0.1"},
                        },
                        "id": 1,
                    })
                    session_id = resp.headers.get("mcp-session-id")
                    if session_id:
                        self._qmd_session_id = session_id
                        await client.post(
                            self.qmd_endpoint,
                            headers={"mcp-session-id": self._qmd_session_id},
                            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                        )

                headers = {}
                if self._qmd_session_id:
                    headers["mcp-session-id"] = self._qmd_session_id

                q = f"{query} collection:{collection}" if collection else query
                resp = await client.post(
                    self.qmd_endpoint,
                    headers=headers,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {"name": "query", "arguments": {"query": q, "limit": limit}},
                        "id": 2,
                    },
                )
                data = resp.json()
                if "result" in data:
                    content = data["result"].get("content", [])
                    if content and content[0].get("text"):
                        return json.loads(content[0]["text"])
                return []
        except Exception as e:
            logger.debug("qmd MCP query failed, falling back to CLI: %s", e)
            return self._qmd_search_sync(query, collection, limit)

    def search(self, collection: Optional[str] = None, agent_id: Optional[str] = None,
               team_id: Optional[str] = None, query: Optional[str] = None,
               limit: int = 20) -> list[dict]:
        """Search artifacts. QMD for text queries, SQLite for metadata filters."""
        if query:
            qmd_results = self._qmd_search_sync(query, collection, limit)
            if qmd_results:
                return qmd_results

        return self.state.search_artifacts(
            collection=collection, agent_id=agent_id,
            team_id=team_id, query=query, limit=limit,
        )

    def get_recent(self, collection: str, limit: int = 10,
                   agent_id: Optional[str] = None) -> list[dict]:
        """Get most recent artifacts from a collection."""
        return self.state.get_recent_artifacts(
            collection=collection, limit=limit, agent_id=agent_id,
        )

    def read(self, collection: str, filename: str) -> Optional[str]:
        """Read the full content of an artifact."""
        filepath = self.base_dir / collection / filename
        if filepath.exists():
            return filepath.read_text()
        return None

    def get_agent_context(self, agent_id: str, team_id: str) -> str:
        """Build context string from recent artifacts relevant to an agent."""
        parts = []

        for collection in ["research-scans", "cycle-logs", "decisions"]:
            recent = self.get_recent(collection, limit=3)
            if recent:
                parts.append(f"\n### Recent {collection}")
                for r in recent:
                    title = r.get("title") or r.get("filename", "untitled")
                    dt = r.get("created_at", "")[:10]
                    parts.append(f"- [{dt}] {title}")

        agent_output = self.get_recent("content-drafts", limit=5, agent_id=agent_id)
        if agent_output:
            parts.append(f"\n### Your Recent Output ({agent_id})")
            for d in agent_output:
                title = d.get("title") or d.get("filename", "untitled")
                parts.append(f"- [{d.get('created_at', '')[:10]}] {title}")

        return "\n".join(parts) if parts else "No prior context available."
