import ast
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class PerformanceCategory(Enum):
    ALGORITHM = "ALGORITHM"
    MEMORY = "MEMORY"
    CPU = "CPU"
    I_O = "I_O"
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    CACHING = "CACHING"
    CONCURRENCY = "CONCURRENCY"


@dataclass
class PerformanceIssue:
    category: PerformanceCategory
    severity: str
    file_path: str
    line_number: int
    function_name: str
    message: str
    current_complexity: Optional[str] = None
    recommended_complexity: Optional[str] = None
    estimated_impact: str = ""
    optimization_strategy: str = ""


class PerformanceProfiler:
    """Enterprise Performance Profiler - Detects performance issues"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]) -> Dict:
        default = {
            "max_loop_nesting": 3,
            "warn_on_list_comp_in_loop": True,
            "detect_n_plus_one": True,
            "require_caching_for_expensive_ops": True,
            "max_query_complexity": 10,
            "warn_blocking_in_async": True,
            "max_string_concat_in_loop": 5
        }

        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                default.update(yaml.safe_load(f))

        return default

    def analyze_project(self, project_path: str, language: str = "python") -> List[PerformanceIssue]:
        issues = []
        project = Path(project_path)

        for file_path in project.rglob(f"*.{language}"):
            if self._should_analyze(file_path):
                file_issues, _file_errors = self.analyze_file(file_path, language)
                issues.extend(file_issues)

        return issues

    def analyze_file(self, file_path: Path, language: str) -> tuple:
        """Analyze single file. Returns (issues, errors)."""
        issues = []
        errors = []
        content = file_path.read_text(encoding='utf-8', errors='ignore')

        if language == "python":
            try:
                tree = ast.parse(content)
                issues.extend(self._analyze_algorithms(tree, file_path, content))
                issues.extend(self._analyze_memory_patterns(tree, file_path, content))
                issues.extend(self._analyze_database_patterns(tree, file_path, content))
                issues.extend(self._analyze_caching_patterns(tree, file_path, content))
                issues.extend(self._analyze_async_patterns(tree, file_path, content))
                issues.extend(self._analyze_string_operations(tree, file_path, content))
            except SyntaxError as e:
                errors.append({"file": str(file_path), "error": str(e), "type": "SyntaxError"})

        return issues, errors

    def _analyze_algorithms(self, tree: ast.AST, file_path: Path, content: str) -> List[PerformanceIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                nesting = self._count_loop_nesting(node)
                if nesting >= 2:
                    if self._has_expensive_operation(node):
                        issues.append(PerformanceIssue(
                            category=PerformanceCategory.ALGORITHM,
                            severity="high" if nesting >= 3 else "medium",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            function_name=self._get_enclosing_function(node, tree),
                            message=f"Nested loop detected (depth: {nesting}) - potential O(n^{nesting}) complexity",
                            current_complexity=f"O(n^{nesting})",
                            recommended_complexity="O(n log n) or O(n)",
                            estimated_impact="Significant slowdown with large datasets",
                            optimization_strategy="Consider hash maps, sorting, or database-level operations"
                        ))

                if self._has_list_ops_in_loop(node):
                    issues.append(PerformanceIssue(
                        category=PerformanceCategory.ALGORITHM,
                        severity="medium",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        function_name=self._get_enclosing_function(node, tree),
                        message="List/dict operations inside loop - consider building outside loop",
                        optimization_strategy="Pre-allocate collections or use comprehensions"
                    ))

                if self._has_repeated_calls(node):
                    issues.append(PerformanceIssue(
                        category=PerformanceCategory.ALGORITHM,
                        severity="medium",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        function_name=self._get_enclosing_function(node, tree),
                        message="Repeated function calls with identical arguments in loop",
                        optimization_strategy="Cache results or hoist call outside loop"
                    ))

        return issues

    def _analyze_memory_patterns(self, tree: ast.AST, file_path: Path, content: str) -> List[PerformanceIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                if len(node.generators) > 2:
                    issues.append(PerformanceIssue(
                        category=PerformanceCategory.MEMORY,
                        severity="medium",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        function_name=self._get_enclosing_function(node, tree),
                        message="Complex nested list comprehension - high memory usage",
                        optimization_strategy="Use generator expressions or process in chunks"
                    ))

            if isinstance(node, ast.Call):
                name = self._get_call_name(node)
                if name in ['read', 'readlines'] and self._is_file_operation(node):
                    issues.append(PerformanceIssue(
                        category=PerformanceCategory.MEMORY,
                        severity="medium",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        function_name=self._get_enclosing_function(node, tree),
                        message="Loading entire file into memory",
                        optimization_strategy="Use streaming/chunked reading for large files"
                    ))

            if isinstance(node, ast.BinOp):
                if isinstance(node.op, ast.Add):
                    if self._is_string_concatenation(node):
                        issues.append(PerformanceIssue(
                            category=PerformanceCategory.MEMORY,
                            severity="low",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            function_name=self._get_enclosing_function(node, tree),
                            message="String concatenation - use join() or f-strings",
                            optimization_strategy="Use ''.join() or f-strings for better performance"
                        ))

        return issues

    def _analyze_database_patterns(self, tree: ast.AST, file_path: Path, content: str) -> List[PerformanceIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        name = self._get_call_name(child)
                        if any(q in name for q in ['query', 'filter', 'find', 'select', 'execute']):
                            issues.append(PerformanceIssue(
                                category=PerformanceCategory.DATABASE,
                                severity="critical",
                                file_path=str(file_path),
                                line_number=child.lineno,
                                function_name=self._get_enclosing_function(node, tree),
                                message="Database query inside loop - N+1 problem",
                                current_complexity="O(n) queries",
                                recommended_complexity="O(1) query with JOIN or prefetch",
                                estimated_impact="Severe performance degradation with scale",
                                optimization_strategy="Use eager loading, JOINs, or batch queries"
                            ))
                            break

                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        name = self._get_call_name(child)
                        if 'all()' in name or 'find_all' in name:
                            if not self._has_limit(child):
                                issues.append(PerformanceIssue(
                                    category=PerformanceCategory.DATABASE,
                                    severity="high",
                                    file_path=str(file_path),
                                    line_number=child.lineno,
                                    function_name=self._get_enclosing_function(node, tree),
                                    message="Unbounded database query without pagination",
                                    optimization_strategy="Add LIMIT/OFFSET or cursor-based pagination"
                                ))

        return issues

    def _analyze_caching_patterns(self, tree: ast.AST, file_path: Path, content: str) -> List[PerformanceIssue]:
        issues = []

        expensive_patterns = ['expensive_computation', 'heavy_calculation', 
                            'complex_query', 'external_api', 'fetch_data']

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if any(pattern in node.name for pattern in expensive_patterns):
                    if not self._has_caching(node):
                        issues.append(PerformanceIssue(
                            category=PerformanceCategory.CACHING,
                            severity="medium",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            function_name=node.name,
                            message=f"Potentially expensive function '{node.name}' lacks caching",
                            optimization_strategy="Add @lru_cache, @cache, or Redis caching"
                        ))

        return issues

    def _analyze_async_patterns(self, tree: ast.AST, file_path: Path, content: str) -> List[PerformanceIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        name = self._get_call_name(child)
                        blocking_ops = ['time.sleep', 'requests.get', 'requests.post',
                                       'open', 'read', 'write', 'subprocess.run']
                        if any(op in name for op in blocking_ops):
                            issues.append(PerformanceIssue(
                                category=PerformanceCategory.CONCURRENCY,
                                severity="high",
                                file_path=str(file_path),
                                line_number=child.lineno,
                                function_name=node.name,
                                message=f"Blocking operation '{name}' in async function",
                                optimization_strategy="Use async alternatives: aiohttp, aiofiles, asyncio.sleep"
                            ))

        return issues

    def _analyze_string_operations(self, tree: ast.AST, file_path: Path, content: str) -> List[PerformanceIssue]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                concat_count = self._count_string_concat_in_loop(node)
                if concat_count > self.config['max_string_concat_in_loop']:
                    issues.append(PerformanceIssue(
                        category=PerformanceCategory.ALGORITHM,
                        severity="medium",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        function_name=self._get_enclosing_function(node, tree),
                        message=f"{concat_count} string concatenations in loop",
                        optimization_strategy="Use list.append() + ''.join() or io.StringIO"
                    ))

        return issues

    def _count_loop_nesting(self, node: ast.AST, depth: int = 0) -> int:
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While)):
                max_depth = max(max_depth, self._count_loop_nesting(child, depth + 1))
            else:
                max_depth = max(max_depth, self._count_loop_nesting(child, depth))
        return max_depth

    def _has_expensive_operation(self, node: ast.AST) -> bool:
        expensive = ['query', 'filter', 'sort', 'search', 'find']
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = self._get_call_name(child)
                if any(op in name for op in expensive):
                    return True
        return False

    def _has_list_ops_in_loop(self, node: ast.AST) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr in ['append', 'extend', 'insert', 'remove']:
                        return True
        return False

    def _has_repeated_calls(self, node: ast.AST) -> bool:
        calls = {}
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = self._get_call_name(child)
                if name in calls:
                    calls[name] += 1
                else:
                    calls[name] = 1
        return any(count > 2 for count in calls.values())

    def _is_file_operation(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Call):
                if isinstance(node.func.value.func, ast.Name):
                    return node.func.value.func.id == 'open'
        return False

    def _is_string_concatenation(self, node: ast.BinOp) -> bool:
        def is_string(n):
            return isinstance(n, ast.Str) or (isinstance(n, ast.Call) and 
                   isinstance(n.func, ast.Name) and n.func.id == 'str')
        return is_string(node.left) or is_string(node.right)

    def _has_limit(self, node: ast.Call) -> bool:
        for kw in node.keywords:
            if kw.arg in ['limit', 'first', 'top']:
                return True
        return False

    def _has_caching(self, node: ast.FunctionDef) -> bool:
        cache_decorators = ['lru_cache', 'cache', 'cached', 'memoize', 'redis_cache']
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id in cache_decorators:
                    return True
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    if decorator.func.id in cache_decorators:
                        return True
        return False

    def _count_string_concat_in_loop(self, node: ast.AST) -> int:
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Add):
                if self._is_string_concatenation(child):
                    count += 1
        return count

    def _get_call_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return f"{self._get_expr_name(node.func.value)}.{node.func.attr}"
        return ""

    def _get_expr_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_expr_name(node.value)}.{node.attr}"
        return ""

    def _get_enclosing_function(self, node: ast.AST, tree: ast.AST) -> str:
        """Return the name of the innermost function that contains the given node."""
        node_lineno = getattr(node, 'lineno', -1)
        if node_lineno < 0:
            return "<module>"

        best_func = None
        best_span = float('inf')

        for func in ast.walk(tree):
            if isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_start = func.lineno
                func_end = getattr(func, 'end_lineno', func_start) or func_start

                if func_start <= node_lineno <= func_end:
                    span = func_end - func_start
                    if span < best_span:
                        best_span = span
                        best_func = func

        return best_func.name if best_func else "<module>"

    def _should_analyze(self, file_path: Path) -> bool:
        exclude = ['test_', '_test.py', 'conftest.py', '__pycache__', 
                  'venv', 'node_modules', '.git', 'migrations']
        return not any(e in str(file_path) for e in exclude)
