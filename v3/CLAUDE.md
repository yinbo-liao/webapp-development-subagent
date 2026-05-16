# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Enterprise Web Development System v2.0 — a Python 3.11+ multi-agent code generation system with integrated Enterprise Code Compliance (ECC) static analysis. Agents generate full-stack web application code (React/TypeScript frontend, FastAPI/Python backend, PostgreSQL database, Docker/K8s infra), then ECC tools scan the output for security, stability, performance, and maintainability issues before passing quality gates.

When `ANTHROPIC_API_KEY` is set in the environment, agents use structured LLM generation with an ECC feedback loop (generate → validate → fix → repeat, up to 3 iterations). Without an API key, agents fall back to Jinja2 template-based generation.

## Commands

```bash
# Install system dependencies + package (editable)
pip install -r requirements.txt && pip install -e .

# After pip install -e ., use the ewds CLI
ewds --workflow new-project --project ./my-app --requirements requirements-example.yaml
ewds --ecc-scan --project ./my-app --output html

# Run demo (generates demo-output/)
python demo.py

# Workflows
python main.py --workflow new-project --project ./my-app --requirements requirements-example.yaml
python main.py --workflow feature-dev --project ./my-app --feature "user-authentication"

# ECC scanning
python main.py --ecc-scan --project ./my-app --output html          # Full project scan
python main.py --ecc-scan --file path/to/file.py --output json      # Single-file scan
python main.py --ecc-scan --tools security stability                # Specific tools only
python main.py --ecc-scan --pre-commit --project .                  # CI hook (exit 1 on fail)

# Additional flags
python main.py --workflow new-project --project ./my-app --verbose  # Debug
python main.py --workflow new-project --project ./my-app --dry-run  # Preview
python main.py --workflow new-project --project ./my-app --skip-ecc # Skip validation

# LLM-powered generation (set env var first)
export ANTHROPIC_API_KEY="sk-ant-..."
python main.py --workflow new-project --project ./my-app

# Development
make lint    # flake8 + mypy + bandit on agents/, ecc_tools/, shared/
make format  # black + isort
make test    # pytest --cov
make pre-commit  # ECC scan that blocks on critical/high findings
make scan-file FILE=path/to/file.py
```

## Architecture

### Three-layer design

```
CLI (main.py) → Orchestrator → Agent Registry → Specialized Agents
                     │                              │
                     ▼                              ▼
              ECCEngine (singleton)    BaseAgent (LLM loop / Jinja2 fallback)
              ├─ SASTEngine           ├─ FrontendAgent
              ├─ StabilityAnalyzer    ├─ BackendAgent (Jinja2 .j2 templates)
              ├─ PerformanceProfiler  ├─ DatabaseAgent
              └─ MaintainabilityAnalyzer ├─ QAAgent
                                         └─ DevOpsAgent
```

### Directory layout

```
main.py                         # CLI with --file, --pre-commit, --tools flags
demo.py                         # Demo workflow (writes to demo-output/)
setup.py                        # Registers `ewds` console_scripts entry point
requirements.txt                # System deps (pyyaml, anthropic, pydantic, ...)
requirements-generated.txt      # Deps for generated projects (fastapi, sqlalchemy, ...)
test-output/                    # Pre-generated demo output (committed for inspection)

agents/
  base_agent.py                 # LLM-powered base agent with ECC feedback loop
  registry.py                   # Config-driven agent discovery (from config/agents.yaml)
  orchestrator/main.py          # 7-phase workflow, agent registry, quality gates
  backend_agent/                # FastAPI code generation (Jinja2 + LLM)
    agent.py
    templates/                  # Jinja2 .j2 templates (model, schema, router, service, core, middleware)
  frontend_agent/
    agent.py
    templates/                  # component.tsx.j2, component.types.ts.j2, component.test.tsx.j2
  database_agent/
    agent.py
    templates/                  # database.py.j2
  qa_agent/
    agent.py
    templates/                  # pytest.ini.j2, conftest.py.j2
  devops_agent/
    agent.py
    templates/                  # Dockerfile.j2, docker-compose.yml.j2
  prompts/                      # Shared LLM prompt templates

ecc_tools/
  core/
    engine.py                   # ECCEngine singleton — shared, thread-safe, incremental scanning
    config.py                   # ECCConfig — deep-merges agents.yaml + ecc.yaml
    logger.py                   # Structured logging (structlog)
    exceptions.py               # ECCToolError hierarchy
    metrics.py                  # MetricsCollector
  security/
    sast_engine.py              # SAST: 7 vuln categories, taint analysis, SARIF/JSON/HTML reports
    rules/                      # python_security.yaml, secret_patterns.yaml
    compliance/                 # owasp_mapper.py, cwe_classifier.py
  stability/
    static_analyzer.py          # Complexity, error handling, type coverage, resource leaks
    rules/complexity.yaml
  performance/
    profiler.py                 # Algorithm, memory, DB N+1, caching, async patterns
    rules/performance_patterns.yaml
  maintainability/
    code_metrics.py             # Halstead, MI, code smells, SOLID, documentation
    rules/code_quality.yaml
  reporting/
    report_generator.py         # Unified SARIF/JSON/HTML report generation

shared/
  protocols/agent_protocol.py   # Pydantic v2 inter-agent messages (MessageType, TaskAssignment, TaskResult)
  knowledge_base/tech_stack_db.py  # Tech stack metadata + recommendation logic
  templates/AGENTS.md.j2        # Renders AGENTS.md into each generated project

workflows/
  new-project.yaml              # 7-phase YAML workflow with DAG dependencies
  base_workflow.py              # Workflow parser/validator with cycle detection

config/
  agents.yaml                   # Agent capabilities, quality gate thresholds (0 critical, 5 high max)
  ecc.yaml                      # ECC thresholds (complexity, nesting, type coverage, etc.)
```

### Workflow phases

1. **Requirements Analysis** — decomposes YAML requirements into tasks
2. **Architecture Design** — selects tech stack, pattern, component tree via `shared/knowledge_base/tech_stack_db.py`
3. **Parallel Implementation** — `ThreadPoolExecutor` dispatches agents concurrently (300s timeout)
4. **ECC Scanning** — `ECCEngine.full_scan()` runs all 4 analyzers via the shared singleton
5. **Quality Gate** — `QualityGateResult` centralizes evaluation; blocks on critical findings
6. **Testing** — QA agent generates and runs test suites
7. **Deployment** — DevOps agent generates infrastructure config

### Agent pattern

All agents accept `config: Dict` and `ecc: ECCEngine` via constructor (dependency injection).
Agents no longer instantiate their own ECC tools — they use the shared `ECCEngine`.

- **`BaseAgent`** (agents/base_agent.py): LLM-powered generation with structured JSON output.
  - `implement(spec, project_path)` → generate → validate → fix loop
  - `validate_output(output_path)` → ECCEngine.full_scan → quality check
  - Falls back to `_render_default()` when no API key set
- **`BackendAgent(BaseAgent)`**: Uses Jinja2 `.j2` templates for FastAPI code
- **`FrontendAgent`**, **`DatabaseAgent`**, **`QAAgent`**, **`DevOpsAgent`**: Use Jinja2 templates with f-string fallbacks
- **Architecture invariant**: Only BackendAgent extends BaseAgent (LLM-enabled). Other agents use template-based generation but share the ECCEngine.

### ECC tools pattern

- **`ECCEngine`** (ecc_tools/core/engine.py): Thread-safe singleton facade.
  - `full_scan(project_path)` → `ECCReport` with all four analysis results
  - `scan_incremental(project_path)` → returns None if no files changed (hash-based)
  - `scan_single_file(file_path)` → `ECCReport` for a single file
  - `quality_gate_check(project_path, gates)` → `QualityGateResult`
- **`ECCReport`**: Aggregated results with `evaluate_gates()` method
- **`QualityGateResult`**: Centralized pass/fail with per-category checks and failure messages
- All analyzers: `analyze_project(project_path)` / `analyze_file(file_path)`, returning dataclass findings
- Structured error collection: `ScanResult.parse_errors` and `ScanResult.scan_errors` capture failures that were previously silently swallowed

### Key design decisions

- **Python 3.11+** — `find_packages()`, modern typing
- **ECCEngine singleton** — all agents share one instance; no redundant tool construction; hash-based incremental scanning
- **Jinja2 for code generation** — templates in `agents/*/templates/`; fallback to f-strings when templates missing
- **LLM integration** — `BaseAgent` uses Anthropic SDK with structured JSON output; self-corrects from ECC findings up to 3 iterations
- **Generated code uses async SQLAlchemy 2.0 + Pydantic v2** — `mapped_column()` style, `model_config` instead of `class Config`
- **QA generates SQLite in-memory test fixtures** — designed for CI, not PostgreSQL
- **Quality gates block on security/stability/performance criticals** — maintainability is non-blocking
- **YAML rule files externalize ECC thresholds** — enables customization without code changes
- **Agent registry** — config-driven from `config/agents.yaml`; no hardcoded agent list in CLI
- **Split requirements** — `requirements.txt` (system) vs `requirements-generated.txt` (generated projects)
- **Correctness fix** — `_is_in_context_manager()` uses parent-map traversal; `_get_enclosing_function()` uses line-range to find innermost function
