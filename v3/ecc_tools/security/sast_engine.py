import ast
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from datetime import datetime


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Confidence(Enum):
    CERTAIN = "CERTAIN"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class SecurityFinding:
    rule_id: str
    rule_name: str
    severity: Severity
    confidence: Confidence
    file_path: str
    line_number: int
    column: int
    message: str
    code_snippet: str
    remediation: str
    owasp_mapping: List[str] = field(default_factory=list)
    cwe_id: Optional[str] = None
    hash: str = field(default="")

    def __post_init__(self):
        if not self.hash:
            content = f"{self.rule_id}:{self.file_path}:{self.line_number}:{self.code_snippet}"
            self.hash = hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class ScanError:
    file_path: str
    error: str
    error_type: str = "scan_error"

@dataclass
class ScanResult:
    findings: List[SecurityFinding] = field(default_factory=list)
    files_scanned: int = 0
    lines_scanned: int = 0
    scan_duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    parse_errors: List[ScanError] = field(default_factory=list)
    scan_errors: List[ScanError] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def error_count(self) -> int:
        return len(self.parse_errors) + len(self.scan_errors)


class SASTEngine:
    """Enterprise Static Application Security Testing Engine"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self._ast_cache: Dict[str, ast.AST] = {}

    def _load_config(self, config_path: Optional[str]) -> Dict:
        default_config = {
            "max_file_size_kb": 500,
            "exclude_patterns": [
                "*.min.js", "*.bundle.js", "node_modules/*", 
                "venv/*", ".git/*", "dist/*", "build/*"
            ],
            "severity_threshold": "MEDIUM",
            "enable_taint_analysis": True,
            "enable_dataflow_analysis": True,
        }

        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    def scan_project(self, project_path: str, language: Optional[str] = None) -> ScanResult:
        import time
        start_time = time.time()

        project = Path(project_path)
        if not project.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")

        result = ScanResult()
        files_to_scan = self._get_files_to_scan(project, language)

        for file_path in files_to_scan:
            try:
                findings, parse_errs, scan_errs = self._scan_file(file_path)
                result.findings.extend(findings)
                result.parse_errors.extend(parse_errs)
                result.scan_errors.extend(scan_errs)
                result.files_scanned += 1

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    result.lines_scanned += len(f.readlines())

            except Exception as e:
                result.scan_errors.append(ScanError(
                    file_path=str(file_path),
                    error=str(e),
                    error_type=type(e).__name__,
                ))

        result.scan_duration_ms = (time.time() - start_time) * 1000
        return result

    def _get_files_to_scan(self, project: Path, language: Optional[str]) -> List[Path]:
        files = []
        extensions = self._get_extensions(language)

        for ext in extensions:
            for file_path in project.rglob(f"*.{ext}"):
                if not self._should_exclude(file_path):
                    if file_path.stat().st_size <= self.config['max_file_size_kb'] * 1024:
                        files.append(file_path)

        return files

    def _get_extensions(self, language: Optional[str]) -> List[str]:
        lang_map = {
            'python': ['py'],
            'javascript': ['js', 'jsx'],
            'typescript': ['ts', 'tsx'],
            'sql': ['sql'],
            'java': ['java'],
            'go': ['go'],
            'rust': ['rs']
        }

        if language:
            return lang_map.get(language, [])
        return [ext for exts in lang_map.values() for ext in exts]

    def _should_exclude(self, file_path: Path) -> bool:
        path_str = str(file_path)
        for pattern in self.config['exclude_patterns']:
            if self._match_pattern(path_str, pattern):
                return True
        return False

    def _match_pattern(self, path: str, pattern: str) -> bool:
        import fnmatch
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, f"*/{pattern}")

    def _scan_file(self, file_path: Path) -> tuple:
        """Scan a single file. Returns (findings, parse_errors, scan_errors)."""
        findings = []
        parse_errors = []
        scan_errors = []
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        suffix = file_path.suffix.lower()

        if suffix in ['.py']:
            py_findings, py_errors = self._scan_python_file(file_path, content)
            findings.extend(py_findings)
            parse_errors.extend(py_errors)
        elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
            findings.extend(self._scan_js_file(file_path, content))
        elif suffix in ['.sql']:
            findings.extend(self._scan_sql_file(file_path, content))

        findings.extend(self._scan_patterns(file_path, content))
        return findings, parse_errors, scan_errors

    def _scan_python_file(self, file_path: Path, content: str) -> tuple:
        """Scan a Python file. Returns (findings, parse_errors)."""
        findings = []
        parse_errors = []
        try:
            tree = ast.parse(content)
            self._ast_cache[str(file_path)] = tree

            findings.extend(self._detect_sql_injection_python(tree, file_path, content))
            findings.extend(self._detect_command_injection_python(tree, file_path, content))
            findings.extend(self._detect_path_traversal_python(tree, file_path, content))
            findings.extend(self._detect_hardcoded_secrets_python(tree, file_path, content))
            findings.extend(self._detect_insecure_deserialization_python(tree, file_path, content))
            findings.extend(self._detect_ssrf_python(tree, file_path, content))

            if self.config['enable_taint_analysis']:
                findings.extend(self._taint_analysis_python(tree, file_path, content))
        except SyntaxError as e:
            parse_errors.append(ScanError(
                file_path=str(file_path),
                error=f"SyntaxError: {e}",
                error_type="SyntaxError",
            ))
        return findings, parse_errors

    def _contains_string_formatting(self, node: ast.AST) -> bool:
        if isinstance(node, (ast.JoinedStr, ast.BinOp)):
            return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ['format', 'replace']:
                    return True
            if isinstance(node.func, ast.Name):
                if node.func.id in ['f', 'format']:
                    return True
        return False

    def _get_function_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._get_function_name(node.value)}.{node.attr}"
        return ""

    def _is_user_controlled(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id in ['request', 'input', 'args', 'kwargs', 'params']
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                return node.value.id in ['request', 'flask', 'django']
        if isinstance(node, ast.Subscript):
            return self._is_user_controlled(node.value)
        return False

    def _is_tainted(self, node: ast.AST, taint_sources: set) -> bool:
        if isinstance(node, ast.Name):
            return node.id in taint_sources
        if isinstance(node, ast.BinOp):
            return self._is_tainted(node.left, taint_sources) or self._is_tainted(node.right, taint_sources)
        if isinstance(node, ast.JoinedStr):
            return any(self._is_tainted(v, taint_sources) for v in node.values)
        return False

    def _detect_sql_injection_python(self, tree: ast.AST, file_path: Path, content: str) -> List[SecurityFinding]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr in ['execute', 'executemany', 'raw']):
                    if node.args:
                        first_arg = node.args[0]
                        if self._contains_string_formatting(first_arg):
                            finding = SecurityFinding(
                                rule_id="PY-SQL-001",
                                rule_name="SQL Injection via String Formatting",
                                severity=Severity.CRITICAL,
                                confidence=Confidence.HIGH,
                                file_path=str(file_path),
                                line_number=getattr(node, 'lineno', 0),
                                column=getattr(node, 'col_offset', 0),
                                message="Potential SQL injection: User input used in SQL query via string formatting",
                                code_snippet=ast.get_source_segment(content, node) or "",
                                remediation="Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                                owasp_mapping=["A03:2021 – Injection"],
                                cwe_id="CWE-89"
                            )
                            findings.append(finding)
        return findings

    def _detect_command_injection_python(self, tree: ast.AST, file_path: Path, content: str) -> List[SecurityFinding]:
        findings = []
        dangerous_functions = ['os.system', 'os.popen', 'subprocess.call', 
                              'subprocess.Popen', 'subprocess.run', 'eval', 'exec']
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name in dangerous_functions:
                    if any(self._is_user_controlled(arg) for arg in node.args):
                        finding = SecurityFinding(
                            rule_id="PY-CMD-001",
                            rule_name="Command Injection",
                            severity=Severity.CRITICAL,
                            confidence=Confidence.HIGH,
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column=node.col_offset,
                            message=f"Potential command injection in {func_name} with user-controlled input",
                            code_snippet=ast.get_source_segment(content, node) or "",
                            remediation="Use subprocess with shell=False and pass arguments as list",
                            owasp_mapping=["A03:2021 – Injection"],
                            cwe_id="CWE-78"
                        )
                        findings.append(finding)
        return findings

    def _detect_path_traversal_python(self, tree: ast.AST, file_path: Path, content: str) -> List[SecurityFinding]:
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name in ['open', 'os.path.join', 'os.path.abspath']:
                    if any(self._is_user_controlled(arg) for arg in node.args):
                        finding = SecurityFinding(
                            rule_id="PY-PTH-001",
                            rule_name="Path Traversal",
                            severity=Severity.HIGH,
                            confidence=Confidence.MEDIUM,
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column=node.col_offset,
                            message="Potential path traversal with user-controlled input",
                            code_snippet=ast.get_source_segment(content, node) or "",
                            remediation="Validate and sanitize file paths using pathlib.Path.resolve()",
                            owasp_mapping=["A01:2021 – Broken Access Control"],
                            cwe_id="CWE-22"
                        )
                        findings.append(finding)
        return findings

    def _detect_hardcoded_secrets_python(self, tree: ast.AST, file_path: Path, content: str) -> List[SecurityFinding]:
        findings = []
        secret_patterns = [
            (r'(?i)(password|passwd|pwd)\s*=\s*["\'](?!.*\{\{).+?["\']', "Hardcoded Password", "CWE-798"),
            (r'(?i)(api[_-]?key|apikey)\s*=\s*["\'](?!.*\{\{).+?["\']', "Hardcoded API Key", "CWE-798"),
            (r'(?i)(secret[_-]?key|secretkey)\s*=\s*["\'](?!.*\{\{).+?["\']', "Hardcoded Secret Key", "CWE-798"),
            (r'sk-[a-zA-Z0-9]{48}', "OpenAI API Key", "CWE-798"),
            (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token", "CWE-798"),
            (r'private_key\s*=\s*["\']-----BEGIN', "Hardcoded Private Key", "CWE-798"),
        ]
        for pattern, name, cwe in secret_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                finding = SecurityFinding(
                    rule_id=f"PY-SEC-{cwe}",
                    rule_name=f"Hardcoded {name}",
                    severity=Severity.HIGH,
                    confidence=Confidence.MEDIUM,
                    file_path=str(file_path),
                    line_number=line_num,
                    column=match.start() - content.rfind('\n', 0, match.start()),
                    message=f"Hardcoded {name.lower()} detected. Use environment variables or secret management.",
                    code_snippet=match.group()[:100],
                    remediation="Use environment variables: os.environ.get('SECRET_KEY') or a secret manager",
                    owasp_mapping=["A07:2021 – Identification and Authentication Failures"],
                    cwe_id=cwe
                )
                findings.append(finding)
        return findings

    def _detect_insecure_deserialization_python(self, tree: ast.AST, file_path: Path, content: str) -> List[SecurityFinding]:
        findings = []
        dangerous = ['pickle.loads', 'yaml.load', 'marshal.loads', 'eval']
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name in dangerous:
                    finding = SecurityFinding(
                        rule_id="PY-DES-001",
                        rule_name="Insecure Deserialization",
                        severity=Severity.CRITICAL,
                        confidence=Confidence.HIGH,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column=node.col_offset,
                        message=f"Insecure deserialization using {func_name}",
                        code_snippet=ast.get_source_segment(content, node) or "",
                        remediation="Use safe alternatives: json.loads(), yaml.safe_load()",
                        owasp_mapping=["A08:2021 – Software and Data Integrity Failures"],
                        cwe_id="CWE-502"
                    )
                    findings.append(finding)
        return findings

    def _detect_ssrf_python(self, tree: ast.AST, file_path: Path, content: str) -> List[SecurityFinding]:
        findings = []
        http_libs = ['requests.get', 'requests.post', 'urllib.request.urlopen',
                    'http.client.HTTPConnection', 'httpx.get', 'httpx.post']
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name in http_libs:
                    if any(self._is_user_controlled(arg) for arg in node.args):
                        finding = SecurityFinding(
                            rule_id="PY-SSRF-001",
                            rule_name="Server-Side Request Forgery (SSRF)",
                            severity=Severity.HIGH,
                            confidence=Confidence.MEDIUM,
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column=node.col_offset,
                            message="Potential SSRF: User-controlled URL in HTTP request",
                            code_snippet=ast.get_source_segment(content, node) or "",
                            remediation="Validate URLs against allowlist, block internal IPs",
                            owasp_mapping=["A10:2021 – Server-Side Request Forgery (SSRF)"],
                            cwe_id="CWE-918"
                        )
                        findings.append(finding)
        return findings

    def _taint_analysis_python(self, tree: ast.AST, file_path: Path, content: str) -> List[SecurityFinding]:
        findings = []
        taint_sources = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name in ['input', 'request.args.get', 'request.form.get',
                               'request.json.get', 'request.headers.get']:
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                taint_sources.add(target.id)

        taint_sinks = ['execute', 'system', 'eval', 'open', 'urlopen']
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if any(sink in func_name for sink in taint_sinks):
                    for arg in node.args:
                        if self._is_tainted(arg, taint_sources):
                            finding = SecurityFinding(
                                rule_id="PY-TAINT-001",
                                rule_name="Tainted Data Flow",
                                severity=Severity.HIGH,
                                confidence=Confidence.MEDIUM,
                                file_path=str(file_path),
                                line_number=node.lineno,
                                column=node.col_offset,
                                message=f"User-controlled data reaches dangerous sink: {func_name}",
                                code_snippet=ast.get_source_segment(content, node) or "",
                                remediation="Validate and sanitize all user inputs before use",
                                owasp_mapping=["A03:2021 – Injection"],
                                cwe_id="CWE-20"
                            )
                            findings.append(finding)
        return findings

    def _scan_js_file(self, file_path: Path, content: str) -> List[SecurityFinding]:
        findings = []
        for match in re.finditer(r'\beval\s*\(', content):
            line_num = content[:match.start()].count('\n') + 1
            finding = SecurityFinding(
                rule_id="JS-EVAL-001",
                rule_name="Dangerous eval() Usage",
                severity=Severity.CRITICAL,
                confidence=Confidence.HIGH,
                file_path=str(file_path),
                line_number=line_num,
                column=match.start(),
                message="Use of eval() can lead to code injection",
                code_snippet=content[match.start():match.start()+50],
                remediation="Use JSON.parse() for data parsing or safer alternatives",
                owasp_mapping=["A03:2021 – Injection"],
                cwe_id="CWE-95"
            )
            findings.append(finding)

        for match in re.finditer(r'\.innerHTML\s*=', content):
            line_num = content[:match.start()].count('\n') + 1
            finding = SecurityFinding(
                rule_id="JS-XSS-001",
                rule_name="DOM XSS via innerHTML",
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                file_path=str(file_path),
                line_number=line_num,
                column=match.start(),
                message="innerHTML assignment can lead to XSS if user input is used",
                code_snippet=content[match.start():match.start()+50],
                remediation="Use textContent or DOMPurify for sanitization",
                owasp_mapping=["A03:2021 – Injection"],
                cwe_id="CWE-79"
            )
            findings.append(finding)
        return findings

    def _scan_sql_file(self, file_path: Path, content: str) -> List[SecurityFinding]:
        findings = []
        dangerous_patterns = [
            (r'\bEXEC\s*\(\s*@', "Dynamic SQL Execution", "CWE-89"),
            (r'\bsp_executesql\s+@', "Dynamic SQL via sp_executesql", "CWE-89"),
            (r'\bxp_cmdshell\b', "Dangerous xp_cmdshell", "CWE-78"),
        ]
        for pattern, name, cwe in dangerous_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[:match.start()].count('\n') + 1
                finding = SecurityFinding(
                    rule_id=f"SQL-DYN-{cwe}",
                    rule_name=name,
                    severity=Severity.HIGH,
                    confidence=Confidence.MEDIUM,
                    file_path=str(file_path),
                    line_number=line_num,
                    column=match.start(),
                    message=f"Dangerous SQL pattern detected: {name}",
                    code_snippet=content[match.start():match.start()+50],
                    remediation="Use parameterized queries and avoid dynamic SQL",
                    owasp_mapping=["A03:2021 – Injection"],
                    cwe_id=cwe
                )
                findings.append(finding)
        return findings

    def _scan_patterns(self, file_path: Path, content: str) -> List[SecurityFinding]:
        findings = []
        secret_patterns = [
            (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded Password", "CWE-798"),
            (r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded API Key", "CWE-798"),
            (r'(?i)(secret[_-]?key|secretkey)\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded Secret Key", "CWE-798"),
            (r'sk-[a-zA-Z0-9]{48}', "OpenAI API Key", "CWE-798"),
            (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token", "CWE-798"),
        ]
        for pattern, name, cwe in secret_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                finding = SecurityFinding(
                    rule_id=f"GEN-SEC-{cwe}",
                    rule_name=f"Hardcoded {name}",
                    severity=Severity.HIGH,
                    confidence=Confidence.MEDIUM,
                    file_path=str(file_path),
                    line_number=line_num,
                    column=match.start() - content.rfind('\n', 0, match.start()),
                    message=f"Potential hardcoded {name.lower()} detected",
                    code_snippet=match.group()[:100],
                    remediation="Move secrets to environment variables or use a secret manager",
                    owasp_mapping=["A07:2021 – Identification and Authentication Failures"],
                    cwe_id=cwe
                )
                findings.append(finding)
        return findings

    def generate_report(self, result: ScanResult, format: str = "sarif") -> str:
        if format == "sarif":
            return self._generate_sarif(result)
        elif format == "json":
            return self._generate_json(result)
        elif format == "html":
            return self._generate_html(result)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_sarif(self, result: ScanResult) -> str:
        import json
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {"driver": {"name": "ECC-SAST", "version": "1.0.0"}},
                "results": []
            }]
        }
        for finding in result.findings:
            sarif["runs"][0]["results"].append({
                "ruleId": finding.rule_id,
                "message": {"text": finding.message},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": finding.file_path},
                        "region": {
                            "startLine": finding.line_number,
                            "startColumn": finding.column,
                            "snippet": {"text": finding.code_snippet}
                        }
                    }
                }],
                "properties": {
                    "severity": finding.severity.value,
                    "remediation": finding.remediation,
                    "owasp": finding.owasp_mapping,
                    "cwe": finding.cwe_id
                }
            })
        return json.dumps(sarif, indent=2)

    def _generate_json(self, result: ScanResult) -> str:
        import json
        return json.dumps({
            "summary": {
                "files_scanned": result.files_scanned,
                "lines_scanned": result.lines_scanned,
                "total_findings": len(result.findings),
                "critical": result.critical_count,
                "high": result.high_count,
                "scan_duration_ms": result.scan_duration_ms
            },
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "severity": f.severity.value,
                    "file": f.file_path,
                    "line": f.line_number,
                    "message": f.message,
                    "remediation": f.remediation,
                    "cwe": f.cwe_id
                }
                for f in result.findings
            ]
        }, indent=2)

    def _generate_html(self, result: ScanResult) -> str:
        findings_html = ""
        for f in result.findings:
            color = {"CRITICAL": "#dc3545", "HIGH": "#fd7e14", "MEDIUM": "#ffc107", 
                    "LOW": "#17a2b8", "INFO": "#6c757d"}.get(f.severity.value, "#6c757d")
            findings_html += f"""
            <div style="border-left: 4px solid {color}; margin: 10px 0; padding: 10px; background: #f8f9fa;">
                <h4>{f.rule_name} <span style="color: {color};">[{f.severity.value}]</span></h4>
                <p><strong>File:</strong> {f.file_path}:{f.line_number}</p>
                <p><strong>Message:</strong> {f.message}</p>
                <pre style="background: #e9ecef; padding: 8px; border-radius: 4px;">{f.code_snippet}</pre>
                <p><strong>Remediation:</strong> {f.remediation}</p>
            </div>
            """
        return f"""
        <!DOCTYPE html><html><head><title>ECC Security Report</title>
        <style>body {{ font-family: sans-serif; margin: 40px; }}
        .summary {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 20px 0; }}
        .metric {{ padding: 20px; text-align: center; border-radius: 8px; color: white; }}
        .critical {{ background: #dc3545; }} .high {{ background: #fd7e14; }}
        .medium {{ background: #ffc107; color: #000; }} .low {{ background: #17a2b8; }}
        .info {{ background: #6c757d; }}</style></head>
        <body><h1>🔒 ECC Security Report</h1>
        <div class="summary">
            <div class="metric critical">{result.critical_count}<br><small>Critical</small></div>
            <div class="metric high">{result.high_count}<br><small>High</small></div>
            <div class="metric medium">{len([f for f in result.findings if f.severity.value == 'MEDIUM'])}<br><small>Medium</small></div>
            <div class="metric low">{len([f for f in result.findings if f.severity.value == 'LOW'])}<br><small>Low</small></div>
            <div class="metric info">{result.files_scanned}<br><small>Files</small></div>
        </div><h2>Findings</h2>{findings_html}</body></html>
        """
