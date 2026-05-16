#!/usr/bin/env python3
"""
Demo script for Enterprise Web Development System
Demonstrates the complete workflow with all agents and ECC tools
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator.main import Orchestrator
from agents.registry import AgentRegistry
from ecc_tools.core.engine import ECCEngine


def demo():
    print("\n" + "="*70)
    print("ENTERPRISE WEB DEVELOPMENT SYSTEM - DEMO")
    print("="*70 + "\n")

    # Initialize orchestrator
    orchestrator = Orchestrator()

    # Register agents via config-driven registry
    print("[1] Registering specialized agents...")
    ecc = ECCEngine.get_instance("config")
    registry = AgentRegistry(config=orchestrator.config, ecc=ecc)
    for agent_type, agent_instance in registry.discover_all().items():
        orchestrator.register_agent(agent_type, agent_instance)
    print("    [OK] All agents registered\n")

    # Define requirements
    requirements = {
        "functional": [
            "User authentication with JWT tokens",
            "Role-based access control",
            "Project and task management",
            "Real-time notifications"
        ],
        "non_functional": [
            "API response time < 200ms",
            "Support 1000 concurrent users",
            "99.9% uptime"
        ],
        "security": [
            "OWASP Top 10 compliance",
            "JWT authentication",
            "Rate limiting"
        ],
        "performance": [
            "Redis caching",
            "Database optimization",
            "CDN integration"
        ]
    }

    # Execute workflow
    print("[2] Executing development workflow...")
    results = orchestrator.execute_workflow(
        workflow_name="enterprise-demo",
        project_path="./demo-output",
        requirements=requirements
    )

    # Generate report
    print("\n[3] Generating workflow report...")
    report = orchestrator.generate_report(results, format="html")
    report_path = "./demo-output/workflow-report.html"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    print(f"    [OK] Report saved to: {report_path}\n")

    # Summary
    print("="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print(f"Workflow Status: {results['status']}")
    print(f"Quality Gate: {'PASSED' if results['quality_gate'].get('passed') else 'FAILED'}")
    print(f"Security Findings: {results['ecc_results'].get('security', {}).critical_count if 'security' in results.get('ecc_results', {}) else 'N/A'} critical")
    print(f"\nGenerated files:")
    for phase, phase_results in results.get('phases', {}).get('implementation', {}).items():
        if isinstance(phase_results, dict) and 'generated_files' in phase_results:
            print(f"  [{phase.upper()}] {len(phase_results['generated_files'])} files")

    print("\nNext steps:")
    print("  1. Review generated code in ./demo-output/")
    print("  2. Check ECC reports for any issues")
    print("  3. Run tests: pytest ./demo-output/app/tests")
    print("  4. Deploy: docker-compose -f ./demo-output/docker-compose.yml up -d")
    print()


if __name__ == "__main__":
    demo()
