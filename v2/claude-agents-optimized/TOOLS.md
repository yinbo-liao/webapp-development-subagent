---
name: tools-reference
description: Quick reference for all tools available to PARL agents
type: system
budget: always-hot
---

# TOOLS.md — Tool Quick Reference

## File Operations
| Tool | Purpose | Agent Scope |
|------|---------|-------------|
| `Read` | Read file contents (supports .md, .py, .ts, .tsx, .yaml, .json, .ipynb, .pdf, images) | All agents |
| `Write` | Create or overwrite a file | All agents |
| `Edit` | Exact string replacement in existing files | All agents |
| `Glob` | File pattern matching (`**/*.tsx`, `src/**/*.py`) | All agents |
| `Grep` | Regex content search with ripgrep | All agents |
| `Bash` | Shell command execution | All agents |
| `PowerShell` | PowerShell command execution (Windows) | All agents |

## Agent Coordination
| Tool | Purpose | Agent Scope |
|------|---------|-------------|
| `Agent` | Spawn sub-agent with isolated context | project-planner, fastapi-architect |
| `TaskCreate` | Create structured task tracking | project-planner |
| `TaskUpdate` | Update task status/progress | All agents |
| `TaskList` | List all tracked tasks | All agents |

## Research & Reference
| Tool | Purpose | Agent Scope |
|------|---------|-------------|
| `WebSearch` | Web search with current information | All agents |
| `WebFetch` | Fetch and process URL content | All agents |

## Configuration
| Tool | Purpose | Agent Scope |
|------|---------|-------------|
| `Skill` | Invoke specialized skills (init, review, security-review, etc.) | project-planner |
| `CronCreate` | Schedule recurring tasks | web-deployer |
| `Monitor` | Stream events from long-running processes | web-deployer |

## Parallel Execution Notes
- **Independent file writes**: Agents writing to separate files can run in parallel.
- **Shared file writes**: Sequentialize through orchestrator to avoid merge conflicts.
- **Read-only agents**: security-auditor and test-automator can run concurrently with any agent.
- **Token budgets**: Monitor output size — large grep/glob results eat context. Use `head_limit`.
