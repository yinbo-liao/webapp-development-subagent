import ast
import math
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


class MaintainabilityAnalyzer:
    """Enterprise Maintainability Analyzer - Halstead metrics, code smells, SOLID principles"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]) -> Dict:
        default = {
            "min_maintainability_index": 70,
            "max_halstead_volume": 1500,
            "max_halstead_difficulty": 20,
            "max_function_count_per_class": 20,
            "max_parameter_count": 5,
            "max_return_statements": 4,
            "require_docstrings": True,
            "max_comment_ratio": 0.4,
            "min_comment_ratio": 0.05
        }

        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                default.update(yaml.safe_load(f))

        return default

    def analyze_project(self, project_path: str) -> List[Dict]:
        issues = []
        project = Path(project_path)

        for file_path in project.rglob("*.py"):
            if self._should_analyze(file_path):
                file_issues, _file_errors = self.analyze_file(file_path)
                issues.extend(file_issues)

        return issues

    def analyze_file(self, file_path: Path) -> tuple:
        """Analyze single file. Returns (issues, errors)."""
        issues = []
        errors = []
        content = file_path.read_text(encoding='utf-8', errors='ignore')

        try:
            tree = ast.parse(content)

            halstead = self._calculate_halstead(tree)
            mi = self._calculate_maintainability_index(tree, content, halstead)

            if mi < self.config['min_maintainability_index']:
                issues.append({
                    "type": "MAINTAINABILITY",
                    "severity": "medium",
                    "file": str(file_path),
                    "message": f"Maintainability Index: {mi:.1f} (min: {self.config['min_maintainability_index']})",
                    "recommendation": "Refactor complex functions, add documentation, reduce complexity"
                })

            issues.extend(self._detect_code_smells(tree, file_path, content))
            issues.extend(self._check_solid_principles(tree, file_path))
            issues.extend(self._check_documentation(tree, file_path, content))

        except SyntaxError as e:
            errors.append({"file": str(file_path), "error": str(e), "type": "SyntaxError"})

        return issues, errors

    def _calculate_halstead(self, tree: ast.AST) -> Dict:
        operators = set()
        operands = set()
        operator_count = 0
        operand_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.operator):
                operators.add(type(node).__name__)
                operator_count += 1
            elif isinstance(node, ast.Name):
                operands.add(node.id)
                operand_count += 1
            elif isinstance(node, ast.Constant):
                operands.add(str(node.value))
                operand_count += 1

        n1 = len(operators)
        n2 = len(operands)
        N1 = operator_count
        N2 = operand_count

        vocabulary = n1 + n2
        length = N1 + N2

        if vocabulary == 0:
            return {"volume": 0, "difficulty": 0, "effort": 0}

        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = difficulty * volume

        return {
            "volume": volume,
            "difficulty": difficulty,
            "effort": effort,
            "vocabulary": vocabulary,
            "length": length
        }

    def _calculate_maintainability_index(self, tree: ast.AST, content: str, halstead: Dict) -> float:
        lines = len(content.split('\n'))

        complexities = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cc = self._calculate_cyclomatic(node)
                complexities.append(cc)

        avg_cc = sum(complexities) / len(complexities) if complexities else 1

        volume = halstead.get('volume', 1)
        if volume <= 0:
            volume = 1

        mi = 171 - 5.2 * math.log(volume) - 0.23 * avg_cc - 16.2 * math.log(lines)
        return max(0, mi)

    def _calculate_cyclomatic(self, node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                               ast.With, ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _detect_code_smells(self, tree: ast.AST, file_path: Path, content: str) -> List[Dict]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_count = len(node.args.args) + len(node.args.kwonlyargs)
                if param_count > self.config['max_parameter_count']:
                    issues.append({
                        "type": "CODE_SMELL",
                        "severity": "low",
                        "file": str(file_path),
                        "line": node.lineno,
                        "message": f"Function '{node.name}' has {param_count} parameters",
                        "smell": "LONG_PARAMETER_LIST",
                        "recommendation": "Use data classes or dictionaries for related parameters"
                    })

                return_count = sum(1 for child in ast.walk(node) if isinstance(child, ast.Return))
                if return_count > self.config['max_return_statements']:
                    issues.append({
                        "type": "CODE_SMELL",
                        "severity": "low",
                        "file": str(file_path),
                        "line": node.lineno,
                        "message": f"Function '{node.name}' has {return_count} return statements",
                        "smell": "MANY_RETURN_STATEMENTS",
                        "recommendation": "Consolidate logic to reduce exit points"
                    })

            if isinstance(node, ast.ClassDef):
                method_count = len([n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
                if method_count > self.config['max_function_count_per_class']:
                    issues.append({
                        "type": "CODE_SMELL",
                        "severity": "medium",
                        "file": str(file_path),
                        "line": node.lineno,
                        "message": f"Class '{node.name}' has {method_count} methods",
                        "smell": "GOD_CLASS",
                        "recommendation": "Extract cohesive groups of methods into separate classes"
                    })

                external_calls = self._count_external_calls(node)
                if external_calls > method_count * 2:
                    issues.append({
                        "type": "CODE_SMELL",
                        "severity": "low",
                        "file": str(file_path),
                        "line": node.lineno,
                        "message": f"Class '{node.name}' may have feature envy",
                        "smell": "FEATURE_ENVY",
                        "recommendation": "Move methods to the class they interact with most"
                    })

        return issues

    def _check_solid_principles(self, tree: ast.AST, file_path: Path) -> List[Dict]:
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                responsibilities = self._analyze_responsibilities(node)
                if len(responsibilities) > 3:
                    issues.append({
                        "type": "SOLID",
                        "severity": "low",
                        "file": str(file_path),
                        "line": node.lineno,
                        "message": f"Class '{node.name}' may violate Single Responsibility Principle",
                        "principle": "SRP",
                        "recommendation": f"Split into classes handling: {', '.join(responsibilities[:3])}"
                    })

                if_chains = self._count_if_chains(node)
                if if_chains > 3:
                    issues.append({
                        "type": "SOLID",
                        "severity": "low",
                        "file": str(file_path),
                        "line": node.lineno,
                        "message": f"Class '{node.name}' has long if/elif chains - consider polymorphism",
                        "principle": "OCP",
                        "recommendation": "Use Strategy pattern or polymorphism instead of conditionals"
                    })

        return issues

    def _check_documentation(self, tree: ast.AST, file_path: Path, content: str) -> List[Dict]:
        issues = []
        total_lines = len(content.split('\n'))
        comment_lines = len([l for l in content.split('\n') if l.strip().startswith('#')])
        docstring_lines = content.count('\"\"\"') // 2 * 3

        comment_ratio = (comment_lines + docstring_lines) / total_lines if total_lines > 0 else 0

        if comment_ratio < self.config['min_comment_ratio']:
            issues.append({
                "type": "DOCUMENTATION",
                "severity": "low",
                "file": str(file_path),
                "message": f"Low comment ratio: {comment_ratio:.1%} (min: {self.config['min_comment_ratio']:.0%})",
                "recommendation": "Add docstrings and inline comments for complex logic"
            })

        if self.config['require_docstrings']:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        issues.append({
                            "type": "DOCUMENTATION",
                            "severity": "low",
                            "file": str(file_path),
                            "line": node.lineno,
                            "message": f"Missing docstring for {type(node).__name__.lower()} '{node.name}'",
                            "recommendation": "Add descriptive docstring explaining purpose and parameters"
                        })

        return issues

    def _count_external_calls(self, node: ast.ClassDef) -> int:
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    count += 1
        return count

    def _analyze_responsibilities(self, node: ast.ClassDef) -> List[str]:
        responsibilities = set()
        for method in node.body:
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = method.name.lower()
                if any(word in name for word in ['get', 'fetch', 'load', 'read']):
                    responsibilities.add("data_access")
                elif any(word in name for word in ['save', 'update', 'delete', 'create']):
                    responsibilities.add("data_modification")
                elif any(word in name for word in ['validate', 'check', 'verify']):
                    responsibilities.add("validation")
                elif any(word in name for word in ['send', 'notify', 'publish']):
                    responsibilities.add("communication")
                elif any(word in name for word in ['render', 'display', 'format']):
                    responsibilities.add("presentation")
                elif any(word in name for word in ['calculate', 'compute', 'process']):
                    responsibilities.add("computation")
        return list(responsibilities)

    def _count_if_chains(self, node: ast.AST) -> int:
        max_chain = 0
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                chain_len = 1
                current = child
                while hasattr(current, 'orelse') and current.orelse:
                    if len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                        chain_len += 1
                        current = current.orelse[0]
                    else:
                        break
                max_chain = max(max_chain, chain_len)
        return max_chain

    def _should_analyze(self, file_path: Path) -> bool:
        exclude = ['test_', '_test.py', 'conftest.py', '__pycache__', 
                  'venv', 'node_modules', '.git', 'migrations']
        return not any(e in str(file_path) for e in exclude)
