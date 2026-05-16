"""Shared ECC engine — single point of access for all analysis tools.

Replaces per-agent instantiation of ECC tools with a thread-safe singleton
that supports incremental (hash-based) scanning to avoid redundant work.
"""

import hashlib
import threading
from pathlib import Path
from typing import Dict, List, Optional

from ecc_tools.security.sast_engine import SASTEngine, ScanResult
from ecc_tools.stability.static_analyzer import StabilityAnalyzer, StabilityIssue
from ecc_tools.performance.profiler import PerformanceProfiler, PerformanceIssue
from ecc_tools.maintainability.code_metrics import MaintainabilityAnalyzer


class ECCEngine:
    """Thread-safe facade over all four ECC analysis tools.

    Usage:
        engine = ECCEngine.get_instance("config")
        report = engine.full_scan("./my-app")
        result = engine.quality_gate_check("./my-app")
    """

    _instance: Optional["ECCEngine"] = None
    _lock = threading.Lock()

    def __init__(self, config_dir: str = "config"):
        self._config_dir = config_dir
        self._security = SASTEngine(f"{config_dir}/ecc.yaml")
        self._stability = StabilityAnalyzer(f"{config_dir}/ecc.yaml")
        self._performance = PerformanceProfiler(f"{config_dir}/ecc.yaml")
        self._maintainability = MaintainabilityAnalyzer(f"{config_dir}/ecc.yaml")
        self._file_hashes: Dict[str, str] = {}
        self._scan_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls, config_dir: str = "config") -> "ECCEngine":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        with cls._lock:
            cls._instance = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def full_scan(self, project_path: str, language: str = "python") -> "ECCReport":
        """Run all four analysis passes over the entire project."""
        with self._scan_lock:
            report = ECCReport(project_path=project_path)

            report.security = self._security.scan_project(project_path, language)
            report.stability = self._stability.analyze_project(project_path, language)
            report.performance = self._performance.analyze_project(project_path, language)
            report.maintainability = self._maintainability.analyze_project(project_path)

            return report

    def scan_incremental(self, project_path: str, language: str = "python") -> Optional["ECCReport"]:
        """Rescan only files whose contents have changed since last scan.

        Returns None if no files changed (everything is clean).
        """
        current_hashes = self._hash_project_files(project_path, language)

        if current_hashes == self._file_hashes:
            return None

        self._file_hashes = current_hashes
        return self.full_scan(project_path, language)

    def quality_gate_check(self, project_path: str,
                           quality_gates: Optional[Dict] = None) -> "QualityGateResult":
        """Run full scan and evaluate quality gates.

        If quality_gates is None, default thresholds are used:
          security: max_critical=0, max_high=5
          stability: max_critical=0
          performance: max_critical=0
          maintainability: min_mi=70
        """
        quality_gates = quality_gates or {
            "security": {"max_critical": 0, "max_high": 5},
            "stability": {"max_critical": 0},
            "performance": {"max_critical": 0},
            "maintainability": {"min_mi": 70},
        }

        report = self.full_scan(project_path)
        return report.evaluate_gates(quality_gates)

    def scan_single_file(self, file_path: str, language: str = "python") -> "ECCReport":
        """Run all four analyzers against a single file."""
        p = Path(file_path)
        report = ECCReport(project_path=str(p.parent))

        if not p.exists():
            return report

        report.security = self._security.scan_project(str(p.parent), language)
        report.stability, _ = self._stability.analyze_file(p, language)
        report.performance, _ = self._performance.analyze_file(p, language)
        report.maintainability, _ = self._maintainability.analyze_file(p)

        return report

    # ------------------------------------------------------------------
    # Incremental-scan helpers
    # ------------------------------------------------------------------

    def _hash_project_files(self, project_path: str, language: str) -> Dict[str, str]:
        """Compute SHA256 hashes of all scannable files in the project."""
        hashes = {}
        base = Path(project_path)
        if not base.exists():
            return hashes

        exts = {"python": [".py"], "javascript": [".js", ".jsx"],
                "typescript": [".ts", ".tsx"]}.get(language, [".py"])

        for ext in exts:
            for fp in base.rglob(f"*{ext}"):
                if self._should_scan(fp):
                    hashes[str(fp)] = hashlib.sha256(
                        fp.read_bytes()
                    ).hexdigest()
        return hashes

    @staticmethod
    def _should_scan(file_path: Path) -> bool:
        exclude = ['test_', '_test.py', 'conftest.py', '__pycache__',
                   'venv', 'node_modules', '.git', 'dist', 'build', 'migrations']
        path_str = str(file_path)
        return not any(e in path_str for e in exclude)


class ECCReport:
    """Aggregated results from a full ECC scan."""

    def __init__(self, project_path: str = ""):
        self.project_path = project_path
        self.security: Optional[ScanResult] = None
        self.stability: List[StabilityIssue] = []
        self.performance: List[PerformanceIssue] = []
        self.maintainability: List[Dict] = []

    @property
    def total_issues(self) -> int:
        sec = len(self.security.findings) if self.security else 0
        return sec + len(self.stability) + len(self.performance) + len(self.maintainability)

    def _all_findings(self) -> list:
        """Merge all findings into a single list for unified reporting."""
        all_f = []
        if self.security:
            all_f.extend(self.security.findings)
        all_f.extend(self.stability)
        all_f.extend(self.performance)
        all_f.extend(self.maintainability)
        return all_f

    def evaluate_gates(self, quality_gates: Dict) -> "QualityGateResult":
        """Evaluate quality gates against this report."""
        result = QualityGateResult()

        if self.security:
            sec_max_critical = quality_gates.get("security", {}).get("max_critical", 0)
            sec_max_high = quality_gates.get("security", {}).get("max_high", 5)
            sec_critical = self.security.critical_count
            sec_high = self.security.high_count

            result.add_check("security", sec_critical <= sec_max_critical and sec_high <= sec_max_high,
                             details={"critical": sec_critical, "high": sec_high,
                                      "max_critical": sec_max_critical, "max_high": sec_max_high},
                             failure_message=f"Security: {sec_critical} critical (max {sec_max_critical}), "
                                             f"{sec_high} high (max {sec_max_high})")

        stab_max_critical = quality_gates.get("stability", {}).get("max_critical", 0)
        stab_critical = len([i for i in self.stability if i.severity == 'critical'])
        result.add_check("stability", stab_critical <= stab_max_critical,
                         details={"critical": stab_critical, "max_critical": stab_max_critical},
                         failure_message=f"Stability: {stab_critical} critical issues")

        perf_max_critical = quality_gates.get("performance", {}).get("max_critical", 0)
        perf_critical = len([i for i in self.performance if i.severity == 'critical'])
        result.add_check("performance", perf_critical <= perf_max_critical,
                         details={"critical": perf_critical, "max_critical": perf_max_critical},
                         failure_message=f"Performance: {perf_critical} critical issues")

        maint_min_mi = quality_gates.get("maintainability", {}).get("min_mi", 70)
        maint_mi_issues = [i for i in self.maintainability
                          if 'Maintainability Index' in i.get('message', '')]
        result.add_check("maintainability", len(maint_mi_issues) == 0,
                         details={"mi_issues": len(maint_mi_issues), "min_mi": maint_min_mi},
                         failure_message=f"Maintainability: {len(maint_mi_issues)} MI violations")

        return result


class QualityGateResult:
    """Result of quality gate evaluation."""

    def __init__(self):
        self.passed = True
        self.checks: Dict[str, Dict] = {}
        self.failures: List[str] = []

    def add_check(self, name: str, passed: bool, details: Dict = None,
                  failure_message: str = ""):
        self.checks[name] = {"passed": passed, "details": details or {}}
        if not passed:
            self.passed = False
            if failure_message:
                self.failures.append(failure_message)

    def to_dict(self) -> Dict:
        return {
            "passed": self.passed,
            "checks": self.checks,
            "failures": self.failures,
        }
