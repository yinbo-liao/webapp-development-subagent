import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
import concurrent.futures
from datetime import datetime

from ecc_tools.core.engine import ECCEngine, QualityGateResult


class Orchestrator:
    """
    Central orchestrator for the subagent system
    Manages workflow execution, agent coordination, and quality gates
    """

    def __init__(self, config_path: str = "config/agents.yaml"):
        self.config = self._load_config(config_path)
        self.agents = {}
        self.ecc = ECCEngine.get_instance("config")
        self.workflow_history = []

    def _load_config(self, config_path: str) -> Dict:
        if Path(config_path).exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {
            "agents": {
                "frontend": {"enabled": True, "priority": 2},
                "backend": {"enabled": True, "priority": 2},
                "database": {"enabled": True, "priority": 2},
                "security": {"enabled": True, "priority": 1},
                "performance": {"enabled": True, "priority": 1},
                "qa": {"enabled": True, "priority": 3},
                "devops": {"enabled": True, "priority": 3}
            },
            "quality_gates": {
                "security": {"max_critical": 0, "max_high": 5},
                "stability": {"max_critical": 0},
                "performance": {"max_critical": 0},
                "maintainability": {"min_mi": 70}
            }
        }

    def register_agent(self, agent_type: str, agent_instance: Any):
        """Register a subagent"""
        self.agents[agent_type] = agent_instance
        print(f"[ORCHESTRATOR] Registered agent: {agent_type}")

    def execute_workflow(self, workflow_name: str, project_path: str, requirements: Dict) -> Dict:
        """
        Execute a complete development workflow

        Phases:
        1. Requirements Analysis
        2. Architecture Design  
        3. Implementation (parallel agents)
        4. ECC Scanning (security, stability, performance, maintainability)
        5. Quality Gate
        6. Testing
        7. Deployment
        """
        print(f"\n{'='*60}")
        print(f"[ORCHESTRATOR] Starting workflow: {workflow_name}")
        print(f"{'='*60}\n")

        start_time = datetime.now()

        results = {
            "workflow": workflow_name,
            "project": project_path,
            "start_time": start_time.isoformat(),
            "phases": {},
            "ecc_results": {},
            "quality_gate": {},
            "status": "running"
        }

        try:
            # Phase 1: Requirements Analysis
            print("[PHASE 1] Requirements Analysis...")
            results["phases"]["requirements"] = self._phase_requirements(requirements)
            print("[PHASE 1] [OK] Complete\n")

            # Phase 2: Architecture Design
            print("[PHASE 2] Architecture Design...")
            results["phases"]["architecture"] = self._phase_architecture(results["phases"]["requirements"])
            print("[PHASE 2] [OK] Complete\n")

            # Phase 3: Parallel Implementation
            print("[PHASE 3] Parallel Implementation...")
            results["phases"]["implementation"] = self._phase_implementation(
                results["phases"]["architecture"], 
                project_path
            )
            print("[PHASE 3] [OK] Complete\n")

            # Phase 4: ECC Comprehensive Scanning
            print("[PHASE 4] ECC Comprehensive Scanning...")
            results["ecc_results"] = self._phase_ecc_scan(project_path)
            print("[PHASE 4] [OK] Complete\n")

            # Phase 5: Quality Gate
            print("[PHASE 5] Quality Gate Evaluation...")
            results["quality_gate"] = self._phase_quality_gate(results["ecc_results"])
            print("[PHASE 5] [OK] Complete\n")

            if not results["quality_gate"]["passed"]:
                results["status"] = "failed_quality_gate"
                print("[QUALITY GATE] [FAIL] FAILED - Review issues before proceeding\n")
                return results

            print("[QUALITY GATE] [OK] PASSED\n")

            # Phase 6: Testing
            print("[PHASE 6] Testing...")
            results["phases"]["testing"] = self._phase_testing(project_path)
            print("[PHASE 6] [OK] Complete\n")

            # Phase 7: Deployment
            print("[PHASE 7] Deployment...")
            results["phases"]["deployment"] = self._phase_deployment(project_path)
            print("[PHASE 7] [OK] Complete\n")

            results["status"] = "completed"
            results["end_time"] = datetime.now().isoformat()

            print(f"{'='*60}")
            print(f"[ORCHESTRATOR] Workflow completed successfully!")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"[ORCHESTRATOR] [FAIL] Workflow failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
            results["end_time"] = datetime.now().isoformat()

        self.workflow_history.append(results)
        return results

    def _phase_requirements(self, requirements: Dict) -> Dict:
        """Analyze and decompose requirements"""
        return {
            "functional": requirements.get("functional", []),
            "non_functional": requirements.get("non_functional", []),
            "security_requirements": requirements.get("security", []),
            "performance_requirements": requirements.get("performance", []),
            "tasks": self._decompose_tasks(requirements)
        }

    def _phase_architecture(self, requirements: Dict) -> Dict:
        """Design system architecture"""
        tech_stack = self._select_tech_stack(requirements)

        return {
            "pattern": self._select_architecture_pattern(requirements),
            "tech_stack": tech_stack,
            "components": self._design_components(requirements, tech_stack),
            "data_model": self._design_data_model(requirements),
            "api_design": self._design_api(requirements),
            "security_architecture": self._design_security(requirements),
            "deployment_architecture": self._design_deployment(requirements)
        }

    def _phase_implementation(self, architecture: Dict, project_path: str) -> Dict:
        """Execute parallel implementation by specialized agents"""
        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}

            if "frontend" in architecture["components"] and "frontend" in self.agents:
                futures['frontend'] = executor.submit(
                    self.agents['frontend'].implement,
                    architecture["components"]["frontend"],
                    project_path
                )

            if "backend" in architecture["components"] and "backend" in self.agents:
                futures['backend'] = executor.submit(
                    self.agents['backend'].implement,
                    architecture["components"]["backend"],
                    project_path
                )

            if "database" in architecture["components"] and "database" in self.agents:
                futures['database'] = executor.submit(
                    self.agents['database'].implement,
                    architecture["data_model"],
                    project_path
                )

            if "devops" in self.agents:
                futures['devops'] = executor.submit(
                    self.agents['devops'].setup,
                    architecture["deployment_architecture"],
                    project_path
                )

            for agent_type, future in futures.items():
                try:
                    results[agent_type] = future.result(timeout=300)
                    print(f"  [{agent_type.upper()}] [OK] Implementation complete")
                except Exception as e:
                    results[agent_type] = {"status": "failed", "error": str(e)}
                    print(f"  [{agent_type.upper()}] [FAIL] Failed: {e}")

        return results

    def _phase_ecc_scan(self, project_path: str) -> Dict:
        """Run comprehensive ECC scanning via shared engine."""
        report = self.ecc.full_scan(project_path)

        security = report.security
        stability = report.stability
        performance = report.performance
        maintainability = report.maintainability

        print(f"  [SECURITY] SAST scan: {security.critical_count} critical, {security.high_count} high"
              if security else "  [SECURITY] No scan results")
        print(f"  [STABILITY] {len([i for i in stability if i.severity == 'critical'])} critical issues")
        print(f"  [PERFORMANCE] {len([i for i in performance if i.severity == 'critical'])} critical issues")
        print(f"  [MAINTAINABILITY] {len(maintainability)} issues")

        return {
            "security": security,
            "stability": stability,
            "performance": performance,
            "maintainability": maintainability,
        }

    def _phase_quality_gate(self, ecc_results: Dict) -> Dict:
        """Evaluate quality gates using centralized evaluator."""
        quality_gates = self.config.get("quality_gates", {})

        gate = QualityGateResult()

        # Security
        sec = ecc_results.get("security")
        if sec:
            max_crit = quality_gates.get("security", {}).get("max_critical", 0)
            max_high = quality_gates.get("security", {}).get("max_high", 5)
            sec_pass = sec.critical_count <= max_crit and sec.high_count <= max_high
            gate.add_check("security", sec_pass,
                          details={"critical": sec.critical_count, "high": sec.high_count,
                                   "max_critical": max_crit, "max_high": max_high},
                          failure_message=f"Security: {sec.critical_count} critical (max {max_crit}), "
                                         f"{sec.high_count} high (max {max_high})")

        # Stability
        stab = ecc_results.get("stability", [])
        stab_max = quality_gates.get("stability", {}).get("max_critical", 0)
        stab_crit = len([i for i in stab if i.severity == 'critical'])
        gate.add_check("stability", stab_crit <= stab_max,
                      details={"critical_count": stab_crit, "max_critical": stab_max},
                      failure_message=f"Stability: {stab_crit} critical issues")

        # Performance
        perf = ecc_results.get("performance", [])
        perf_max = quality_gates.get("performance", {}).get("max_critical", 0)
        perf_crit = len([i for i in perf if i.severity == 'critical'])
        gate.add_check("performance", perf_crit <= perf_max,
                      details={"critical_count": perf_crit, "max_critical": perf_max},
                      failure_message=f"Performance: {perf_crit} critical issues")

        # Maintainability
        maint = ecc_results.get("maintainability", [])
        mi_issues = [i for i in maint if 'Maintainability Index' in i.get('message', '')]
        gate.add_check("maintainability", len(mi_issues) == 0,
                      details={"issues": len(mi_issues)})

        return gate.to_dict()

    def _phase_testing(self, project_path: str) -> Dict:
        """Execute comprehensive testing"""
        if "qa" in self.agents:
            return self.agents['qa'].run_tests(project_path)
        return {"status": "skipped", "reason": "No QA agent registered"}

    def _phase_deployment(self, project_path: str) -> Dict:
        """Deploy application"""
        if "devops" in self.agents:
            return self.agents['devops'].deploy(project_path)
        return {"status": "skipped", "reason": "No DevOps agent registered"}

    def _decompose_tasks(self, requirements: Dict) -> List[Dict]:
        """Decompose requirements into implementable tasks"""
        tasks = []
        for req in requirements.get("functional", []):
            tasks.append({
                "type": "feature",
                "description": req,
                "estimated_complexity": "medium",
                "dependencies": []
            })
        return tasks

    def _select_tech_stack(self, requirements: Dict) -> Dict:
        """Select optimal technology stack"""
        stack = {
            "frontend": "react_typescript",
            "backend": "fastapi_python",
            "database": "postgresql",
            "cache": "redis",
            "message_queue": "rabbitmq",
            "containerization": "docker",
            "orchestration": "kubernetes"
        }

        req_str = str(requirements).lower()
        if "real-time" in req_str:
            stack["websocket"] = "socket.io"
        if "high-traffic" in req_str:
            stack["load_balancer"] = "nginx"
            stack["cdn"] = "cloudflare"

        return stack

    def _select_architecture_pattern(self, requirements: Dict) -> str:
        req_str = str(requirements).lower()
        if "microservices" in req_str:
            return "microservices"
        elif "serverless" in req_str:
            return "serverless"
        return "modular_monolith"

    def _design_components(self, requirements: Dict, tech_stack: Dict) -> Dict:
        return {
            "frontend": {
                "framework": tech_stack["frontend"],
                "components": [
                    {"name": "AuthForm", "props": [{"name": "onSubmit", "type": "function", "required": True}], "description": "Authentication form component"},
                    {"name": "Dashboard", "props": [{"name": "data", "type": "DashboardData", "required": True}], "description": "Main dashboard view"},
                    {"name": "DataTable", "props": [{"name": "rows", "type": "Array<Record>", "required": True}], "description": "Reusable data table"},
                    {"name": "FormBuilder", "props": [{"name": "schema", "type": "FormSchema", "required": True}], "description": "Dynamic form builder"},
                ]
            },
            "backend": {
                "framework": tech_stack["backend"],
                "modules": ["auth", "api", "services", "repositories"],
                "models": [
                    {"name": "User", "fields": [
                        {"name": "email", "type": "String", "nullable": False, "unique": True, "index": True},
                        {"name": "hashed_password", "type": "String", "nullable": False},
                        {"name": "full_name", "type": "String", "nullable": True},
                    ], "description": "User account model"},
                ],
                "schemas": [
                    {"name": "User", "fields": [
                        {"name": "email", "type": "str"},
                        {"name": "full_name", "type": "Optional[str]"},
                    ]},
                ],
                "endpoints": [
                    {"name": "User"},
                ],
                "services": [
                    {"name": "User"},
                ],
            },
            "database": {
                "type": tech_stack["database"],
                "entities": ["users", "roles", "audit_logs"]
            }
        }

    def _design_data_model(self, requirements: Dict) -> Dict:
        return {"entities": [], "relationships": []}

    def _design_api(self, requirements: Dict) -> Dict:
        return {"version": "v1", "endpoints": [], "authentication": "jwt"}

    def _design_security(self, requirements: Dict) -> Dict:
        return {
            "authentication": "oauth2_jwt",
            "authorization": "rbac",
            "encryption": "aes256",
            "audit_logging": True,
            "rate_limiting": True
        }

    def _design_deployment(self, requirements: Dict) -> Dict:
        return {
            "environments": ["dev", "staging", "production"],
            "strategy": "blue_green",
            "auto_scaling": True,
            "monitoring": ["prometheus", "grafana", "elk"]
        }

    def generate_report(self, workflow_results: Dict, format: str = "html") -> str:
        """Generate comprehensive workflow report"""
        if format == "html":
            return self._generate_html_report(workflow_results)
        elif format == "json":
            import json
            return json.dumps(workflow_results, indent=2, default=str)
        return ""

    def _generate_html_report(self, results: Dict) -> str:
        ecc = results.get("ecc_results", {})
        security = ecc.get("security", None)

        security_summary = ""
        if security:
            security_summary = f"""
            <div class="metric critical">{security.critical_count}<br><small>Critical</small></div>
            <div class="metric high">{security.high_count}<br><small>High</small></div>
            <div class="metric medium">{len([f for f in security.findings if f.severity.value == 'MEDIUM'])}<br><small>Medium</small></div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Enterprise Web Dev System - Workflow Report</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #1a1a2e; border-bottom: 3px solid #16213e; padding-bottom: 15px; }}
                h2 {{ color: #0f3460; margin-top: 30px; }}
                .status {{ display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: bold; }}
                .status.completed {{ background: #d4edda; color: #155724; }}
                .status.failed {{ background: #f8d7da; color: #721c24; }}
                .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
                .metric {{ padding: 25px; text-align: center; border-radius: 10px; color: white; font-size: 24px; font-weight: bold; }}
                .critical {{ background: #dc3545; }} .high {{ background: #fd7e14; }}
                .medium {{ background: #ffc107; color: #000; }} .low {{ background: #17a2b8; }}
                .phase {{ background: #e9ecef; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #16213e; }}
                .phase h3 {{ margin: 0 0 10px 0; color: #16213e; }}
                .gate-passed {{ background: #d4edda; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; }}
                .gate-failed {{ background: #f8d7da; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 Enterprise Web Development System</h1>
                <h2>Workflow Report: {results.get("workflow", "Unknown")}</h2>

                <p><strong>Project:</strong> {results.get("project", "N/A")}</p>
                <p><strong>Status:</strong> <span class="status {results.get("status", "")}">{results.get("status", "Unknown").upper()}</span></p>
                <p><strong>Start:</strong> {results.get("start_time", "N/A")}</p>

                <h2>🔒 Security Scan Results</h2>
                <div class="summary">
                    {security_summary}
                </div>

                <h2>📋 Phase Summary</h2>
                <div class="phase">
                    <h3>Phase 1: Requirements Analysis</h3>
                    <p>Functional requirements: {len(results.get("phases", {}).get("requirements", {}).get("functional", []))}</p>
                </div>

                <div class="phase">
                    <h3>Phase 2: Architecture Design</h3>
                    <p>Pattern: {results.get("phases", {}).get("architecture", {}).get("pattern", "N/A")}</p>
                    <p>Frontend: {results.get("phases", {}).get("architecture", {}).get("tech_stack", {}).get("frontend", "N/A")}</p>
                    <p>Backend: {results.get("phases", {}).get("architecture", {}).get("tech_stack", {}).get("backend", "N/A")}</p>
                </div>

                <h2>🚦 Quality Gate</h2>
                <div class="{"gate-passed" if results.get("quality_gate", {}).get("passed") else "gate-failed"}">
                    <h3>{"[OK] PASSED" if results.get("quality_gate", {}).get("passed") else "[FAIL] FAILED"}</h3>
                    {"<p>Failures: " + "<br>".join(results.get("quality_gate", {}).get("failures", [])) + "</p>" if not results.get("quality_gate", {}).get("passed") else ""}
                </div>
            </div>
        </body>
        </html>
        """
