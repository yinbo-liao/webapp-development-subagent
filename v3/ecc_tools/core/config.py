from pathlib import Path
from typing import Dict, List, Optional
import yaml


class ECCConfig:
    """Unified ECC configuration loaded from YAML files.

    Merges config/agents.yaml and config/ecc.yaml with defaults.
    Provides single access point for all ECC tool thresholds.
    """

    _instance: Optional["ECCConfig"] = None

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._data: Dict = {}
        self._load()

    def _load(self):
        """Load and merge all configuration files."""
        default = self._defaults()

        agents_path = self.config_dir / "agents.yaml"
        if agents_path.exists():
            with open(agents_path, "r") as f:
                agents_cfg = yaml.safe_load(f) or {}
                self._deep_merge(default, agents_cfg)

        ecc_path = self.config_dir / "ecc.yaml"
        if ecc_path.exists():
            with open(ecc_path, "r") as f:
                ecc_cfg = yaml.safe_load(f) or {}
                self._deep_merge(default, ecc_cfg)

        self._data = default

    @staticmethod
    def _defaults() -> Dict:
        return {
            "agents": {
                "frontend": {"enabled": True, "priority": 2, "ecc_validation": True},
                "backend": {"enabled": True, "priority": 2, "ecc_validation": True},
                "database": {"enabled": True, "priority": 2, "ecc_validation": True},
                "qa": {"enabled": True, "priority": 3, "ecc_validation": True},
                "devops": {"enabled": True, "priority": 3, "ecc_validation": True},
            },
            "quality_gates": {
                "security": {"max_critical": 0, "max_high": 5, "block_on_failure": True},
                "stability": {"max_critical": 0, "block_on_failure": True},
                "performance": {"max_critical": 0, "block_on_failure": True},
                "maintainability": {"min_mi": 70, "block_on_failure": False},
            },
            "ecc": {
                "security": {
                    "max_file_size_kb": 500,
                    "severity_threshold": "MEDIUM",
                    "enable_taint_analysis": True,
                    "enable_dataflow_analysis": True,
                    "exclude_patterns": [
                        "*.min.js", "*.bundle.js", "node_modules/*",
                        "venv/*", ".git/*", "dist/*", "build/*",
                    ],
                },
                "stability": {
                    "max_cyclomatic_complexity": 10,
                    "max_cognitive_complexity": 15,
                    "max_function_length": 50,
                    "max_nesting_depth": 4,
                    "max_class_length": 300,
                    "max_file_length": 500,
                    "min_type_coverage": 0.8,
                },
                "performance": {
                    "max_loop_nesting": 3,
                    "detect_n_plus_one": True,
                    "require_caching_for_expensive_ops": True,
                    "warn_blocking_in_async": True,
                    "max_string_concat_in_loop": 5,
                },
                "maintainability": {
                    "min_maintainability_index": 70,
                    "max_halstead_volume": 1500,
                    "max_halstead_difficulty": 20,
                    "max_parameter_count": 5,
                    "max_return_statements": 4,
                    "max_function_count_per_class": 20,
                    "require_docstrings": True,
                    "min_comment_ratio": 0.05,
                    "max_comment_ratio": 0.4,
                },
            },
            "logging": {
                "level": "INFO",
            },
        }

    @staticmethod
    def _deep_merge(base: Dict, override: Dict):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ECCConfig._deep_merge(base[key], value)
            else:
                base[key] = value

    @classmethod
    def get_instance(cls, config_dir: str = "config") -> "ECCConfig":
        if cls._instance is None:
            cls._instance = cls(config_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def get(self, *keys: str, default=None):
        """Get a nested config value by key path."""
        node = self._data
        for key in keys:
            if isinstance(node, dict):
                node = node.get(key)
            else:
                return default
            if node is None:
                return default
        return node

    @property
    def quality_gates(self) -> Dict:
        return self._data.get("quality_gates", {})

    @property
    def security_config(self) -> Dict:
        return self._data.get("ecc", {}).get("security", {})

    @property
    def stability_config(self) -> Dict:
        return self._data.get("ecc", {}).get("stability", {})

    @property
    def performance_config(self) -> Dict:
        return self._data.get("ecc", {}).get("performance", {})

    @property
    def maintainability_config(self) -> Dict:
        return self._data.get("ecc", {}).get("maintainability", {})

    def get_quality_gate(self, gate_name: str) -> Dict:
        return self.quality_gates.get(gate_name, {})

    def is_agent_enabled(self, agent_name: str) -> bool:
        return self._data.get("agents", {}).get(agent_name, {}).get("enabled", True)
