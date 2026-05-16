"""Base agent with Anthropic LLM integration.

All specialized agents inherit from this class. It replaces the previous
f-string code-generation pattern with a structured LLM reasoning loop:
  1. Build system + task prompt from YAML spec
  2. Call Anthropic API with structured JSON output
  3. Parse response into generated files
  4. Validate output via ECCEngine
  5. Feed ECC findings back to LLM for self-correction (up to N iterations)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from anthropic import Anthropic
from jinja2 import Environment, FileSystemLoader

from ecc_tools.core.engine import ECCEngine


class BaseAgent:
    """LLM-powered agent with ECC validation feedback loop.

    Subclasses override:
      - system_prompt_template: path to Jinja2 system-prompt template
      - task_prompt_template: path to Jinja2 task-prompt template
      - _parse_response(response_json) -> dict of file_path -> content
      - _render_default(spec, project_path) -> dict (fallback when no API key)

    Args:
        config: Agent-specific configuration (tech stack preferences, etc.)
        ecc: Shared ECCEngine instance (injected, not self-created)
        model: Anthropic model ID (default: claude-sonnet-4-6)
        max_fix_iterations: Maximum ECC feedback → fix loops (default: 3)
    """

    # Subclasses should override these template paths
    system_prompt_template: str = ""
    task_prompt_template: str = ""

    def __init__(
        self,
        config: Optional[Dict] = None,
        ecc: Optional[ECCEngine] = None,
        model: str = "claude-sonnet-4-6",
        max_fix_iterations: int = 3,
    ):
        self.config = config or {}
        self.ecc = ecc or ECCEngine.get_instance("config")
        self.model = model
        self.max_fix_iterations = max_fix_iterations

        # Jinja2 environment for prompt templates
        template_dir = Path(__file__).parent / "prompts"
        self._jinja = None
        if template_dir.exists():
            self._jinja = Environment(
                loader=FileSystemLoader(str(template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )

        # Anthropic client (lazy init — only if API key is set)
        self._client: Optional[Anthropic] = None

    @property
    def client(self) -> Optional[Anthropic]:
        if self._client is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self._client = Anthropic(api_key=api_key)
        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def implement(self, spec: Dict, project_path: str) -> Dict:
        """Generate code from a specification, with ECC validation.

        Returns:
            {"status": "success"|"failed",
             "generated_files": [str, ...],
             "validation": {"passed": bool, ...},
             "iterations": int}
        """
        if self.client:
            return self._implement_with_llm(spec, project_path)
        else:
            return self._implement_fallback(spec, project_path)

    def validate_output(self, output_path: str) -> Dict:
        """Run ECC validation on generated output."""
        report = self.ecc.full_scan(output_path)

        sec_ok = report.security.critical_count == 0 if report.security else True
        stab_ok = len([i for i in report.stability if i.severity == 'critical']) == 0
        perf_ok = len([i for i in report.performance if i.severity == 'critical']) == 0

        return {
            "passed": sec_ok and stab_ok and perf_ok,
            "security": report.security,
            "stability": report.stability,
            "performance": report.performance,
            "maintainability": report.maintainability,
        }

    # ------------------------------------------------------------------
    # LLM reasoning loop
    # ------------------------------------------------------------------

    def _implement_with_llm(self, spec: Dict, project_path: str) -> Dict:
        """Core LLM loop: generate → validate → fix → repeat."""
        results: Dict[str, Any] = {
            "status": "running",
            "generated_files": [],
            "validation": {},
            "iterations": 0,
        }

        for iteration in range(1, self.max_fix_iterations + 1):
            results["iterations"] = iteration

            # Build prompt context (includes previous ECC findings on retry)
            system_prompt = self._build_system_prompt()
            task_prompt = self._build_task_prompt(spec, results.get("validation"))

            # Call Anthropic API with structured output
            response_json = self._call_llm(system_prompt, task_prompt)
            if not response_json:
                results["status"] = "failed"
                results["error"] = "LLM returned no structured output"
                return results

            # Parse structured response into files
            generated = self._parse_response(response_json, project_path)
            results["generated_files"] = generated

            # Validate with ECC
            validation = self.validate_output(project_path)
            results["validation"] = validation

            if validation["passed"]:
                results["status"] = "success"
                return results

            # Feed findings back to LLM for next iteration
            if iteration < self.max_fix_iterations:
                print(f"  [{self.__class__.__name__}] ECC issues found, "
                      f"self-correcting (iteration {iteration}/{self.max_fix_iterations})...")

        results["status"] = "failed_validation"
        return results

    def _implement_fallback(self, spec: Dict, project_path: str) -> Dict:
        """Fallback code generation when no LLM API key is configured.

        Subclasses must override _render_default() to provide
        template-based or f-string fallback output.
        """
        generated = self._render_default(spec, project_path)
        validation = self.validate_output(project_path) if generated else {"passed": True}

        return {
            "status": "success" if validation.get("passed") else "failed_validation",
            "generated_files": generated,
            "validation": validation,
            "iterations": 0,
        }

    # ------------------------------------------------------------------
    # Prompt construction (override in subclasses)
    # ------------------------------------------------------------------

    def _build_system_prompt(self) -> str:
        """Build the system prompt from Jinja2 template or defaults."""
        if self._jinja and self.system_prompt_template:
            template = self._jinja.get_template(self.system_prompt_template)
            return template.render(config=self.config, model=self.model)
        return self._default_system_prompt()

    def _build_task_prompt(self, spec: Dict, prev_validation: Dict = None) -> str:
        """Build the task/user prompt with spec and optional ECC feedback."""
        extra_context = ""
        if prev_validation:
            findings = self._format_ecc_findings(prev_validation)
            if findings:
                extra_context = (
                    "\n\n## Previous ECC Validation Issues\n"
                    "Fix the following issues in your output:\n\n"
                    f"{findings}\n"
                )

        if self._jinja and self.task_prompt_template:
            template = self._jinja.get_template(self.task_prompt_template)
            return template.render(spec=spec, config=self.config,
                                   ecc_context=extra_context)

        return json.dumps(spec, indent=2) + extra_context

    def _default_system_prompt(self) -> str:
        return (
            "You are an expert full-stack software engineer. "
            "Generate production-ready code from the provided specification. "
            "Return a JSON object mapping file paths to file contents. "
            "Follow security best practices (OWASP Top 10), write clean, "
            "well-typed code with proper error handling."
        )

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------

    def _call_llm(self, system_prompt: str, task_prompt: str) -> Optional[Dict]:
        """Call the Anthropic API with structured JSON output mode."""
        if not self.client:
            return None

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": task_prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "generated_files",
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    },
                },
            )

            # Parse JSON from the response content
            for block in response.content:
                if hasattr(block, "text"):
                    return json.loads(block.text)
                elif isinstance(block, dict) and "text" in block:
                    return json.loads(block["text"])

            return None

        except Exception as e:
            print(f"  [{self.__class__.__name__}] LLM call failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Response parsing (override in subclasses)
    # ------------------------------------------------------------------

    def _parse_response(self, response_json: Dict, project_path: str) -> List[str]:
        """Parse LLM JSON response into files on disk.

        Expected response format:
            {"path/to/file.py": "file content...", ...}

        Returns list of file paths written.
        """
        generated = []
        base = Path(project_path)

        for file_path, content in response_json.items():
            full_path = base / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(str(content), encoding="utf-8")
            generated.append(str(full_path))

        return generated

    def _render_default(self, spec: Dict, project_path: str) -> List[str]:
        """Default fallback — subclasses MUST override for template-based generation."""
        return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _format_ecc_findings(self, validation: Dict) -> str:
        """Format ECC findings for LLM feedback context."""
        lines = []

        sec = validation.get("security")
        if sec and hasattr(sec, 'findings'):
            for f in sec.findings:
                if hasattr(f.severity, 'value'):
                    sev = f.severity.value
                else:
                    sev = str(f.severity)
                if sev in ('CRITICAL', 'HIGH'):
                    lines.append(
                        f"- [{sev}] {f.rule_name}: {f.message} "
                        f"({f.file_path}:{f.line_number}). "
                        f"Fix: {f.remediation}"
                    )

        for issue in validation.get("stability", []):
            if issue.severity == 'critical':
                lines.append(
                    f"- [CRITICAL/STABILITY] {issue.message} "
                    f"({issue.file_path}:{issue.line_number}). "
                    f"Fix: {issue.recommendation}"
                )

        for issue in validation.get("performance", []):
            if issue.severity == 'critical':
                lines.append(
                    f"- [CRITICAL/PERF] {issue.message} "
                    f"({issue.file_path}:{issue.line_number}). "
                    f"Fix: {issue.optimization_strategy}"
                )

        return "\n".join(lines)
