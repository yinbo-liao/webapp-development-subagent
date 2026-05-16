import ast
import math
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class StabilityIssueType(Enum):
    COMPLEXITY = "COMPLEXITY"
    ERROR_HANDLING = "ERROR_HANDLING"
    CONCURRENCY = "CONCURRENCY"
    TYPE_SAFETY = "TYPE_SAFETY"
    RESOURCE_MANAGEMENT = "RESOURCE_MANAGEMENT"


@dataclass
class StabilityIssue:
    issue_type: StabilityIssueType
    severity: str
    file_path: str
    line_number: int
    message: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    recommendation: str = ""


class StabilityAnalyzer:
    """Enterprise Stability Analyzer - Detects code stability issues"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]) -> Dict:
        default = {
            "max_cyclomatic_complexity": 10,
            "max_cognitive_complexity": 15,
            "max_function_length": 50,
            "max_nesting_depth": 4,
            "min_type_coverage": 0.8,
            "require_exception_handling": True,
            "max_class_length": 300,
            "max_file_length": 500
        }

        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                default.update(yaml.safe_load(f))

        return default

    def analyze_project(self, project_path: str, language: str = "python") -> List[StabilityIssue]:
        issues = []
        errors = []
        project = Path(project_path)

        for file_path in project.rglob(f"*.{language}"):
            if self._should_analyze(file_path):
                file_issues, file_errors = self.analyze_file(file_path, language)
                issues.extend(file_issues)
                errors.extend(file_errors)

        return issues

    def analyze_file(self, file_path: Path, language: str) -> tuple:
        """Analyze single file. Returns (issues, errors)."""
        issues = []
        errors = []
        content = file_path.read_text(encoding='utf-8', errors='ignore')

        if language == "python":
            try:
                tree = ast.parse(content)
                parent_map = self._build_parent_map(tree)
                issues.extend(self._analyze_python_complexity(tree, file_path, content))
                issues.extend(self._analyze_python_error_handling(tree, file_path, content))
                issues.extend(self._analyze_python_type_coverage(tree, file_path, content))
                issues.extend(self._analyze_python_resource_management(tree, file_path, content, parent_map))
                issues.extend(self._analyze_python_concurrency(tree, file_path, content))
            except SyntaxError as e:
                errors.append({"file": str(file_path), "error": str(e), "type": "SyntaxError"})

        lines = content.split('\n')
        if len(lines) > self.config['max_file_length']:
            issues.append(StabilityIssue(
                issue_type=StabilityIssueType.COMPLEXITY,
                severity="medium",
                file_path=str(file_path),
                line_number=1,
                message=f"File too long: {len(lines)} lines (max: {self.config['max_file_length']})",
                metric_value=len(lines),
                threshold=self.config['max_file_length'],
                recommendation="Split file into modules or extract classes/functions"
            ))

        return issues

    def _analyze_python_complexity(self, tree: ast.AST, file_path: Path, content: str) -> List[StabilityIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_cyclomatic_complexity(node)

                if complexity > self.config['max_cyclomatic_complexity']:
                    issues.append(StabilityIssue(
                        issue_type=StabilityIssueType.COMPLEXITY,
                        severity="high" if complexity > 20 else "medium",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        message=f"Function '{node.name}' has cyclomatic complexity of {complexity}",
                        metric_value=complexity,
                        threshold=self.config['max_cyclomatic_complexity'],
                        recommendation="Refactor into smaller functions, use early returns, extract logic"
                    ))

                cognitive = self._calculate_cognitive_complexity(node)
                if cognitive > self.config['max_cognitive_complexity']:
                    issues.append(StabilityIssue(
                        issue_type=StabilityIssueType.COMPLEXITY,
                        severity="medium",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        message=f"Function '{node.name}' has cognitive complexity of {cognitive}",
                        metric_value=cognitive,
                        threshold=self.config['max_cognitive_complexity'],
                        recommendation="Simplify nested conditionals, extract helper functions"
                    ))

                func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                if func_lines > self.config['max_function_length']:
                    issues.append(StabilityIssue(
                        issue_type=StabilityIssueType.COMPLEXITY,
                        severity="medium",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        message=f"Function '{node.name}' is {func_lines} lines long",
                        metric_value=func_lines,
                        threshold=self.config['max_function_length'],
                        recommendation="Extract helper functions, follow Single Responsibility Principle"
                    ))

                max_depth = self._calculate_nesting_depth(node)
                if max_depth > self.config['max_nesting_depth']:
                    issues.append(StabilityIssue(
                        issue_type=StabilityIssueType.COMPLEXITY,
                        severity="medium",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        message=f"Maximum nesting depth of {max_depth} in '{node.name}'",
                        metric_value=max_depth,
                        threshold=self.config['max_nesting_depth'],
                        recommendation="Use guard clauses, extract nested logic into functions"
                    ))

            elif isinstance(node, ast.ClassDef):
                class_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                if class_lines > self.config['max_class_length']:
                    issues.append(StabilityIssue(
                        issue_type=StabilityIssueType.COMPLEXITY,
                        severity="low",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        message=f"Class '{node.name}' is {class_lines} lines long",
                        metric_value=class_lines,
                        threshold=self.config['max_class_length'],
                        recommendation="Consider splitting into multiple classes or using composition"
                    ))

        return issues

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                 ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _calculate_cognitive_complexity(self, node: ast.AST, nesting_level: int = 0) -> int:
        complexity = 0

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1 + nesting_level
                complexity += self._calculate_cognitive_complexity(child, nesting_level + 1)
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
                for value in child.values:
                    complexity += self._calculate_cognitive_complexity(value, nesting_level)
            else:
                complexity += self._calculate_cognitive_complexity(child, nesting_level)

        return complexity

    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        max_depth = 0

        def _depth(current: ast.AST, current_depth: int):
            nonlocal max_depth
            if isinstance(current, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)

            for child in ast.iter_child_nodes(current):
                _depth(child, current_depth)

        _depth(node, 0)
        return max_depth

    def _analyze_python_error_handling(self, tree: ast.AST, file_path: Path, content: str) -> List[StabilityIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if handler.type is None:
                        issues.append(StabilityIssue(
                            issue_type=StabilityIssueType.ERROR_HANDLING,
                            severity="high",
                            file_path=str(file_path),
                            line_number=handler.lineno,
                            message="Bare 'except:' clause catches all exceptions including SystemExit and KeyboardInterrupt",
                            recommendation="Use 'except Exception:' or catch specific exceptions"
                        ))

                    if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                        issues.append(StabilityIssue(
                            issue_type=StabilityIssueType.ERROR_HANDLING,
                            severity="high",
                            file_path=str(file_path),
                            line_number=handler.lineno,
                            message="Empty except block silently swallows exceptions",
                            recommendation="Log the exception or re-raise after handling"
                        ))

                    if isinstance(handler.type, ast.Name) and handler.type.id == 'Exception':
                        has_logging = any(
                            isinstance(stmt, ast.Expr) and 
                            isinstance(stmt.value, ast.Call) and
                            self._is_logging_call(stmt.value)
                            for stmt in handler.body
                        )
                        if not has_logging:
                            issues.append(StabilityIssue(
                                issue_type=StabilityIssueType.ERROR_HANDLING,
                                severity="medium",
                                file_path=str(file_path),
                                line_number=handler.lineno,
                                message="Broad exception catch without logging",
                                recommendation="Add logging to exception handlers for observability"
                            ))

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self._has_risky_operations(node) and not self._has_exception_handling(node):
                    issues.append(StabilityIssue(
                        issue_type=StabilityIssueType.ERROR_HANDLING,
                        severity="medium",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        message=f"Function '{node.name}' performs risky operations without exception handling",
                        recommendation="Add try-except blocks for network, file, or database operations"
                    ))

        return issues

    def _is_logging_call(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id in ['logging', 'logger', 'log']
        return False

    def _has_risky_operations(self, node: ast.AST) -> bool:
        risky_calls = ['open', 'read', 'write', 'requests', 'urlopen', 
                      'connect', 'execute', 'query', 'fetch']
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = self._get_call_name(child)
                if any(risky in name for risky in risky_calls):
                    return True
        return False

    def _has_exception_handling(self, node: ast.AST) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                return True
        return False

    def _get_call_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return f"{self._get_call_name_from_expr(node.func.value)}.{node.func.attr}"
        return ""

    def _get_call_name_from_expr(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_call_name_from_expr(node.value)}.{node.attr}"
        return ""

    def _analyze_python_type_coverage(self, tree: ast.AST, file_path: Path, content: str) -> List[StabilityIssue]:
        issues = []

        total_functions = 0
        typed_functions = 0
        total_params = 0
        typed_params = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_functions += 1
                if node.returns:
                    typed_functions += 1

                for arg in node.args.args + node.args.kwonlyargs:
                    total_params += 1
                    if arg.annotation:
                        typed_params += 1

        if total_functions > 0:
            coverage = typed_functions / total_functions
            if coverage < self.config['min_type_coverage']:
                issues.append(StabilityIssue(
                    issue_type=StabilityIssueType.TYPE_SAFETY,
                    severity="medium",
                    file_path=str(file_path),
                    line_number=1,
                    message=f"Type annotation coverage: {coverage:.1%} (min: {self.config['min_type_coverage']:.0%})",
                    metric_value=coverage,
                    threshold=self.config['min_type_coverage'],
                    recommendation="Add return type annotations to all functions"
                ))

        return issues

    def _analyze_python_resource_management(self, tree: ast.AST, file_path: Path, content: str, parent_map: dict) -> List[StabilityIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    if not self._is_in_context_manager(node, parent_map):
                        issues.append(StabilityIssue(
                            issue_type=StabilityIssueType.RESOURCE_MANAGEMENT,
                            severity="high",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            message="File opened without context manager (with statement)",
                            recommendation="Use 'with open(...) as f:' to ensure proper resource cleanup"
                        ))

                name = self._get_call_name(node)
                if 'connect' in name and not self._is_in_context_manager(node, parent_map):
                    issues.append(StabilityIssue(
                        issue_type=StabilityIssueType.RESOURCE_MANAGEMENT,
                        severity="medium",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        message="Database connection may not be properly closed",
                        recommendation="Use context managers or connection pooling"
                    ))

        return issues

    def _build_parent_map(self, tree: ast.AST) -> dict:
        """Build mapping from each AST node to its parent node."""
        parent_map = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parent_map[child] = parent
        return parent_map

    def _is_in_context_manager(self, node: ast.AST, parent_map: dict) -> bool:
        """Check whether an AST node is lexically inside a 'with' statement."""
        current = node
        while current in parent_map:
            parent = parent_map[current]
            if isinstance(parent, ast.With):
                return True
            current = parent
        return False

    def _analyze_python_concurrency(self, tree: ast.AST, file_path: Path, content: str) -> List[StabilityIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                for arg in node.args.args:
                    if arg.default and isinstance(arg.default, (ast.List, ast.Dict)):
                        issues.append(StabilityIssue(
                            issue_type=StabilityIssueType.CONCURRENCY,
                            severity="high",
                            file_path=str(file_path),
                            line_number=arg.lineno,
                            message="Mutable default argument in async function can cause race conditions",
                            recommendation="Use None as default and initialize inside function"
                        ))

        return issues

    def _should_analyze(self, file_path: Path) -> bool:
        exclude = ['test_', '_test.py', 'conftest.py', '__pycache__', 
                  'venv', 'node_modules', '.git']
        return not any(e in str(file_path) for e in exclude)
