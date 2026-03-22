"""Heartbeat -- event-driven task queue for inter-agent coordination.

Events create queue entries, the heartbeat loop dispatches them to agents.
No hardcoded routing -- event targets are specified at emit time or
configured in team flow definitions.
"""

import asyncio
import logging
from typing import Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

POLL_INTERVAL = 60  # seconds

# Priority levels (lower = more urgent)
PRIORITY_URGENT = 1
PRIORITY_HIGH = 2
PRIORITY_NORMAL = 3
PRIORITY_LOW = 4


class Heartbeat:
    """Event-driven queue processor that dispatches work to agents."""

    def __init__(self, state_db, dispatch_fn: Callable[..., Awaitable]):
        """
        Args:
            state_db: StateDB instance for queue operations
            dispatch_fn: async function(agent_key, context) to run an agent
        """
        self.state = state_db
        self.dispatch = dispatch_fn
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def emit(
        self,
        event_type: str,
        team_id: str,
        context: Optional[dict] = None,
        target_agents: Optional[list[str]] = None,
        priority: int = PRIORITY_NORMAL,
    ) -> list[int]:
        """Emit an event into the queue.

        target_agents must be provided -- no hardcoded routing table.
        Returns list of created task IDs.
        """
        if not target_agents:
            logger.warning("emit(%s) with no target_agents, nothing queued", event_type)
            return []

        task_ids = []
        for agent_id in target_agents:
            task_id = self.state.enqueue_task(
                event_type=event_type,
                agent_id=agent_id,
                team_id=team_id,
                context=context,
                priority=priority,
            )
            task_ids.append(task_id)
            logger.info(
                "queued: %s -> %s/%s (priority %d, task %d)",
                event_type, team_id, agent_id, priority, task_id,
            )

        return task_ids

    async def process_queue(self) -> int:
        """Process all pending tasks in priority order.

        Returns number of tasks processed.
        """
        tasks = self.state.get_pending_tasks()
        processed = 0

        for task in tasks:
            agent_key = f"{task['team_id']}/{task['agent_id']}"
            event_type = task["event_type"]
            context = task.get("context")

            logger.info("heartbeat: dispatching %s -> %s (task %d)", event_type, agent_key, task["id"])
            self.state.update_task_status(task["id"], "processing")

            try:
                result = await self.dispatch(agent_key, context)
                self.state.update_task_status(
                    task["id"], "completed",
                    result_summary=str(result)[:500] if result else None,
                )
                processed += 1
            except Exception as e:
                self.state.update_task_status(task["id"], "failed", error=str(e))
                logger.error("heartbeat: failed %s -> %s: %s", event_type, agent_key, e)

        return processed

    async def _loop(self):
        """Main heartbeat loop."""
        logger.info("heartbeat started (poll every %ds)", POLL_INTERVAL)
        while self._running:
            try:
                processed = await self.process_queue()
                if processed > 0:
                    logger.info("heartbeat: processed %d tasks", processed)
            except Exception as e:
                logger.error("heartbeat loop error: %s", e)
            await asyncio.sleep(POLL_INTERVAL)
        logger.info("heartbeat stopped")

    def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    def get_queue_status(self) -> dict:
        return self.state.get_queue_stats()
