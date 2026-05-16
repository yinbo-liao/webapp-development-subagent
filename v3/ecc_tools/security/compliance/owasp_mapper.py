"""Maps security findings to OWASP Top 10 (2021) categories."""

OWASP_2021_CATEGORIES = {
    "A01:2021": {
        "name": "Broken Access Control",
        "description": "Restrictions on authenticated users are not properly enforced",
        "cwes": ["CWE-22", "CWE-23", "CWE-35", "CWE-59", "CWE-200", "CWE-201",
                 "CWE-219", "CWE-264", "CWE-275", "CWE-276", "CWE-284", "CWE-285",
                 "CWE-352", "CWE-359", "CWE-377", "CWE-402", "CWE-425", "CWE-441",
                 "CWE-497", "CWE-538", "CWE-540", "CWE-548", "CWE-552", "CWE-566",
                 "CWE-601", "CWE-639", "CWE-647", "CWE-668", "CWE-706", "CWE-862",
                 "CWE-863", "CWE-913", "CWE-922", "CWE-1275"],
    },
    "A02:2021": {
        "name": "Cryptographic Failures",
        "description": "Failures related to cryptography leading to sensitive data exposure",
        "cwes": ["CWE-261", "CWE-296", "CWE-310", "CWE-319", "CWE-321", "CWE-322",
                 "CWE-323", "CWE-324", "CWE-325", "CWE-326", "CWE-327", "CWE-328",
                 "CWE-329", "CWE-330", "CWE-331", "CWE-335", "CWE-338", "CWE-347",
                 "CWE-523", "CWE-720", "CWE-757", "CWE-759", "CWE-760", "CWE-780"],
    },
    "A03:2021": {
        "name": "Injection",
        "description": "User-supplied data is not validated, filtered, or sanitized",
        "cwes": ["CWE-20", "CWE-74", "CWE-75", "CWE-77", "CWE-78", "CWE-79",
                 "CWE-80", "CWE-83", "CWE-87", "CWE-88", "CWE-89", "CWE-90",
                 "CWE-91", "CWE-93", "CWE-94", "CWE-95", "CWE-98", "CWE-99",
                 "CWE-100", "CWE-113", "CWE-116", "CWE-138", "CWE-184", "CWE-470",
                 "CWE-471", "CWE-564", "CWE-610", "CWE-643", "CWE-644", "CWE-652",
                 "CWE-706", "CWE-707", "CWE-943", "CWE-1336"],
    },
    "A04:2021": {
        "name": "Insecure Design",
        "description": "Design and architectural flaws",
        "cwes": ["CWE-73", "CWE-183", "CWE-209", "CWE-213", "CWE-221",
                 "CWE-248", "CWE-256", "CWE-267", "CWE-269", "CWE-272",
                 "CWE-307", "CWE-308", "CWE-424", "CWE-430", "CWE-434",
                 "CWE-444", "CWE-451", "CWE-501", "CWE-522", "CWE-525",
                 "CWE-539", "CWE-579", "CWE-602", "CWE-642", "CWE-646",
                 "CWE-650", "CWE-653", "CWE-656", "CWE-657", "CWE-799",
                 "CWE-804", "CWE-840", "CWE-841", "CWE-909", "CWE-1004",
                 "CWE-1022", "CWE-1039", "CWE-1042", "CWE-1045", "CWE-1052",
                 "CWE-1073", "CWE-1088", "CWE-1092", "CWE-1103", "CWE-1110",
                 "CWE-1114", "CWE-1119", "CWE-1127", "CWE-1173"],
    },
    "A05:2021": {
        "name": "Security Misconfiguration",
        "description": "Insecure default configurations, incomplete configurations, open cloud storage",
        "cwes": ["CWE-2", "CWE-11", "CWE-13", "CWE-15", "CWE-16", "CWE-260",
                 "CWE-315", "CWE-346", "CWE-401", "CWE-453", "CWE-489",
                 "CWE-543", "CWE-565", "CWE-829", "CWE-838", "CWE-933",
                 "CWE-937", "CWE-942", "CWE-1004", "CWE-1032", "CWE-1174"],
    },
    "A06:2021": {
        "name": "Vulnerable and Outdated Components",
        "description": "Using components with known vulnerabilities",
        "cwes": ["CWE-937", "CWE-1035", "CWE-1104"],
    },
    "A07:2021": {
        "name": "Identification and Authentication Failures",
        "description": "Authentication attacks and credential management failures",
        "cwes": ["CWE-255", "CWE-259", "CWE-287", "CWE-288", "CWE-290",
                 "CWE-294", "CWE-295", "CWE-297", "CWE-300", "CWE-302",
                 "CWE-304", "CWE-306", "CWE-307", "CWE-309", "CWE-311",
                 "CWE-317", "CWE-318", "CWE-319", "CWE-345", "CWE-353",
                 "CWE-354", "CWE-384", "CWE-521", "CWE-522", "CWE-549",
                 "CWE-579", "CWE-598", "CWE-613", "CWE-615", "CWE-620",
                 "CWE-640", "CWE-645", "CWE-798", "CWE-804", "CWE-840",
                 "CWE-841", "CWE-1390"],
    },
    "A08:2021": {
        "name": "Software and Data Integrity Failures",
        "description": "Insecure deserialization, CI/CD pipeline integrity failures",
        "cwes": ["CWE-345", "CWE-353", "CWE-426", "CWE-494", "CWE-502",
                 "CWE-565", "CWE-784", "CWE-829", "CWE-830", "CWE-915"],
    },
    "A09:2021": {
        "name": "Security Logging and Monitoring Failures",
        "description": "Insufficient logging, detection, monitoring, and active response",
        "cwes": ["CWE-117", "CWE-223", "CWE-532", "CWE-778"],
    },
    "A10:2021": {
        "name": "Server-Side Request Forgery (SSRF)",
        "description": "SSRF flaws occur when a web application fetches a remote resource without validating the URL",
        "cwes": ["CWE-918"],
    },
}


class OWASPMapper:
    """Maps security findings to OWASP Top 10 (2021) categories."""

    @staticmethod
    def get_category_for_cwe(cwe_id: str) -> dict:
        """Find the OWASP category for a given CWE ID."""
        if not cwe_id:
            return {"id": None, "name": "Uncategorized", "description": "No CWE mapping available"}

        for owasp_id, category in OWASP_2021_CATEGORIES.items():
            if cwe_id.upper().replace("-", "-") in [c.upper() for c in category["cwes"]]:
                return {"id": owasp_id, **category}
        return {"id": None, "name": "Other", "description": "Not directly mapped to OWASP Top 10 2021"}

    @staticmethod
    def get_compliance_summary(findings: list) -> dict:
        """Generate OWASP compliance summary from a list of findings."""
        summary = {}
        for category_id, category in OWASP_2021_CATEGORIES.items():
            summary[category_id] = {
                "name": category["name"],
                "status": "PASS",
                "finding_count": 0,
            }

        for finding in findings:
            cwe = getattr(finding, "cwe_id", None)
            if cwe:
                category = OWASPMapper.get_category_for_cwe(cwe)
                if category["id"]:
                    summary[category["id"]]["finding_count"] += 1
                    summary[category["id"]]["status"] = "REVIEW"

        return summary

    @staticmethod
    def get_all_categories() -> dict:
        return dict(OWASP_2021_CATEGORIES)
