"""Process adapter -- spawn a CLI process as an agent.

Runs a command, pipes the brief as JSON to stdin, reads result from stdout.
Good for wrapping existing CLI tools, Python scripts, or compiled binaries.

Config example (in agent.yaml):
    runtime: process
    runtime_config:
      command: python3 my_agent.py
      cwd: /path/to/agent
      timeout: 60
      env:
        MY_VAR: value
"""

import asyncio
import json
import logging
import os
from typing import Optional

from .base import AdapterCapabilities, AdapterResult, RuntimeAdapter

logger = logging.getLogger(__name__)


class ProcessAdapter(RuntimeAdapter):
    """Spawn a CLI process, pipe brief as JSON stdin, read JSON stdout."""

    def __init__(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: float = 60.0,
        env: Optional[dict] = None,
    ):
        self.command = command
        self.cwd = cwd
        self.timeout = timeout
        self._env = env

    def _build_env(self) -> Optional[dict]:
        if not self._env:
            return None
        env = os.environ.copy()
        env.update(self._env)
        return env

    async def execute(self, brief: dict) -> AdapterResult:
        """Run the command, pipe brief as JSON to stdin, parse JSON from stdout."""
        brief_json = json.dumps(brief)

        try:
            proc = await asyncio.create_subprocess_shell(
                self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd,
                env=self._build_env(),
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=brief_json.encode()),
                timeout=self.timeout,
            )

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()[:500] or f"Process exited with code {proc.returncode}"
                logger.error("process adapter error: %s", error_msg)
                return AdapterResult(content="", error=error_msg)

            output = stdout.decode().strip()

            # Try to parse as JSON
            try:
                data = json.loads(output)
                content = (
                    data.get("content")
                    or data.get("result")
                    or data.get("output")
                    or json.dumps(data)
                )
                return AdapterResult(
                    content=content,
                    model=data.get("model", "process"),
                    metadata=data.get("metadata", {}),
                )
            except json.JSONDecodeError:
                # Plain text output is fine
                return AdapterResult(content=output, model="process")

        except asyncio.TimeoutError:
            error_msg = f"Process timed out after {self.timeout}s"
            logger.error(error_msg)
            return AdapterResult(content="", error=error_msg)

        except Exception as e:
            error_msg = f"Process adapter failed: {e}"
            logger.error(error_msg)
            return AdapterResult(content="", error=error_msg)

    async def health(self) -> bool:
        """Check if the command exists."""
        try:
            cmd = self.command.split()[0]
            proc = await asyncio.create_subprocess_shell(
                f"which {cmd}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False
