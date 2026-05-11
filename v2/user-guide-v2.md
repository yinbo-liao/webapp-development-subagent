# Claude Agents Optimized — User Guide v2.6.0

## Document Owner
yinbo-liao · yinbo.leon@gmail.com · Version 2.6.0 · 2026-05-11

---

## Table of Contents

1. [Overview](#1-overview)
2. [Quick Start](#2-quick-start)
3. [Directory Map](#3-directory-map)
4. [Dashboard Reference — claude-agents-optimized.html](#4-dashboard-reference)
5. [Agent Usage](#5-agent-usage)
6. [PARL Workflow](#6-parl-workflow)
7. [Vault System](#7-vault-system)
8. [Self-Improving System](#8-self-improving-system)
9. [Configuration Reference](#9-configuration-reference)
10. [Daily Operations](#10-daily-operations)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Overview

**Claude Agents Optimized** is a PARL (Parallel Agent Reinforcement Learning) coordination framework for Claude Code. It structures 6 specialized SubAgents into a unified development team with:

- **Always-hot core context** — SOUL.md, AGENTS.md, MEMORY.md, TOOLS.md load on every session
- **6 agent definitions** — Opus for planner/backend/security/deployer; Sonnet for frontend/testing
- **6-section vault** — On-demand reference from architecture decisions to runbooks
- **Self-improving loop** — Errors → learnings → prevention across sessions
- **4 YAML configs** — Compaction, caching (75-83% savings), parallel execution, security isolation
- **Interactive HTML dashboard** — `claude-agents-optimized.html` with 9 panels

### Architecture at a Glance

```
project-planner (Opus · 32K)  ← Orchestrator
    │
    ├── fastapi-architect (Opus · 24K)    ← Backend, per-endpoint
    ├── vite-react-developer (Sonnet · 16K) ← Frontend, per-component
    ├── security-auditor (Opus · 20K)     ← Security gate, 5 gates
    ├── test-automator (Sonnet · 16K)     ← Quality gate, 3 test types
    └── web-deployer (Opus · 24K)         ← DevOps, per-environment

Total budget: 132,000 tokens · Max concurrency: 15 work streams
```

---

## 2. Quick Start

### 2.1 Open the Dashboard

```bash
# Windows
start claude-agents-optimized.html

# macOS
open claude-agents-optimized.html

# Linux
xdg-open claude-agents-optimized.html

# Or serve for sharing
python -m http.server 8080
# Visit: http://localhost:8080/claude-agents-optimized.html
```

### 2.2 Install Agent Files

```bash
# Create agent directory
mkdir -p ~/.claude/agents/your-project/

# Copy core context (always hot)
cp claude-agents-optimized/SOUL.md ~/.claude/agents/your-project/
cp claude-agents-optimized/AGENTS.md ~/.claude/agents/your-project/
cp claude-agents-optimized/MEMORY.md ~/.claude/agents/your-project/
cp claude-agents-optimized/TOOLS.md ~/.claude/agents/your-project/

# Copy agent definitions
cp claude-agents-optimized/agents/*.md ~/.claude/agents/your-project/
```

### 2.3 Initialize Vault (per project)

```bash
# Copy vault structure to your project
cp -r claude-agents-optimized/vault/* ~/your-project/vault/
cp -r claude-agents-optimized/.learnings ~/your-project/
cp claude-agents-optimized/progress.txt ~/your-project/
cp claude-agents-optimized/*.yaml ~/your-project/
```

### 2.4 Start a Session

```
> "Read progress.txt and resume from the last checkpoint"
> "Use project-planner to plan the next feature based on current progress"
```

---

## 3. Directory Map

```
claude-agents-optimized/
│
├── 🧠 CORE CONTEXT (Always Hot — loaded every session)
│   ├── SOUL.md                  Identity, prime directives, target metrics
│   ├── AGENTS.md                PARL orchestration, decision tree, agent registry
│   ├── MEMORY.md                Index pointers to user/feedback/project/reference memory
│   └── TOOLS.md                 File ops, agent coordination, config tools reference
│
├── 👥 AGENT DEFINITIONS (Warm — loaded per task)
│   ├── agents/project-planner.md      Opus · 32K · Principal Engineer
│   ├── agents/fastapi-architect.md    Opus · 24K · Backend Specialist
│   ├── agents/vite-react-developer.md  Sonnet · 16K · Frontend Specialist
│   ├── agents/security-auditor.md     Opus · 20K · Security Gate
│   ├── agents/test-automator.md       Sonnet · 16K · Quality Gate
│   └── agents/web-deployer.md         Opus · 24K · DevOps/SRE
│
├── 📚 VAULT (On-Demand Reference — read when needed)
│   ├── vault/01_thinking/       Architecture decisions (ADRs), MOCs
│   ├── vault/02_reference/      API contracts, DB schema, design system, security, testing
│   ├── vault/03_creating/       Active feature specs
│   ├── vault/04_published/      Final docs, test reports, deploy logs
│   ├── vault/05_archive/        Historical records (retention: 30d-∞)
│   └── vault/06_system/         Runbooks, incident response, procedures
│
├── 🧬 SELF-IMPROVING (.learnings/)
│   ├── corrections.md           Error corrections with root cause + prevention
│   ├── ERRORS.md                Failure pattern catalog
│   ├── LEARNINGS.md             Discoveries and insights
│   ├── FEATURE_REQUESTS.md      Backlog with priority and effort
│   └── security/                Security patterns, remediation templates
│
├── ⚙️ CONFIGURATION (YAML)
│   ├── compaction-rules.yaml    Context compression: keep/compress/discard tiers
│   ├── cache-policy.yaml        75-83% token savings, TTL per cache tier
│   ├── parallel-config.yaml     Concurrency limits, dependency resolution, timeouts
│   └── security-isolation.yaml  Per-agent sandbox, blocked commands, secrets detection
│
└── 📋 OPERATIONAL
    ├── progress.txt             Session checkpoint (LIFO stack)
    ├── README.md                Full framework documentation
    └── claude-agents-optimized.html  Interactive dashboard
```

### File Temperature Legend

| Badge | Meaning | When Loaded |
|-------|---------|-------------|
| **HOT** | Always in context | Every session start |
| **WARM** | Loaded on demand | When agent is assigned a task |
| **COLD** | Read when needed | Only when relevant to current task |

---

## 4. Dashboard Reference — claude-agents-optimized.html

The interactive HTML dashboard has **9 panels** accessible via the top navigation bar.

### 4.1 Dashboard
Default landing page. Shows:
- **Agent Status Bar**: All 6 agents with online/busy indicators and token budgets
- **Agent Cards**: Click to view details or select for prompt building
- **Architecture Diagram**: SVG showing orchestrator → specialist flow
- **Key Metrics**: Time-to-MVP (2-3 wks), Coverage (>90%/>80%), OWASP (0 Crit), Availability (99.9%)

### 4.2 Strategy Doc
Embedded content from the master strategy document:
- Executive Summary with target metrics table
- Full technology stack (18 technologies across 6 layers)
- Development phases (Phase 0-3, Weeks 1-8) with agent assignments

### 4.3 SubAgents
Agent team details:
- **Hierarchy Diagram**: SVG showing orchestrator → 4 specialists → deployer
- **Collaboration Matrix**: 14 rows mapping concerns to primary + supporting agents

### 4.4 Architecture
System architecture visualization:
- **Layered diagram**: Client → CDN → Load Balancer → Application (FastAPI + React) → Data (PostgreSQL + Redis + Celery)

### 4.5 Workflow
6-phase feature development flow:
- Planning → API Contract → Parallel Build (Backend || Frontend) → Testing → Security Gate → Deploy → Monitor
- Remediation loop (FAIL → back to Build) and gate decision (PASS → Deploy)

### 4.6 Prompt Builder
Interactive prompt generator:
- **4 selectors**: Agent, Task Type, Complexity, Priority
- **Live preview**: Updates in real-time as selections change
- **Copy button**: One-click to clipboard
- **Quick templates**: 6 pre-built commands for each agent

### 4.7 Security
Security governance:
- **5 Security Gates table**: SAST, Dependency Scan, Container Scan, Penetration Test, Code Review
- **10-item interactive checklist**: Check off per-feature security requirements

### 4.8 Deployment
Operations panel:
- **Pipeline**: Local → CI (GitHub Actions) → Staging (Terraform) → Production (Canary)
- **Rollback Procedures**: 4 scenarios with recovery times (< 30s to < 1hr)
- **Incident Response**: SEV 1 (Site Down) and SEV 2 (Degraded) runbooks

### 4.9 File Map
Project structure reference:
- Agent file locations in `~/.claude/agents/your-project/`
- Full directory tree of `claude-agents-optimized/`
- **Integration Checklist**: 10 items tracking Phase 0 setup progress

### Dashboard Shortcuts
| Action | Shortcut |
|--------|----------|
| Search all docs | `Ctrl+K` |
| Close search | `Esc` |
| Jump to Prompt Builder | Click "Select" on any agent card |
| View agent details | Click "Details" on any agent card |

---

## 5. Agent Usage

### 5.1 project-planner (Opus · 32K · Singleton)

**When to use**: Any architectural decision, task decomposition, or cross-team coordination.

```bash
> "Use project-planner to create technical spec for [feature]"
> "Use project-planner to estimate effort and identify risks"
> "Use project-planner to decompose [epic] into parallel work streams"
> "Use project-planner to set up repository structure and development standards"
```

**Process**: 5 phases — Discovery → Decomposition → Contract Publishing → Fan-Out → Integration

**Output**: YAML plan with streams, contracts, dependencies, budgets, and risk areas.

### 5.2 fastapi-architect (Opus · 24K · Per-Endpoint)

**When to use**: Any backend endpoint, middleware, database schema, or API contract.

```bash
> "Use fastapi-architect to design API for [resource]"
> "Use fastapi-architect to implement [feature] with full test coverage"
> "Use fastapi-architect to optimize [query] for N+1 problem"
> "Use fastapi-architect to create database migration for [schema change]"
```

**Tech stack**: Python 3.12+, FastAPI 0.110+, SQLAlchemy 2.0 async, Pydantic v2, Alembic, OAuth2+JWT, Celery+Redis.

**Output per endpoint**: `router.py` + `models.py` + `service.py` + `repository.py` + tests.

### 5.3 vite-react-developer (Sonnet · 16K · Per-Component)

**When to use**: Any frontend component, route, state management, or UI integration.

```bash
> "Use vite-react-developer to build [component] with loading/error states"
> "Use vite-react-developer to integrate [API] with TanStack Query"
> "Use vite-react-developer to implement responsive [page]"
> "Use vite-react-developer to add accessibility audit fixes for [component]"
```

**Tech stack**: React 18+, TypeScript 5 strict, Vite 5, Tailwind CSS 3, Zustand, TanStack Query, React Hook Form + Zod, TanStack Router.

**Output per component**: `index.tsx` + `types.ts` + `hooks.ts` + `*.test.tsx` + skeletons + error boundaries.

### 5.4 security-auditor (Opus · 20K · Per-Module)

**When to use**: Any security review, vulnerability assessment, or pre-deployment audit.

```bash
> "Use security-auditor to review [file/PR] for OWASP compliance"
> "Use security-auditor to perform penetration test on auth flow"
> "Use security-auditor to scan dependencies for vulnerabilities"
> "Use security-auditor to create threat model for [new feature]"
```

**5 Security Gates**: SAST → Dependency Scan → Container Scan → Penetration Test → Code Review.

**Output**: Audit report YAML with findings (CRITICAL/HIGH/MEDIUM/LOW), OWASP mapping, and remediation steps.

### 5.5 test-automator (Sonnet · 16K · Per-Test-Type)

**When to use**: Any test creation, coverage improvement, or CI test gate configuration.

```bash
> "Use test-automator to write unit tests for [module]"
> "Use test-automator to set up E2E tests for [user journey]"
> "Use test-automator to improve coverage in [area]"
> "Use test-automator to implement contract tests between [frontend] and [backend]"
```

**Test pyramid**: 60% Unit (pytest/Vitest) → 30% Integration (HTTPX/MSW) → 10% E2E (Playwright).

**Coverage targets**: >90% backend (services 90%, routers 85%), >80% frontend (components 80%, utilities 95%).

### 5.6 web-deployer (Opus · 24K · Per-Environment)

**When to use**: Any infrastructure, CI/CD, deployment, or monitoring task.

```bash
> "Use web-deployer to containerize application with Docker"
> "Use web-deployer to set up GitHub Actions CI/CD pipeline"
> "Use web-deployer to deploy to [environment] with monitoring"
> "Use web-deployer to configure auto-scaling and load balancing"
```

**Environment progression**: Local (docker-compose) → CI (GitHub Actions) → Staging (blue-green) → Production (canary).

**Recovery times**: Bad deploy < 30s, DB issue < 5min, Security breach < 10min, Data corruption < 1hr.

---

## 6. PARL Workflow

### 6.1 Decision Tree

```
INCOMING TASK
  ├─ Architectural decision? → project-planner (blocks all others)
  ├─ Backend endpoint/DB?    → fastapi-architect (per-endpoint parallel)
  ├─ Frontend component/UI?  → vite-react-developer (per-component parallel)
  ├─ Auth/data/input/secrets? → security-auditor (per-module, gates deploy)
  ├─ Test/QA task?           → test-automator (unit || integration || e2e)
  ├─ Deployment/infra?       → web-deployer (per-environment parallel)
  └─ Unclear?                → Route to project-planner for triage
```

### 6.2 Parallel Execution Flow

```
1. project-planner receives requirement → decomposes into contracts
2. Contracts published to vault/02_reference/api-contracts/ (OpenAPI 3.1)
3. Independent agents fan out in parallel:
   - fastapi-architect (endpoint 1) || fastapi-architect (endpoint 2)
   - vite-react-developer (component 1) || vite-react-developer (component 2)
   - security-auditor runs alongside development
   - test-automator (unit) || test-automator (integration) || test-automator (e2e)
4. Results merge through orchestrator → integration validation
5. Learnings captured to .learnings/ → next session benefits
```

### 6.3 Phase Alignment

| Phase | Week | Primary Agents | Status |
|-------|------|---------------|--------|
| **0: Foundation** | 1 | project-planner, web-deployer | Docker, CI/CD, linting, design system |
| **1: Core Features** | 2-3 | All agents (parallel) | Auth, CRUD, basic UI → MVP |
| **2: Expansion** | 4-6 | fastapi-architect, vite-react-developer, test-automator | Business logic, full coverage |
| **3: Hardening** | 7-8 | security-auditor (lead), web-deployer, all | Pen test, perf, production |

### 6.4 Inter-Agent Communication

- All handoffs through `vault/` files — never in-context agent-to-agent chat
- OpenAPI 3.1 specs are the source of truth for frontend ↔ backend
- Frontend types generated: `npx openapi-typescript http://localhost:8000/openapi.json`
- Security audit blocks merge on CRITICAL/HIGH
- Tests publish to `vault/04_published/test-reports/`
- Deployment gated: all tests green + security clean + staging smoke tests

---

## 7. Vault System

### 7.1 Section Reference

| Section | Purpose | Hot/Cold | When to Read |
|---------|---------|----------|-------------|
| `01_thinking` | ADRs, MOCs, tech-debt | Cold | Before architectural changes |
| `02_reference` | API contracts, DB schema, design system, security, testing | Cold | During implementation |
| `03_creating` | Active feature specs | Cold | When starting new features |
| `04_published` | Shipped docs, test reports, deploy logs | Cold | For reference/audit |
| `05_archive` | Deprecated ADRs, old features | Cold (rarely) | For historical context |
| `06_system` | Runbooks, procedures, incident response | Cold | During operations/incidents |

### 7.2 Vault Operations

**Writing a new ADR** (in `01_thinking`):
```markdown
---
adr: 1
status: proposed
date: 2026-05-11
deciders: [project-planner]
---

# ADR-1: Title

## Context
<Problem and constraints>

## Decision
<What we chose and why>

## Alternatives Considered
- Option A: ... — Rejected because ...

## Consequences
- Positive: ...
- Negative: ...
```

**Publishing a feature** (from `03_creating` → `04_published`):
1. Feature complete and tested
2. Move spec file from `03_creating/` to `04_published/feature-docs/`
3. Regenerate API docs from OpenAPI spec
4. Archive test reports

**Archiving** (to `05_archive`):
1. Add archive metadata (date, reason, superseded_by)
2. Move to `05_archive/`
3. Update any references in `01_thinking/`

---

## 8. Self-Improving System

### 8.1 The Learning Loop

```
Agent makes error
  → Logged to .learnings/ERRORS.md (with pattern categorization)
  → Correction created in .learnings/corrections.md (root cause + fix + prevention)
  → If security-related → pattern extracted to .learnings/security/
  → Next session: SOUL.md + AGENTS.md reference the learned patterns
  → Error prevented next time
```

### 8.2 File Purposes

| File | What Goes In | Format |
|------|-------------|--------|
| `ERRORS.md` | Failure patterns with category, symptoms, root cause | ERR-number |
| `corrections.md` | Specific fixes with agent, severity, prevention | Date + summary |
| `LEARNINGS.md` | Positive discoveries and insights | LRN-number |
| `FEATURE_REQUESTS.md` | User backlog with priority and effort | FR-number |
| `security/README.md` | Vulnerability patterns + remediation templates | Free-form |

### 8.3 When to Write

- **After every error**: Write to `corrections.md` before retrying
- **Pattern detected** (same error 2+ times): Create entry in `ERRORS.md`
- **New insight gained**: Add to `LEARNINGS.md`
- **User requests feature**: Log to `FEATURE_REQUESTS.md`
- **Security finding**: Document pattern in `security/`

---

## 9. Configuration Reference

### 9.1 compaction-rules.yaml
Controls what context survives when token budget runs low.

| Tier | Files | Strategy |
|------|-------|----------|
| **Always Keep** | SOUL, AGENTS, TOOLS, progress.txt | Retain fully |
| **Compress** | Vault thinking, reference, agent defs | Keep 30%, extract key points |
| **Discard** | Archive, learnings, test reports, deploy logs | Re-read on demand |

**Triggers**: 85% context usage, < 5K tokens remaining, 3 idle turns.

### 9.2 cache-policy.yaml
Strategic caching for token savings.

| Cache | TTL | Savings |
|-------|-----|---------|
| Static Core (SOUL, AGENTS, TOOLS, MEMORY) | Session | 85% |
| Agent Definitions | Session | 80% |
| Vault Reference | 5 turns | 75% |
| Vault Thinking | 3 turns | 70% |
| Learnings | 10 turns | 90% |

**Target**: 79% average token reduction.

### 9.3 parallel-config.yaml
PARL execution concurrency limits.

| Agent | Concurrency | Note |
|-------|------------|------|
| project-planner | 1 | Singleton orchestrator |
| fastapi-architect | 3 | Per-endpoint |
| vite-react-developer | 4 | Per-component |
| security-auditor | 2 | Per-module |
| test-automator | 3 | Per-test-type |
| web-deployer | 2 | Per-environment |

**Timeouts**: Agent 600s, Pipeline 3600s. **Retry**: 2 max, exponential backoff.

### 9.4 security-isolation.yaml
Per-agent sandbox rules.

| Agent | Can Write | Cannot Write |
|-------|-----------|-------------|
| security-auditor | `.learnings/security/`, audit-reports/ | `src/`, `vault/02_reference/` |
| project-planner | `vault/01_thinking/`, `vault/03_creating/` | `src/` |
| fastapi-architect | `src/api/`, `src/db/`, `tests/` | `src/frontend/`, `.env*` |
| vite-react-dev | `src/components/`, `src/hooks/` | `src/api/`, `.env*` |
| test-automator | `test-reports/`, `.learnings/ERRORS.md` | `src/` |
| web-deployer | `deployment-logs/` | `src/` |

**Globally blocked**: `git push --force main`, `chmod 777`, `rm -rf /`, reverse shells, fork bombs.

---

## 10. Daily Operations

### 10.1 Session Start

```bash
# 1. Open dashboard
start claude-agents-optimized.html

# 2. In Claude Code, warm up and restore
> "Read SOUL.md, AGENTS.md, TOOLS.md"
> "Read progress.txt and resume from last checkpoint"
```

### 10.2 Morning Planning

```bash
> "Use project-planner to summarize current progress and identify blockers"
> "Use project-planner to prioritize today's tasks based on phase goals"
```

### 10.3 Development Session

```bash
# Decompose and fan out
> "Use project-planner to plan [feature] — publish contracts to vault"

# Parallel implementation
> "Use fastapi-architect to implement [endpoint] per contract [path]"
> "Use vite-react-developer to build [component] per spec [path]"

# Continuous quality
> "Use test-automator to run full test suite and report coverage gaps"
> "Use security-auditor to scan changed files for vulnerabilities"
```

### 10.4 Pre-Commit

```bash
> "Use test-automator to verify all tests pass"
> "Use security-auditor to scan this commit for secrets and vulnerabilities"
```

### 10.5 End of Session

```bash
> "Update progress.txt with today's checkpoint"
> "Log any learnings or errors to .learnings/"
```

### 10.6 Weekly Review

```bash
> "Use project-planner to review this week's ADRs and update strategy doc if needed"
> "Review .learnings/ERRORS.md — promote recurring patterns to SOUL.md if needed"
> "Check security-isolation.yaml and compaction-rules.yaml for tuning"
```

---

## 11. Troubleshooting

### Dashboard Issues

| Problem | Solution |
|---------|----------|
| Dashboard won't open | Ensure file is `.html`, open with browser (not text editor) |
| Blank page | Check browser console (F12). File must be served or opened directly |
| Search not working | Type at least 2 characters. `Ctrl+K` activates search |
| SVG diagrams broken | Use modern browser (Chrome, Firefox, Edge, Safari) |
| Prompt builder not updating | JavaScript must be enabled. Refresh page |

### Agent Issues

| Problem | Solution |
|---------|----------|
| Agent file not found | Verify file exists in `~/.claude/agents/your-project/` |
| Agent exceeds token budget | Decompose task into smaller pieces via project-planner |
| Agent output conflicts | Check `parallel-config.yaml` — sequentialize conflicting writes |
| Security gate blocks deploy | Check audit report for CRITICAL/HIGH findings — fix, then re-audit |
| Test coverage drops | Check `.learnings/ERRORS.md` for coverage gap patterns |

### Vault Issues

| Problem | Solution |
|---------|----------|
| Contract mismatch | Validate with `npx openapi-diff`. Update both frontend and backend |
| ADR conflict | Check `01_thinking/` for superseding ADRs. Latest status wins |
| Missing reference | Read `vault/02_reference/` README files for index |

### Configuration Issues

| Problem | Solution |
|---------|----------|
| Context keeps compacting | Increase `context_usage_pct` threshold in `compaction-rules.yaml` |
| Cache misses | Check file modification times — cache invalidates on edit |
| Parallel tasks hang | Check dependency resolution in `parallel-config.yaml` |
| Agent blocked from writing | Verify `security-isolation.yaml` allows write to target path |

### Recovery Commands

```bash
# Reset session and restore from checkpoint
> "Clear context, re-read SOUL.md + AGENTS.md + TOOLS.md"
> "Read progress.txt — what was the last completed checkpoint?"

# Force re-read everything (skip cache)
> "Ignore cache. Re-read all agent definitions and vault references."

# Emergency rollback
> "Use web-deployer to execute rollback — see vault/06_system/rollback-runbook.md"
```

---

## Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| PARL Dashboard | `claude-agents-optimized.html` | Interactive agent management |
| Framework README | `claude-agents-optimized/README.md` | Full framework documentation |
| Strategy Document | `../v1/web-application-development-strategy.md` | Master development strategy |
| v1 Command Center | `../v1/subagent-command-center.html` | v1 SubAgent dashboard |
| v1 User Guide | `../v1/user_guide.md` | v1 Command Center guide |
| Agent Files (6) | `claude-agents-optimized/agents/` | Agent definitions |
| Installed Agents | `~/.claude/agents/your-project/` | Active Claude Code agents |

---

*Guide maintained by yinbo-liao. Version 2.6.0. Updated per PARL framework evolution.*
