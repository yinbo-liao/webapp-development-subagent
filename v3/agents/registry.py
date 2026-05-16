"""Agent registry — config-driven discovery and instantiation.

Loads agent configuration from config/agents.yaml, discovers agent
implementations, and provides a single dict of ready-to-use agents.
"""

import importlib
from typing import Dict, Optional

from ecc_tools.core.engine import ECCEngine


# Maps agent config names to their module paths
_AGENT_MODULES: Dict[str, str] = {
    "frontend": "agents.frontend_agent.agent",
    "backend": "agents.backend_agent.agent",
    "database": "agents.database_agent.agent",
    "qa": "agents.qa_agent.agent",
    "devops": "agents.devops_agent.agent",
}


class AgentRegistry(dict):
    """Lazy-loaded registry of agent instances keyed by agent type name.

    Usage:
        registry = AgentRegistry(ecc=ECCEngine.get_instance("config"))
        frontend = registry["frontend"]
        backend = registry["backend"]
    """

    def __init__(
        self,
        config: Dict = None,
        ecc: Optional[ECCEngine] = None,
        enabled_only: bool = True,
    ):
        super().__init__()
        self._config = config or {}
        self._ecc = ecc or ECCEngine.get_instance("config")
        self._enabled_only = enabled_only

    def __getitem__(self, key: str):
        if key not in self:
            self._load_agent(key)
        return super().__getitem__(key)

    def __contains__(self, key: str):
        if key not in self and key in _AGENT_MODULES:
            try:
                self._load_agent(key)
                return True
            except Exception:
                return False
        return super().__contains__(key)

    def discover_all(self) -> Dict:
        """Load and return all registered agents."""
        for name in _AGENT_MODULES:
            agent_cfg = self._get_agent_config(name)
            if not self._enabled_only or agent_cfg.get("enabled", True):
                if name not in self:
                    try:
                        self._load_agent(name)
                    except Exception:
                        pass
        return dict(self)

    def _load_agent(self, name: str):
        """Dynamically import and instantiate an agent by name."""
        if name not in _AGENT_MODULES:
            raise KeyError(f"Unknown agent: {name}")

        module_path = _AGENT_MODULES[name]
        try:
            module = importlib.import_module(module_path)
            agent_cls = self._find_agent_class(module, name)
            agent_cfg = self._get_agent_config(name)
            instance = agent_cls(config=agent_cfg, ecc=self._ecc)
            self[name] = instance
        except ImportError as e:
            raise RuntimeError(
                f"Failed to load agent '{name}' from {module_path}: {e}"
            ) from e

    def _get_agent_config(self, name: str) -> Dict:
        """Get agent-specific config from the merged YAML config."""
        return self._config.get("agents", {}).get(name, {})

    @staticmethod
    def _find_agent_class(module, agent_name: str):
        """Find the agent class in a module by naming convention."""
        candidates = [
            f"{agent_name.title()}Agent",
            f"{agent_name.capitalize()}Agent",
            "Agent",
        ]
        for candidate in candidates:
            if hasattr(module, candidate):
                return getattr(module, candidate)

        # Fallback: find first class whose name ends with 'Agent'
        for attr_name in dir(module):
            if attr_name.endswith("Agent") and not attr_name.startswith("_"):
                return getattr(module, attr_name)

        raise AttributeError(
            f"No agent class found in {module.__name__}"
        )
