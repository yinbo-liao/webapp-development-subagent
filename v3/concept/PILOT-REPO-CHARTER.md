# Pilot Repository Charter

**Decision:** ADR-002 · **Status:** draft for signature · **Duration:** 6 weeks from kick-off

## 1. Purpose

Give the agent platform a realistic but **non-production** target where failure is cheap, evidence is complete, and success is measurable. The pilot exists to prove the gates and the operating model, not to ship customer value.

## 2. Scope

| In scope | Out of scope |
|---|---|
| One repository mirroring the target stack (FastAPI, PostgreSQL, Vite/React) | Any production environment, data, or credential |
| Synthetic seed data only | Customer data, PII, or regulated data |
| Staging and ephemeral environments | Production deploy, DNS, or traffic |
| GATE_A–F on the seeded backlog | GATE_G expansion in production (simulated review only) |
| Security policy pack (selected P0 checks) | Full platform security certification |

## 3. Ownership (RACI)

| Role | Person/team | Accountable for |
|---|---|---|
| Platform owner | `<platform-lead>` | Repo, CI, environments, gatekeeper, evidence |
| Business owner (FDE) | `<fde-name>` | KPI contract, scope, adoption, go/no-go for expansion |
| Security reviewer | `<security-name>` | Policy pack, T3 second approval, red-team findings |
| Release manager | `<release-name>` | Default-branch merges, release tags, rollback drill |
| Pilot scribe | `<name>` | Weekly report, decision log, exception register |

## 4. Repository setup (before the first agent run)

- Protected branches: `main` (release only) and `dev` (integration); no direct pushes.
- Required checks: lint, type-check, unit, integration, SAST, dependency scan, e2e, coverage, policy-pack, `check-doc`.
- `CODEOWNERS` for `services/**`, `apps/**`, `db/migrations/**`, `docs/adr/**`.
- Signed commits; linear history on `main`; no force-push on protected branches.
- No repository secrets; deployment credentials are brokered per call and stored in the environment, never in the repo.
- `README` states the synthetic-data rule and the out-of-scope list.

## 5. Branch model

```text
feature/<task-id>  ──►  dev  ──►  main
   builder           auto-merge     release manager
   own worktree      after GATE_C/D  after GATE_E/F
```

- Builders may merge into `dev` autonomously **only** with GATE_C and GATE_D evidence attached.
- `main` merges require the release manager; `main` is the only deployable ref, and staging deploys come from it.
- Rollback is a revert commit on `main` plus the operator runbook; the drill runs once in week 2.

## 6. Seeded backlog (three tasks)

| ID | Task | Exercises |
|---|---|---|
| P-01 | Add a CSV export endpoint for closeout comments, with pagination and an audit event | Feature path A–F, KPI contract, security pack (BOLA, injection) |
| P-02 | Fix an off-by-one in list pagination and add a regression test | Bugfix path, evidence resolution, GATE_C scope |
| P-03 | Fix an object-level authorization gap on `GET /comments/{id}` | Security path, BOLA test, T3 gate set, two-person approval |

Each task ships with acceptance criteria, a test method per criterion, and a definition of done. Tasks may be re-run; success metrics are computed per run, not per task.

## 7. Success criteria (machine-verified)

| Criterion | Target | Source |
|---|---|---|
| Gate pass rate for first-attempt runs | ≥ 60% by week 6 | gatekeeper store |
| Unresolved out-of-scope diffs | 0 | GATE_C evidence |
| Evidence records resolving with matching hash | 100% | evidence registry |
| Unsafe effects (production writes, secret exposure, gate bypass) | 0 | audit chain |
| Audit chain verification | 100% of runs | independent verifier |
| Cost per completed task | ≤ `$<budget>` (set at kick-off) | cost attribution |
| Median cycle time (task start → `dev` merge) | ≤ 1 business day | run timestamps |
| Rework rate (runs requiring a second full loop) | ≤ 25% | gate history |
| KPI contract pre-registered before GATE_E | 100% of feature runs | contract store |
| Red-team corpora pass (injection, fabrication, bypass) | 0 false PASS | eval harness |

## 8. Exit criteria

The pilot exits when: all success criteria are met for two consecutive weeks, the pilot report is written, and the FDE plus platform owner sign a **go / no-go** for a real repository. A "no-go" is a valid outcome; it produces a remediation backlog and a re-run date.

## 9. Cadence

- Daily: gatekeeper dashboard review (5 min), blocked-run triage.
- Weekly: pilot report (runs, gates, cost, incidents, exceptions), FDE review.
- Week 2 and week 5: rollback drill and kill-switch drill.
- Week 6: exit review and decision.

## 10. Non-negotiables

1. No production data or credentials in the pilot, ever.
2. No gate may be disabled to make a task pass; exceptions go through the FDE register (ADR-005) and are time-boxed.
3. No agent writes its own evidence; the gatekeeper records what producers report.
4. Any incident produces an eval case before the fix is merged (test-first for evals).