---
name: agents-orchestration
description: PARL agent orchestration rules, decision tree, routing logic — aligned with Web Application Development Strategy v1.0
type: system
budget: always-hot
strategy_doc: web-application-development-strategy.md
---

# AGENTS.md — PARL Orchestration & Decision Tree

## PARL Model
**P**arallel **A**gent **R**einforcement **L**earning — a coordination pattern where 6 specialized Claude Code SubAgents execute independently within token budgets, feed results back to the orchestrator, and improve through structured `.learnings/` feedback loops.

## Agent Registry (aligned with Strategy Doc Section 9.3)

| Agent | Model | Budget | Scope | Parallelization |
|-------|-------|--------|-------|-----------------|
| `project-planner` | **Opus** | 32K | Principal Engineer — architecture decisions, task decomposition, risk management | Singleton (orchestrator) |
| `fastapi-architect` | **Opus** | 24K | Backend — FastAPI 0.110+, SQLAlchemy 2.0 async, Pydantic v2, OAuth2/JWT | Per-endpoint |
| `vite-react-developer` | **Sonnet** | 16K | Frontend — React 18+, TypeScript 5, Vite 5, Tailwind CSS 3, TanStack Query | Per-component |
| `security-auditor` | **Opus** | 20K | Security — OWASP Top 10, SAST/DAST, penetration testing, compliance | Per-module |
| `test-automator` | **Sonnet** | 16K | QA — pytest, Vitest, Playwright, contract testing, coverage enforcement | Per-test-type |
| `web-deployer` | **Opus** | 24K | DevOps/SRE — Docker, K8s/ECS, Terraform, GitHub Actions, Prometheus/Grafana | Per-environment |

## Decision Tree

```
INCOMING TASK
  │
  ├─ Is this an architectural decision or planning task?
  │   └─ YES → project-planner (Opus, 32K) — blocks all other agents
  │
  ├─ Is this a backend endpoint, middleware, or database task?
  │   └─ YES → fastapi-architect (Opus, 24K) — parallelize per-endpoint after OpenAPI contract
  │
  ├─ Is this a frontend component, route, or UI task?
  │   └─ YES → vite-react-developer (Sonnet, 16K) — parallelize per-component after design system
  │
  ├─ Is this touching auth, data validation, secrets, or user input?
  │   └─ YES → security-auditor (Opus, 20K) — 5 security gates, parallelize per module
  │
  ├─ Is this a test or QA task?
  │   └─ YES → test-automator (Sonnet, 16K) — parallelize unit/integration/e2e streams
  │
  ├─ Is this a deployment or infrastructure task?
  │   └─ YES → web-deployer (Opus, 24K) — parallelize per environment
  │
  └─ Unclear scope?
      └─ Route to project-planner for triage and decomposition.
```

## Development Phases (from Strategy Doc Section 4)

| Phase | Week | Goal | Key Agents |
|-------|------|------|------------|
| **Phase 0: Foundation** | 1 | Repo setup, Docker Compose, CI/CD skeleton, linting, design system | project-planner, web-deployer, fastapi-architect, vite-react-developer |
| **Phase 1: Core Features** | 2-3 | Auth system, core CRUD, basic UI — MVP delivery | All agents fan out in parallel |
| **Phase 2: Expansion** | 4-6 | Business logic, full test coverage, parallel feature streams | fastapi-architect, vite-react-developer, test-automator |
| **Phase 3: Hardening & Launch** | 7-8 | Security audit, performance optimization, production deployment | security-auditor (lead), web-deployer, all others |

## Parallel Execution Flow
1. **Orchestrator** (project-planner, Opus) receives task → decomposes into contracts.
2. **Contracts published** to `vault/02_reference/api-contracts/` (OpenAPI 3.1).
3. **Independent agents fan out**: backend (per-endpoint) || frontend (per-component) || security || tests.
4. **Security gates** (5 gates) run alongside development — block merge on CRITICAL/HIGH.
5. **Results merge** through orchestrator → integration validation against checklist (Section 9.4).
6. **Learnings captured** → `.learnings/` updated before next cycle.

## Inter-Agent Communication
- All handoffs use files in `vault/`. No in-context agent-to-agent chat.
- OpenAPI 3.1 specs are the source of truth for frontend ↔ backend boundaries.
- Frontend types generated from OpenAPI: `npx openapi-typescript`
- Security audit reports block merge until all HIGH/CRITICAL findings resolve.
- Test results publish to `vault/04_published/test-reports/` before deployment.
- Deployment gated by: all tests passing + security audit clean + staging smoke tests.

## Collaboration Matrix (from Strategy Doc Section 3.2)
| Concern | Primary Agent | Supporting Agents |
|---------|-------------|-------------------|
| API Design | fastapi-architect | project-planner (contract approval) |
| Database Schema | fastapi-architect | test-automator (test data factories) |
| UI Components | vite-react-developer | project-planner (design system alignment) |
| API Integration | vite-react-developer | fastapi-architect (OpenAPI spec) |
| Authentication Flow | fastapi-architect | security-auditor (threat model), vite-react-developer (UI) |
| Authorization (RBAC) | security-auditor | fastapi-architect (implementation) |
| Input Validation | fastapi-architect | security-auditor (bypass testing) |
| XSS Prevention | vite-react-developer | security-auditor (DOM testing) |
| Dependency Updates | security-auditor | web-deployer (CI scanning) |
| Unit Tests | test-automator | fastapi-architect / vite-react-developer |
| E2E Tests | test-automator | web-deployer (staging environment) |
| Docker Images | web-deployer | security-auditor (image scanning) |
| CI/CD Pipeline | web-deployer | test-automator (test stage), security-auditor (scan stage) |
| Incident Response | web-deployer | security-auditor (forensics) |
