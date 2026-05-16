#!/usr/bin/env python3
"""
Enterprise Web Development System
Main entry point for the subagent system

Usage:
    python main.py --workflow new-project --project my-app --requirements requirements.yaml
    python main.py --workflow feature-dev --project my-app --feature user-auth
    python main.py --ecc-scan --project my-app
"""

import argparse
import yaml
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator.main import Orchestrator
from agents.registry import AgentRegistry
from ecc_tools.core.engine import ECCEngine


def setup_agents(orchestrator: Orchestrator):
    """Register all specialized agents via config-driven registry."""
    print("[SYSTEM] Setting up specialized agents...")

    ecc = ECCEngine.get_instance("config")
    registry = AgentRegistry(config=orchestrator.config, ecc=ecc)
    agents = registry.discover_all()

    for agent_type, agent_instance in agents.items():
        orchestrator.register_agent(agent_type, agent_instance)

    print(f"[SYSTEM] {len(agents)} agents registered successfully\n")


def load_requirements(requirements_path: str) -> dict:
    """Load requirements from YAML file"""
    if not Path(requirements_path).exists():
        print(f"[ERROR] Requirements file not found: {requirements_path}")
        sys.exit(1)

    with open(requirements_path, 'r') as f:
        return yaml.safe_load(f)


def run_new_project_workflow(args):
    """Execute new project workflow"""
    print("=" * 70)
    print("ENTERPRISE WEB DEVELOPMENT SYSTEM - New Project")
    print("=" * 70)

    # Initialize orchestrator
    orchestrator = Orchestrator()
    setup_agents(orchestrator)

    # Load requirements
    requirements = load_requirements(args.requirements) if args.requirements else {
        "functional": [
            "User authentication and authorization",
            "CRUD operations for main entities",
            "Role-based access control",
            "Audit logging"
        ],
        "non_functional": [
            "Response time < 200ms for API calls",
            "99.9% uptime",
            "Support 10,000 concurrent users"
        ],
        "security": [
            "OWASP Top 10 compliance",
            "JWT token authentication",
            "Rate limiting",
            "Input validation and sanitization"
        ],
        "performance": [
            "Database query optimization",
            "Redis caching",
            "CDN for static assets"
        ]
    }

    # Execute workflow
    results = orchestrator.execute_workflow(
        workflow_name="new-project",
        project_path=args.project,
        requirements=requirements
    )

    # Generate report
    if args.report:
        report = orchestrator.generate_report(results, format=args.report)
        report_path = Path(args.project) / f"workflow-report.{args.report}"
        report_path.write_text(report)
        print(f"\n[SYSTEM] Report saved to: {report_path}")

    return results


def run_feature_workflow(args):
    """Execute feature development workflow"""
    print("=" * 70)
    print("ENTERPRISE WEB DEVELOPMENT SYSTEM - Feature Development")
    print("=" * 70)

    orchestrator = Orchestrator()
    setup_agents(orchestrator)

    requirements = {
        "functional": [args.feature],
        "non_functional": [],
        "security": [],
        "performance": []
    }

    results = orchestrator.execute_workflow(
        workflow_name="feature-development",
        project_path=args.project,
        requirements=requirements
    )

    return results


def run_ecc_scan(args):
    """Run ECC scan on existing project or single file."""
    from ecc_tools.core.engine import ECCEngine

    engine = ECCEngine.get_instance("config")

    # Single-file scan mode
    if args.file:
        print("=" * 70)
        print("ENTERPRISE CODE COMPLIANCE - Single File Scan")
        print("=" * 70)
        print(f"File: {args.file}")

        if not Path(args.file).exists():
            print(f"[ERROR] File not found: {args.file}")
            return 1

        report = engine.scan_single_file(args.file)
        print_report_summary(report)
        return 0 if report.total_issues == 0 else 1

    # Pre-commit mode (scan project, exit non-zero on critical/high)
    if args.pre_commit:
        report = engine.full_scan(args.project)
        critical_count = (
            (report.security.critical_count + report.security.high_count
             if report.security else 0) +
            len([i for i in report.stability if i.severity in ('critical', 'high')]) +
            len([i for i in report.performance if i.severity in ('critical', 'high')])
        )
        if critical_count > 0:
            print(f"[PRE-COMMIT] BLOCKED: {critical_count} critical/high issues found")
            return 1
        print("[PRE-COMMIT] PASSED")
        return 0

    # Full project scan
    print("=" * 70)
    print("ENTERPRISE CODE COMPLIANCE - Full Scan")
    print("=" * 70)

    # Determine which tools to run
    tools = args.tools or ["security", "stability", "performance", "maintainability"]

    report = engine.full_scan(args.project)

    # Print per-tool results
    if "security" in tools and report.security:
        sec = report.security
        print(f"\n[SECURITY] SAST scan: {sec.files_scanned} files, "
              f"{sec.critical_count} critical, {sec.high_count} high, "
              f"{len([f for f in sec.findings if f.severity.value == 'MEDIUM'])} medium")
        if sec.parse_errors:
            print(f"  Parse errors: {len(sec.parse_errors)} files")
        if sec.scan_errors:
            print(f"  Scan errors: {len(sec.scan_errors)} files")

    if "stability" in tools:
        stab_crit = len([i for i in report.stability if i.severity == 'critical'])
        print(f"\n[STABILITY] {len(report.stability)} issues ({stab_crit} critical)")

    if "performance" in tools:
        perf_crit = len([i for i in report.performance if i.severity == 'critical'])
        print(f"\n[PERFORMANCE] {len(report.performance)} issues ({perf_crit} critical)")

    if "maintainability" in tools:
        print(f"\n[MAINTAINABILITY] {len(report.maintainability)} issues")

    # Generate report
    if args.output:
        from ecc_tools.reporting.report_generator import ReportGenerator
        gen = ReportGenerator("ECC-Scan", "2.0.0")
        all_findings = report._all_findings()
        report_text = gen.generate(all_findings, format=args.output,
                                   metadata={"files_scanned": report.security.files_scanned if report.security else 0})
        report_path = Path(args.project) / f"ecc-report.{args.output}"
        report_path.write_text(report_text, encoding="utf-8")
        print(f"\n[SYSTEM] Report saved to: {report_path}")

    # Summary
    total_critical = (
        (report.security.critical_count if report.security else 0) +
        len([i for i in report.stability if i.severity == 'critical']) +
        len([i for i in report.performance if i.severity == 'critical'])
    )

    print("\n" + "=" * 70)
    print("SCAN SUMMARY")
    print("=" * 70)
    print(f"Security: {report.security.critical_count if report.security else 0} critical, "
          f"{report.security.high_count if report.security else 0} high")
    print(f"Stability: {len(report.stability)} issues")
    print(f"Performance: {len(report.performance)} issues")
    print(f"Maintainability: {len(report.maintainability)} issues")

    if total_critical > 0:
        print(f"\n[WARN] {total_critical} CRITICAL issues found. Review required.")
        return 1
    else:
        print("\n[OK] No critical issues found. Project passes ECC scan.")
        return 0


def print_report_summary(report):
    """Print a brief summary from an ECCReport."""
    print(f"  Total issues: {report.total_issues}")
    if report.security:
        print(f"  Security: {report.security.critical_count} critical, "
              f"{report.security.high_count} high")
    print(f"  Stability: {len([i for i in report.stability if i.severity == 'critical'])} critical")
    print(f"  Performance: {len([i for i in report.performance if i.severity == 'critical'])} critical")


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise Web Development System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create new project
  python main.py --workflow new-project --project ./my-app --requirements requirements.yaml

  # Add feature to existing project
  python main.py --workflow feature-dev --project ./my-app --feature "user-authentication"

  # Run ECC security scan
  python main.py --ecc-scan --project ./my-app --output html
        """
    )

    parser.add_argument("--workflow", choices=["new-project", "feature-dev"],
                       help="Workflow to execute")
    parser.add_argument("--project", default=".",
                       help="Project directory path (default: current directory)")
    parser.add_argument("--requirements",
                       help="Requirements YAML file path")
    parser.add_argument("--feature",
                       help="Feature name for feature development")
    parser.add_argument("--ecc-scan", action="store_true",
                       help="Run ECC scan on project")
    parser.add_argument("--file",
                       help="Run ECC scan on a single file")
    parser.add_argument("--pre-commit", action="store_true",
                       help="Pre-commit mode: block on critical/high findings (exit 1)")
    parser.add_argument("--tools", nargs="+",
                       choices=["security", "stability", "performance", "maintainability"],
                       help="Specific ECC tools to run (default: all four)")
    parser.add_argument("--output", choices=["sarif", "json", "html"],
                       help="Output format for ECC scan report")
    parser.add_argument("--report", choices=["html", "json"],
                       help="Generate workflow report")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose/debug output")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be generated without writing files")
    parser.add_argument("--skip-ecc", action="store_true",
                       help="Skip ECC validation phase (faster, for prototyping)")

    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    if args.dry_run:
        print("[DRY-RUN] No files will be written to disk")

    if args.ecc_scan:
        return run_ecc_scan(args)
    elif args.workflow == "new-project":
        results = run_new_project_workflow(args)
        return 0 if results["status"] == "completed" else 1
    elif args.workflow == "feature-dev":
        results = run_feature_workflow(args)
        return 0 if results["status"] == "completed" else 1
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
