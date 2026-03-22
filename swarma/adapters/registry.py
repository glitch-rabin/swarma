"""Adapter registry -- resolves runtime type to adapter instance.

Creates the correct RuntimeAdapter based on agent config.
Caches adapter instances so they're reused across calls.
"""

import logging
import os
import re
from typing import Optional

from .base import RuntimeAdapter
from .hermes import HermesAdapter
from .http import HTTPAdapter
from .llm import LLMAdapter
from .process import ProcessAdapter

logger = logging.getLogger(__name__)


def _expand_env(value: str) -> str:
    """Expand ${VAR} in strings."""
    if isinstance(value, str) and "${" in value:
        def _replace(m):
            return os.environ.get(m.group(1), m.group(0))
        return re.sub(r"\$\{(\w+)\}", _replace, value)
    return value


class AdapterRegistry:
    """Resolves agent runtime configs to adapter instances.

    Instance-level runtime configs (from config.yaml) can define shared
    defaults. Agent-level runtime_config overrides per agent.
    """

    def __init__(self, router=None, instance_runtimes: Optional[dict] = None):
        """
        Args:
            router: ModelRouter instance (for LLM adapter)
            instance_runtimes: Runtime config from config.yaml, e.g.:
                runtimes:
                  hermes:
                    endpoint: http://localhost:3000
                    api_key: ${HERMES_API_KEY}
                  my_service:
                    type: http
                    endpoint: https://my-agent.example.com/run
        """
        self.router = router
        self._instance_runtimes = instance_runtimes or {}
        self._cache: dict[str, RuntimeAdapter] = {}

    def get_adapter(
        self,
        runtime: str = "llm",
        runtime_config: Optional[dict] = None,
    ) -> RuntimeAdapter:
        """Get or create an adapter for a given runtime type.

        Args:
            runtime: "llm", "hermes", "http", "process", or a named runtime
            runtime_config: Agent-level overrides
        """
        config = dict(runtime_config or {})

        # Check if it's a named instance runtime
        if runtime in self._instance_runtimes:
            instance_cfg = dict(self._instance_runtimes[runtime])
            runtime_type = instance_cfg.pop("type", runtime)
            instance_cfg.update(config)  # agent overrides win
            config = instance_cfg
            runtime = runtime_type

        # Build cache key from runtime + sorted config
        cache_key = f"{runtime}:{hash(frozenset(sorted(config.items())))}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        adapter = self._create_adapter(runtime, config)
        self._cache[cache_key] = adapter
        return adapter

    def _create_adapter(self, runtime: str, config: dict) -> RuntimeAdapter:
        """Create an adapter instance from runtime type and config."""
        # Expand env vars in all string config values
        config = {k: _expand_env(str(v)) if isinstance(v, str) else v for k, v in config.items()}

        if runtime == "llm":
            if not self.router:
                raise ValueError("LLM adapter requires a ModelRouter")
            return LLMAdapter(self.router)

        elif runtime == "hermes":
            return HermesAdapter(
                endpoint=config.get("endpoint", "http://localhost:3000"),
                api_key=config.get("api_key"),
                timeout=float(config.get("timeout", 300)),
            )

        elif runtime == "http":
            endpoint = config.get("endpoint")
            if not endpoint:
                raise ValueError("HTTP adapter requires an 'endpoint'")
            return HTTPAdapter(
                endpoint=endpoint,
                api_key=config.get("api_key"),
                headers=config.get("headers"),
                timeout=float(config.get("timeout", 120)),
            )

        elif runtime == "process":
            command = config.get("command")
            if not command:
                raise ValueError("Process adapter requires a 'command'")
            return ProcessAdapter(
                command=command,
                cwd=config.get("cwd"),
                timeout=float(config.get("timeout", 60)),
                env=config.get("env"),
            )

        else:
            raise ValueError(
                f"Unknown runtime: '{runtime}'. "
                f"Available: llm, hermes, http, process"
            )

    async def close_all(self):
        """Close all cached adapters."""
        for adapter in self._cache.values():
            try:
                await adapter.close()
            except Exception as e:
                logger.warning("error closing adapter: %s", e)
        self._cache.clear()
