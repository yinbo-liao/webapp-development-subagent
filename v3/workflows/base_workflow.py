"""Abstract base workflow that reads YAML definitions and executes phases."""

from pathlib import Path
from typing import Dict, List, Optional
import yaml
from dataclasses import dataclass, field


@dataclass
class WorkflowPhase:
    name: str
    agent: str
    action: str
    depends_on: List[str] = field(default_factory=list)
    parallel: Optional[List[Dict]] = None
    on_failure: str = "block"
    timeout_seconds: int = 300


@dataclass
class WorkflowDefinition:
    name: str
    version: str
    description: str
    phases: List[WorkflowPhase] = field(default_factory=list)
    quality_gates: Dict = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "WorkflowDefinition":
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        phases = []
        for p in data.get("phases", []):
            parallel = None
            if "parallel" in p:
                parallel = [
                    {"agent": pa["agent"], "action": pa.get("action", "execute"),
                     "input": pa.get("input", "all")}
                    for pa in p["parallel"]
                ]
            phases.append(WorkflowPhase(
                name=p["name"],
                agent=p.get("agent", "orchestrator"),
                action=p.get("action", "execute"),
                depends_on=p.get("depends_on", []),
                parallel=parallel,
                on_failure=p.get("on_failure", "block"),
                timeout_seconds=p.get("timeout_seconds", 300),
            ))

        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            phases=phases,
            quality_gates=data.get("quality_gates", {}),
        )

    def get_phase_order(self) -> List[str]:
        """Return phases in dependency order (topological sort)."""
        visited = set()
        order = []

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            phase = self.get_phase(name)
            if phase:
                for dep in phase.depends_on:
                    visit(dep)
            order.append(name)

        for phase in self.phases:
            visit(phase.name)

        return order

    def get_phase(self, name: str) -> Optional[WorkflowPhase]:
        for p in self.phases:
            if p.name == name:
                return p
        return None

    def validate(self, available_agents: List[str]) -> List[str]:
        """Validate workflow: check agents exist, no cycles in dependencies."""
        errors = []

        valid_agents = set(available_agents) | {"orchestrator"}
        for phase in self.phases:
            if phase.agent not in valid_agents:
                errors.append(f"Phase '{phase.name}': agent '{phase.agent}' not found")
            if phase.parallel:
                for pa in phase.parallel:
                    if pa["agent"] not in valid_agents:
                        errors.append(
                            f"Phase '{phase.name}' parallel: agent '{pa['agent']}' not found"
                        )

        # Simple cycle detection via DFS
        phase_map = {p.name: p for p in self.phases}
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {p.name: WHITE for p in self.phases}

        def dfs(name: str) -> bool:
            color[name] = GRAY
            phase = phase_map.get(name)
            if phase:
                for dep in phase.depends_on:
                    if color.get(dep) == GRAY:
                        errors.append(f"Cycle detected: {name} -> {dep}")
                        return False
                    if color.get(dep) == WHITE:
                        if not dfs(dep):
                            return False
            color[name] = BLACK
            return True

        for p in self.phases:
            if color[p.name] == WHITE:
                dfs(p.name)

        return errors
