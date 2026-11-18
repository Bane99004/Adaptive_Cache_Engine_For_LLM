"""
L5 — API Dependencies

Dependency injection providers for shared CacheManager and Agent singletons.
Kept in a separate helper file per repository structure rules.
"""

from __future__ import annotations
from src.agent.agent import Agent
from src.agent.executor import ToolExecutor
from src.cache.manager import CacheManager
from src.config.cache_config import default_config

# Global application instances
_CACHE_MANAGER: CacheManager | None = None
_AGENT: Agent | None = None


def get_cache_manager() -> CacheManager:
    """Provide the application-wide CacheManager instance."""
    global _CACHE_MANAGER
    if _CACHE_MANAGER is None:
        _CACHE_MANAGER = CacheManager(default_config())
    return _CACHE_MANAGER


def get_agent() -> Agent:
    """Provide the application-wide Agent instance wired to the CacheManager."""
    global _AGENT
    if _AGENT is None:
        cache_mgr = get_cache_manager()
        executor = ToolExecutor(cache_manager=cache_mgr)
        _AGENT = Agent(executor=executor)
    return _AGENT


def reset_dependencies() -> None:
    """Reset singletons (primarily used for test isolation)."""
    global _CACHE_MANAGER, _AGENT
    _CACHE_MANAGER = None
    _AGENT = None

