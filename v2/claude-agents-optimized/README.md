# Claude Agents Optimized — PARL Agent Mesh

> **Version 2.6.0** | A parallel agent orchestration framework for Claude Code

## What Is This?

Claude Agents Optimized is a structured framework for coordinating multiple Claude agents to build software projects in parallel. It uses the **PARL** (Parallel Agent Reinforcement Learning) model to decompose complex tasks, fan out work across specialized agents, and reassemble results into shippable code.

## Architecture

```
                     ┌──────────────────┐
                     │  project-planner  │  ← Orchestrator (32K budget)
                     │  Decompose & route │
                     └────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
     ┌────────▼────────┐ ┌───▼──────────┐ ┌──▼───────────┐
     │ fastapi-architect│ │vite-react-dev │ │security-auditor│
     │   Backend (24K)  │ │ Frontend (16K)│ │  Security (20K)│
     └────────┬────────┘ └───┬──────────┘ └──┬───────────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
                     ┌────────▼────────┐
                     │ test-automator   │  ← QA Gate (16K)
                     └────────┬────────┘
                              │
                     ┌────────▼────────┐
                     │  web-deployer    │  ← DevOps (24K)
                     └─────────────────┘
```

## Directory Map

| Path | Purpose | Hot/Cold |
|------|---------|----------|
| `SOUL.md` | Identity + inviolable rules | Always hot |
| `AGENTS.md` | PARL orchestration + decision tree | Always hot |
| `MEMORY.md` | Memory index pointers | Always hot |
| `TOOLS.md` | Tool quick reference | Always hot |
| `agents/` | Agent definition files | Warm (loaded per task) |
| `vault/01_thinking/` | Architecture decisions, MOCs | On-demand |
| `vault/02_reference/` | API contracts, schemas, guidelines | On-demand |
| `vault/03_creating/` | Active feature specs | On-demand |
| `vault/04_published/` | Final documentation | On-demand |
| `vault/05_archive/` | Historical records | Cold |
| `vault/06_system/` | Runbooks, procedures | On-demand |
| `.learnings/` | Self-improving feedback loop | On-demand (appended) |
| `compaction-rules.yaml` | Context compression config | Warm |
| `cache-policy.yaml` | Token savings config (75-83%) | Warm |
| `parallel-config.yaml` | PARL execution settings | Warm |
| `security-isolation.yaml` | Security sandbox rules | Warm |
| `progress.txt` | Session checkpoint | Always hot |

## Quick Start

### 1. Initialize a Project
```
Load SOUL.md + AGENTS.md → Read progress.txt → Ready
```

### 2. Submit a Task
```
User: "Build a user registration flow"
  → project-planner decomposes
  → Contracts published to vault/02_reference/
  → Agents fan out: backend → frontend → security → tests
  → Results integrated → Deployed
```

### 3. Parallel Execution
Independent work runs simultaneously:
- Backend endpoint #1 || Backend endpoint #2 || Frontend component #1
- Security audit runs alongside development
- Unit tests || Integration tests || E2E tests

## Agent Budgets

| Agent | Token Budget | Parallel Capacity |
|-------|-------------|-------------------|
| project-planner | 32,000 | 1 (singleton) |
| fastapi-architect | 24,000 | 3 concurrent endpoints |
| vite-react-developer | 16,000 | 4 concurrent components |
| security-auditor | 20,000 | 2 concurrent modules |
| test-automator | 16,000 | 3 concurrent test types |
| web-deployer | 24,000 | 2 concurrent environments |

## Configuration

All configuration is in YAML files at the root level:
- **compaction-rules.yaml** — What to keep/compress/discard when context fills
- **cache-policy.yaml** — Strategic caching for 75-83% token savings
- **parallel-config.yaml** — Concurrency limits and dependency resolution
- **security-isolation.yaml** — Per-agent sandbox and access controls

## The Self-Improving Loop

```
Agent makes error
  → Logged to .learnings/ERRORS.md
  → Correction created in .learnings/corrections.md
  → Pattern extracted → .learnings/security/ if relevant
  → Next session: SOUL.md + AGENTS.md pick up the pattern
  → Error prevented next time
```

## Non-Negotiables (from SOUL.md)

1. **Decompose before delegate** — No agent gets a task larger than its budget.
2. **Parallel where possible** — Identify independent work, fan out.
3. **Contracts over assumptions** — Explicit API contracts at every boundary.
4. **Fail fast, learn faster** — `.learnings/` updated before retries.
5. **Context is currency** — Cache aggressively, spend tokens wisely.

## Requirements

- Claude Code CLI (latest)
- Git (for worktree isolation)
- The project you're building (this framework is the coordination layer)

## Philosophy

This framework treats Claude agents like a high-performing engineering team:
- **Clear roles** — Every agent knows exactly what it owns
- **Contracts** — Handoffs are explicit, never implicit
- **Parallelism** — Work that can be done simultaneously IS done simultaneously
- **Learning** — Mistakes become safeguards automatically
- **Budget discipline** — Token limits are respected like time constraints

---

*Built for Claude Code. Orchestrated by PARL. Shipped by agents.*
