# SubAgent Command Center — User Guide

## Document Owner
yinbo-liao · yinbo.leon@gmail.com · Version 1.0 · 2026-05-11

---

## Table of Contents

1. [Overview](#1-overview)
2. [Quick Start](#2-quick-start)
3. [Panel Reference](#3-panel-reference)
4. [Agent Quick Reference](#4-agent-quick-reference)
5. [Prompt Builder Usage](#5-prompt-builder-usage)
6. [Workflow Integration](#6-workflow-integration)
7. [Keyboard & Navigation](#7-keyboard--navigation)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Overview

The **SubAgent Command Center** (`subagent-command-center.html`) is an interactive dashboard for managing Claude Code SubAgents in a full-stack FastAPI + Vite/React development workflow. It provides:

- **7 tabbed panels** covering Dashboard, SubAgents, Workflow, Architecture, Prompt Builder, Security, and Deployment
- **Real-time agent status** indicators showing which agents are ready/busy
- **Interactive prompt generator** for delegating tasks to specialized AI agents
- **Visual architecture diagrams** of the full system stack
- **Security checklist** with interactive checkboxes
- **Deployment pipeline** visualization with rollback procedures

### Technology Stack Represented

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.110+ / Python 3.12+ / SQLAlchemy 2.0 async / Pydantic v2 |
| Frontend | React 18+ / TypeScript 5 / Vite 5 / Tailwind CSS 3 |
| Infrastructure | Docker / Kubernetes-ECS-Cloud Run / Terraform / GitHub Actions |
| Monitoring | Prometheus + Grafana + Loki + Jaeger |

---

## 2. Quick Start

### Open the Command Center

**Windows**:
```
start subagent-command-center.html
```

**macOS**:
```
open subagent-command-center.html
```

**Linux**:
```
xdg-open subagent-command-center.html
```

### Serve via Local HTTP (for sharing)
```bash
python -m http.server 8080
# Then visit: http://localhost:8080/subagent-command-center.html
```

### First-Time Setup

1. Ensure all 6 agent files are installed in `~/.claude/agents/your-project/`:
   ```
   ~/.claude/agents/your-project/
   ├── project-planner.md
   ├── fastapi-architect.md
   ├── vite-react-developer.md
   ├── security-auditor.md
   ├── test-automator.md
   └── web-deployer.md
   ```

2. Open the Command Center HTML in your browser.

3. Verify all 6 agent status dots are green (online) in the Dashboard.

4. Review the **Strategy Doc** panel for project objectives and phase alignment.

5. Use the **Prompt Builder** to delegate your first task.

---

## 3. Panel Reference

### Dashboard
The default landing page. Shows:
- **Agent Status Bar**: 6 agents with real-time status (online/busy/offline) and model assignments
- **Agent Cards**: Each agent's role, tech stack, model, and capabilities
- **Quick Actions**: "Select" button jumps to Prompt Builder; "Details" shows capability matrix

### Strategy Doc
Embedded content from `web-application-development-strategy.md`:
- Executive Summary with target metrics
- Full technology stack table (18 rows)
- Development phases (Phase 0-3, Weeks 1-8)
- Architecture diagram (CDN → LB → FastAPI + React → Data Layer)

### SubAgents
Detailed agent information:
- **Agent Hierarchy Diagram**: SVG showing orchestrator → specialist flow
- **Capabilities Matrix**: Primary skills, model, best-for, and collaboration mapping for all 6 agents

### Architecture
Visual system architecture with:
- **Layered diagram**: Client → Edge/CDN → Load Balancer → Application → Data
- Each layer shows specific technologies (CloudFront, ALB, FastAPI, PostgreSQL, Redis, Celery)

### Workflow
Feature development lifecycle visualization:
- **6-phase SVG diagram**: Planning → API Contract → Parallel Build (Backend + Frontend) → Testing → Security Audit (with remediation loop) → Deploy → Monitor
- Color-coded by agent responsibility

### Prompt Builder
Interactive tool for generating Claude Code delegation commands:
- **4 selectors**: Primary Agent, Task Type, Complexity, Priority
- **Live preview**: Generated prompt updates in real-time
- **Copy button**: One-click copy to clipboard
- **Quick Templates**: 6 pre-built prompts for common scenarios

### Security
Security gates and compliance tools:
- **5 Security Gates table**: SAST, Dependency Scan, Container Scan, Penetration Test, Code Review
- **10-item interactive checklist**: Check off each security requirement per feature
- Gates show trigger conditions and failure actions

### Deployment
Operations and infrastructure panel:
- **Pipeline visualization**: Local → CI → Staging → Production with descriptions
- **Rollback Procedures table**: 4 scenarios with methods and recovery times (< 30s to < 1hr)
- **Deployment patterns**: Blue-green and canary deploy descriptions

---

## 4. Agent Quick Reference

### Delegation Commands (from Strategy Doc Section 9.2)

**Planning**:
```
> "Use project-planner to create technical spec for [feature]"
> "Use project-planner to estimate effort and identify risks"
```

**Backend Development**:
```
> "Use fastapi-architect to design API for [resource]"
> "Use fastapi-architect to implement [feature] with full test coverage"
> "Use fastapi-architect to optimize [query] for N+1 problem"
```

**Frontend Development**:
```
> "Use vite-react-developer to build [component] with loading/error states"
> "Use vite-react-developer to integrate [API] with TanStack Query"
> "Use vite-react-developer to implement responsive [page]"
```

**Security**:
```
> "Use security-auditor to review [file/PR] for OWASP compliance"
> "Use security-auditor to perform penetration test on auth flow"
> "Use security-auditor to scan dependencies for vulnerabilities"
```

**Testing**:
```
> "Use test-automator to write unit tests for [module]"
> "Use test-automator to set up E2E tests for [user journey]"
> "Use test-automator to improve coverage in [area]"
```

**Deployment**:
```
> "Use web-deployer to containerize application with Docker"
> "Use web-deployer to set up GitHub Actions CI/CD pipeline"
> "Use web-deployer to deploy to [environment] with monitoring"
```

### Model Assignment

| Agent | Model | Why |
|-------|-------|-----|
| project-planner | Opus | Complex system thinking, risk analysis, cross-domain coordination |
| fastapi-architect | Opus | Database design, security patterns, async architecture |
| vite-react-developer | Sonnet | Standard implementation, fast iteration, strong coding |
| security-auditor | Opus | Threat modeling, vulnerability analysis, compliance mapping |
| test-automator | Sonnet | Pattern implementation, comprehensive coverage |
| web-deployer | Opus | Infrastructure design, multi-service orchestration, incident response |

---

## 5. Prompt Builder Usage

### Step-by-Step

1. Click the **Prompt Builder** tab (or click "Select" on any agent card).

2. Choose your parameters:
   - **Primary Agent**: Which specialist handles this task
   - **Task Type**: Implement, Review, Plan, Refactor, Debug, or Deploy
   - **Complexity**: Simple (< 2hr), Medium (2-8hr), Complex (1-3 day), Epic (1-2 week)
   - **Priority**: Low, Medium, High, Critical

3. The generated prompt appears in real-time below the selectors.

4. Click **Copy** to copy the prompt to clipboard.

5. Paste into Claude Code to delegate the task.

### Example Generated Prompts

**New Feature (Backend)**:
```
> Use fastapi-architect to implement user authentication with async SQLAlchemy 2.0,
Pydantic v2 schemas, proper error handling ({detail, code, context}), and structured
logging. Include OpenAPI documentation. [Complexity: medium]
```

**Security Review**:
```
> Use security-auditor to perform a comprehensive security review of auth module.
Check OWASP Top 10, injection flaws, auth bypasses. Use 5-gate process. [Complexity: medium]
```

**Deployment**:
```
> Use web-deployer to execute deployment of v1.2.0 to production with blue-green
strategy, health checks, and rollback readiness. [Complexity: complex]
```

---

## 6. Workflow Integration

### Daily Development Rhythm

**Morning Standup**:
1. Open Command Center → Dashboard
2. Check agent status indicators (all should be green)
3. Review yesterday's progress via `progress.txt`
4. Identify blockers

**Development Session**:
1. Use **Prompt Builder** to generate delegation commands
2. Delegate backend and frontend work in parallel
3. Use **Security** tab to verify checklist items
4. Use **Workflow** tab to track feature through phases

**Pre-Deployment**:
1. Open **Security** tab → verify all 10 checklist items
2. Open **Deployment** tab → review rollback procedures
3. Verify all 5 security gates pass in CI/CD
4. Execute deployment with monitoring active

### Feature Lifecycle

Each feature follows the 6-phase workflow visualized in the **Workflow** tab:
```
Phase 1: Planning (project-planner)
  → Phase 2: API Contract (fastapi-architect)
  → Phase 3: Parallel Build (backend + frontend simultaneously)
  → Phase 4: Testing (test-automator — all layers)
  → Phase 5: Security Audit (security-auditor — 5 gates)
  → Phase 6: Deploy & Monitor (web-deployer)
```

---

## 7. Keyboard & Navigation

### Tab Navigation
Click any tab in the top navigation bar to switch panels:
- **Dashboard** — Agent status and cards
- **Strategy Doc** — Embedded strategy document
- **SubAgents** — Capability matrix
- **Architecture** — System architecture layers
- **Workflow** — Feature development flow
- **Prompt Builder** — Interactive prompt generator
- **Security** — Gates and checklist
- **Deployment** — Pipeline and rollback

### Agent Selection Shortcuts
- Click **Select** on any agent card → jumps to Prompt Builder with that agent pre-selected
- Click **Details** on any agent card → jumps to SubAgents panel showing capability matrix

---

## 8. Troubleshooting

### Agent Status Shows "Offline"
- Verify agent `.md` file exists in `~/.claude/agents/your-project/`
- Check file permissions (should be readable)
- Restart Claude Code session

### Prompt Builder Not Updating
- Ensure JavaScript is enabled in your browser
- Check browser console for errors (F12 → Console)
- Refresh the page

### Architecture Diagram Not Rendering
- The SVG diagrams require a modern browser (Chrome, Firefox, Edge, Safari — all supported)
- If using IE11 or older, upgrade to a modern browser

### Security Checklist Not Persisting
- The interactive checkboxes are session-only (reset on page refresh)
- For permanent tracking, use the actual security review process via `security-auditor` agent

### File Associations
- `.html` files should open in your default browser
- If opening in a text editor, right-click → "Open With" → choose your browser
- Alternatively, use the local HTTP server method described in Quick Start

---

## Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| SubAgent Command Center | `subagent-command-center.html` | Interactive agent management dashboard |
| Development Strategy | `web-application-development-strategy.md` | Master strategy document (9 sections) |
| Agent Files (6) | `~/.claude/agents/your-project/` | SubAgent definitions for Claude Code |
| PARL Framework | `../v2/claude-agents-optimized/` | Full PARL agent mesh with vault, learnings, config |

---

*Guide maintained by yinbo-liao. Update as the SubAgent system evolves.*
