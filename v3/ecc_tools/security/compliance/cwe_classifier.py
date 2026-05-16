"""CWE (Common Weakness Enumeration) classifier.

Provides descriptions and remediation advice for common CWEs.
"""

CWE_DATABASE = {
    "CWE-20": {
        "name": "Improper Input Validation",
        "description": "Product does not validate or incorrectly validates input",
        "remediation": "Validate all inputs for type, length, format, and range. Use allowlists.",
    },
    "CWE-22": {
        "name": "Path Traversal",
        "description": "Improper limitation of a pathname to a restricted directory",
        "remediation": "Use pathlib.Path.resolve() and validate against allowed directories.",
    },
    "CWE-78": {
        "name": "OS Command Injection",
        "description": "Improper neutralization of special elements used in an OS command",
        "remediation": "Use subprocess with shell=False and pass arguments as a list.",
    },
    "CWE-79": {
        "name": "Cross-Site Scripting (XSS)",
        "description": "Improper neutralization of input during web page generation",
        "remediation": "Escape output, use Content-Security-Policy headers, validate input.",
    },
    "CWE-89": {
        "name": "SQL Injection",
        "description": "Improper neutralization of special elements used in an SQL command",
        "remediation": "Use parameterized queries or ORM with bind parameters.",
    },
    "CWE-94": {
        "name": "Code Injection",
        "description": "Improper control of generation of code",
        "remediation": "Avoid dynamic code execution. Use safe parsers and validators.",
    },
    "CWE-95": {
        "name": "Eval Injection",
        "description": "Improper neutralization of directives in dynamically evaluated code",
        "remediation": "Never use eval() on untrusted input. Use JSON.parse() or similar.",
    },
    "CWE-287": {
        "name": "Improper Authentication",
        "description": "Insufficient verification of claimed identity",
        "remediation": "Implement multi-factor auth, strong password policies, session management.",
    },
    "CWE-352": {
        "name": "Cross-Site Request Forgery (CSRF)",
        "description": "Web application does not verify requests were intentionally sent",
        "remediation": "Use CSRF tokens, SameSite cookies, and verify Origin/Referer headers.",
    },
    "CWE-434": {
        "name": "Unrestricted File Upload",
        "description": "Product allows upload of dangerous file types",
        "remediation": "Validate file type, scan for malware, store outside web root, limit size.",
    },
    "CWE-502": {
        "name": "Deserialization of Untrusted Data",
        "description": "Product deserializes untrusted data without verification",
        "remediation": "Use safe serialization formats (JSON), validate before deserializing.",
    },
    "CWE-532": {
        "name": "Sensitive Information in Logs",
        "description": "Sensitive information written to log files",
        "remediation": "Scrub PII, tokens, and passwords from log output.",
    },
    "CWE-601": {
        "name": "Open Redirect",
        "description": "URL redirection to untrusted site",
        "remediation": "Validate redirect URLs against an allowlist. Use relative redirects.",
    },
    "CWE-798": {
        "name": "Hardcoded Credentials",
        "description": "Credentials stored in source code",
        "remediation": "Use environment variables, secret managers, or vault services.",
    },
    "CWE-862": {
        "name": "Missing Authorization",
        "description": "Missing authorization checks on protected resources",
        "remediation": "Implement role-based access control. Verify permissions on every endpoint.",
    },
    "CWE-918": {
        "name": "Server-Side Request Forgery (SSRF)",
        "description": "Server fetches URL controlled by attacker",
        "remediation": "Validate and sanitize URLs. Block internal IPs. Use allowlists.",
    },
    "CWE-1336": {
        "name": "Improper Neutralization of Formula Elements in CSV",
        "description": "CSV injection via formula elements",
        "remediation": "Prefix cells starting with =,+,-,@ with a single quote.",
    },
}


class CWEClassifier:
    """Resolves CWE IDs to descriptions and remediation advice."""

    @staticmethod
    def get_cwe(cwe_id: str) -> dict:
        """Look up a CWE by ID."""
        if not cwe_id:
            return {"id": None, "name": "Unknown", "description": "", "remediation": ""}
        cwe = CWE_DATABASE.get(cwe_id.upper(), {})
        return {"id": cwe_id.upper(), **cwe} if cwe else {
            "id": cwe_id.upper(),
            "name": "Unknown CWE",
            "description": f"CWE {cwe_id} not in local database",
            "remediation": "Consult https://cwe.mitre.org/data/definitions/{}.html".format(
                cwe_id.replace("CWE-", "")
            ),
        }

    @staticmethod
    def get_remediation(cwe_id: str) -> str:
        """Get remediation advice for a CWE."""
        return CWEClassifier.get_cwe(cwe_id).get("remediation", "")

    @staticmethod
    def enrich_findings(findings: list) -> list:
        """Add CWE descriptions to findings that have cwe_id fields."""
        for finding in findings:
            cwe_id = getattr(finding, "cwe_id", None)
            if cwe_id:
                cwe_info = CWEClassifier.get_cwe(cwe_id)
                if not getattr(finding, "cwe_name", None):
                    finding.cwe_name = cwe_info.get("name", "")
        return findings
