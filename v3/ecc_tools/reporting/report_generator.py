"""Unified report generation for all ECC tools.

Supports SARIF v2.1.0, JSON, and HTML output formats.
"""

import json
from typing import Dict, List, Any, Optional


class ReportGenerator:
    """Factory for generating ECC scan reports in multiple formats."""

    FORMATS = ("sarif", "json", "html")

    def __init__(self, tool_name: str = "ECC", tool_version: str = "1.0.0"):
        self.tool_name = tool_name
        self.tool_version = tool_version

    def generate(
        self,
        findings: List[Any],
        format: str = "json",
        metadata: Optional[Dict] = None,
    ) -> str:
        """Generate a formatted report from findings.

        Args:
            findings: List of finding objects (must have
                      severity, file_path, line_number, message,
                      rule_id, remediation attributes or keys).
            format: Output format: 'sarif', 'json', or 'html'.
            metadata: Optional metadata like files_scanned, lines_scanned,
                      scan_duration_ms.

        Returns:
            Formatted report string.
        """
        if format == "sarif":
            return self._generate_sarif(findings, metadata or {})
        elif format == "json":
            return self._generate_json(findings, metadata or {})
        elif format == "html":
            return self._generate_html(findings, metadata or {})
        else:
            raise ValueError(
                f"Unsupported format: {format}. Use one of {self.FORMATS}"
            )

    def _finding_to_dict(self, finding: Any) -> Dict:
        """Normalize a finding object to a dictionary."""
        if isinstance(finding, dict):
            return finding
        return {
            "rule_id": getattr(finding, "rule_id", ""),
            "rule_name": getattr(finding, "rule_name", getattr(finding, "name", "")),
            "severity": str(getattr(finding, "severity", "INFO")),
            "file_path": str(getattr(finding, "file_path", "")),
            "line_number": getattr(finding, "line_number", 0),
            "column": getattr(finding, "column", 0),
            "message": getattr(finding, "message", ""),
            "code_snippet": getattr(finding, "code_snippet", ""),
            "remediation": getattr(finding, "remediation", getattr(finding, "recommendation", "")),
            "cwe_id": getattr(finding, "cwe_id", None),
            "owasp_mapping": getattr(finding, "owasp_mapping", []),
        }

    def _count_by_severity(self, findings: List[Any], severity: str) -> int:
        return sum(
            1 for f in findings
            if str(getattr(f, "severity", f.get("severity", "") if isinstance(f, dict) else "")).upper() == severity.upper()
        )

    def _generate_json(self, findings: List[Any], metadata: Dict) -> str:
        finding_dicts = [self._finding_to_dict(f) for f in findings]
        return json.dumps(
            {
                "tool": {"name": self.tool_name, "version": self.tool_version},
                "summary": {
                    "total_findings": len(findings),
                    "critical": self._count_by_severity(findings, "CRITICAL"),
                    "high": self._count_by_severity(findings, "HIGH"),
                    "medium": self._count_by_severity(findings, "MEDIUM"),
                    "low": self._count_by_severity(findings, "LOW"),
                    "files_scanned": metadata.get("files_scanned", 0),
                    "lines_scanned": metadata.get("lines_scanned", 0),
                    "scan_duration_ms": metadata.get("scan_duration_ms", 0),
                },
                "findings": finding_dicts,
            },
            indent=2,
        )

    def _generate_sarif(self, findings: List[Any], metadata: Dict) -> str:
        results = []
        for f in findings:
            fd = self._finding_to_dict(f)
            results.append(
                {
                    "ruleId": fd["rule_id"],
                    "message": {"text": fd["message"]},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": fd["file_path"]},
                                "region": {
                                    "startLine": fd["line_number"],
                                    "startColumn": fd["column"],
                                    "snippet": {"text": fd.get("code_snippet", "")},
                                },
                            }
                        }
                    ],
                    "properties": {
                        "severity": fd["severity"],
                        "remediation": fd["remediation"],
                        "cwe": fd.get("cwe_id"),
                    },
                }
            )

        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": self.tool_name,
                            "version": self.tool_version,
                        }
                    },
                    "results": results,
                }
            ],
        }
        return json.dumps(sarif, indent=2)

    def _generate_html(self, findings: List[Any], metadata: Dict) -> str:
        SEVERITY_COLORS = {
            "CRITICAL": "#dc3545",
            "HIGH": "#fd7e14",
            "MEDIUM": "#ffc107",
            "LOW": "#17a2b8",
            "INFO": "#6c757d",
        }

        critical = self._count_by_severity(findings, "CRITICAL")
        high = self._count_by_severity(findings, "HIGH")
        medium = self._count_by_severity(findings, "MEDIUM")
        low = self._count_by_severity(findings, "LOW")

        findings_html = ""
        for f in findings:
            fd = self._finding_to_dict(f)
            color = SEVERITY_COLORS.get(fd["severity"].upper(), "#6c757d")
            findings_html += f"""
            <div style="border-left: 4px solid {color}; margin: 10px 0; padding: 10px; background: #f8f9fa;">
                <h4>{fd["rule_name"]} <span style="color: {color};">[{fd["severity"]}]</span></h4>
                <p><strong>File:</strong> {fd["file_path"]}:{fd["line_number"]}</p>
                <p><strong>Message:</strong> {fd["message"]}</p>
                <pre style="background: #e9ecef; padding: 8px; border-radius: 4px; overflow-x: auto;">{fd.get("code_snippet", "")}</pre>
                <p><strong>Remediation:</strong> {fd["remediation"]}</p>
                {f'<p><small>CWE: {fd["cwe_id"]}</small></p>' if fd.get("cwe_id") else ""}
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{self.tool_name} Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #16213e; padding-bottom: 15px; }}
        .summary {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 20px 0; }}
        .metric {{ padding: 20px; text-align: center; border-radius: 8px; color: white; font-size: 24px; font-weight: bold; }}
        .critical {{ background: #dc3545; }} .high {{ background: #fd7e14; }}
        .medium {{ background: #ffc107; color: #000; }} .low {{ background: #17a2b8; }}
        .info {{ background: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{self.tool_name} Report</h1>
        <p>Tool Version: {self.tool_version}</p>
        <div class="summary">
            <div class="metric critical">{critical}<br><small>Critical</small></div>
            <div class="metric high">{high}<br><small>High</small></div>
            <div class="metric medium">{medium}<br><small>Medium</small></div>
            <div class="metric low">{low}<br><small>Low</small></div>
            <div class="metric info">{len(findings)}<br><small>Total</small></div>
        </div>
        <h2>Findings ({len(findings)})</h2>
        {findings_html}
    </div>
</body>
</html>
"""
