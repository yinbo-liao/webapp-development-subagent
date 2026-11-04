# Migration — Python v3 implementation → concept v3.1

**Status:** proposed bridge (ADR-008) · **Target:** DSH-native concept (ADR-001) · **Current:** Python v3 agents + ECC

The concept is the target architecture. The Python system in `v3/agents`, `v3/ecc_tools`, `v3/workflows` is
the running implementation and stays runnable during the migration. This document says what changes, in
what order, and how the two stay honest about each other.

---

## 1. Where the repository is today

| Area | Current implementation |
|---|---|
| Orchestration | `agents/orchestrator/main.py`: 7-phase workflow, in-process quality gate, thread pool |
| Agents | `frontend`, `backend`, `database`, `qa`, `devops` (plus config entries for security/performance/maintenance) |
| Generation | Jinja2 templates + optional Anthropic loop with ECC feedback (max 3 iterations) |
| Quality | `ecc_tools/core/engine.py` singleton: SAST, stability, performance, maintainability; `quality_gate_check()` |
| Config | `config/agents.yaml` (agents + quality thresholds), `config/ecc.yaml` (rules) |
| Workflow | `workflows/new-project.yaml` (YAML DAG), `workflows/base_workflow.py` |
| Protocol | `shared/protocols/agent_protocol.py` (Pydantic messages) |

What it already has that the concept needs: a deterministic scanner suite, quality thresholds, a phase
graph, typed messages, and a working code generator. What it lacks: evidence records, hash-bound
proposals, a monotonic policy layer, guardrails as enforcement, and a business-outcome loop.

---

## 2. Target vs bridge

| | Target (ADR-001) | Bridge (ADR-008, proposed) |
|---|---|---|
| Orchestration | DSH supervisor + role presets | Python orchestrator with gatekeeper calls |
| Enforcement | `dsh-secure-mesh` + `dsh-gatekeeper` | Python gatekeeper core, same policy/semantics |
| Evidence | DSH gatekeeper registry | JSONL/SQLite registry written by the Python adapter |
| Roles | DSH presets | `agents.yaml` v2 roles + capability restrictions |
| Approval | `ctx.approval` / gatekeeper record | Gatekeeper CLI/API record; no chat approvals |
| Audit | secure-mesh hash chain | Append-only JSONL hash chain (same record shape) |

The bridge is not a second policy plane: it is the **same contracts implemented in Python** until the DSH
composition exists. The TypeScript core in [`gatekeeper/`](./gatekeeper/README.md) is the reference
implementation and the conformance oracle; the Python port must produce identical decisions for the same
fixtures.

---

## 3. Agent → role mapping

| Current agent | Concept role | Change |
|---|---|---|
| `orchestrator` | supervisor | replace in-process gate evaluation with gatekeeper calls; no write tools |
| `backend_agent` | builder (backend) | keep generation; add guardrailed scope, evidence reporting, commit-token requirement for effects |
| `frontend_agent` | builder (frontend) | same; bundle inspection becomes evidence |
| `database_agent` | builder (data) | may write migrations; may not apply them outside ephemeral env; expand/contract guardrails |
| `qa_agent` | verifier | keep tests; add blind/edge/acceptance modes; no write to production code |
| `devops_agent` | operator | deploy staging auto; production deploy requires proposal + checklist + GATE_E |
| `security` (config entry) | verifier mode + producer | becomes `sast` evidence producer; not a separate agent |
| `performance` (config entry) | verifier mode + producer | becomes `performance` evidence producer |
| `maintenance` (config entry) | verifier mode + producer | becomes `maintainability` evidence producer |
| *(new)* | analyst | spec artifact, assumptions, acceptance criteria |
| *(new)* | architect | ADRs, trust boundaries, component mapping |
| *(human)* | FDE | KPI contract, exceptions, adoption; not an agent |

---

## 4. Phase → gate mapping

| `new-project.yaml` phase | Gate | Required evidence |
|---|---|---|
| `requirements_analysis` | GATE_A | spec artifact; every criterion has a test method; assumptions flagged |
| `architecture_design` | GATE_B | ADR artifact; design review record; trust-boundary control ratio |
| `implementation` | GATE_C | build; unit tests; diff manifest within scope |
| `ecc_scan` | — (producer) | SAST, static-analysis, performance, maintainability records |
| `quality_gate` | GATE_D | integration tests, e2e trace, coverage, SAST, dependency scan, policy pack |
| `testing` | GATE_D | test evidence with scope coverage |
| `deployment` | GATE_F (+ GATE_E for production) | smoke, observability, approval record, rollback plan |
| *(new, scheduled)* | GATE_G | KPI snapshot, guardrail snapshot, cost attribution |

The existing in-process `quality_gate_check()` becomes a **consumer** of evidence records: it must not
compute PASS from scanner objects it holds in memory, because that is a self-graded gate. The gate reads
the registry.

---

## 5. ECC tools → evidence producers

This is the highest-leverage reuse in the repository: the scanners already produce the data the gates need.

| Current | Evidence kind | Record content |
|---|---|---|
| `ecc_tools/security/sast_engine.py` | `sast` | SARIF/JSON artifact hash, finding counts by severity, ruleset version |
| `security/rules/secret_patterns.yaml` | `secret-scan` | findings, redacted sample, ruleset version |
| `ecc_tools/stability/static_analyzer.py` | `static-analysis` | complexity distribution, error-handling findings, thresholds used |
| `ecc_tools/performance/profiler.py` | `performance` | benchmark command, p95/p99, throughput, environment |
| `ecc_tools/maintainability/code_metrics.py` | `maintainability` | MI, Halstead volume, type coverage |
| `ecc_tools/reporting/report_generator.py` | — | produces the artifact file; its hash goes into the record |
| `ecc_tools/core/engine.py` | — | orchestrates the above; must emit one record per analyzer run |

Every record carries `command`, `exitCode`, `startedAt/endedAt`, `environment.commit`, `toolVersions`, and
`scope` (changed files or full project). A scanner crash is a failed record, not a missing one — fail closed.

---

## 6. Config mapping

| Current config | Concept artifact |
|---|---|
| `agents.yaml: agents.*.capabilities` | role → tools/effects in `effect-matrix.yaml` |
| `agents.yaml: agents.*.ecc_validation/auto_fix` | builder guardrails (ECC evidence mandatory; auto-fix bounded) |
| `agents.yaml: quality_gates.*` | gate metrics and thresholds in `gate-catalog.yaml` (GATE_D) |
| `agents.yaml: communication.*` | proposal/evidence event transport; Redis optional, not authoritative |
| `ecc.yaml` thresholds | policy-pack checks (stack policy pack) |
| `workflows/new-project.yaml` | supervisor workflow phases and gate edges |
| `shared/protocols/agent_protocol.py` | `TaskEnvelope`, `ActionProposal`, `EvidenceRecord` DTOs |

Rule: thresholds live in one place. While both configs exist, the gate catalogue wins and `agents.yaml`
values are generated from it (or validated against it), never the reverse.

---

## 7. Code change points

| File | Change |
|---|---|
| `agents/orchestrator/main.py` | replace `quality_gate_check()` call with `gatekeeper.evaluate_gate('GATE_D', run_id)`; add proposal creation before deploy; no direct gate PASS |
| `agents/base_agent.py` | inject `GatekeeperClient`; report evidence after every generation/validation; enforce guardrail results before write |
| `agents/registry.py` | load role specs (composed tools) instead of capability lists only |
| `agents/database_agent/agent.py` | write migrations under `expand_contract_only`; never call apply outside ephemeral |
| `agents/devops_agent/agent.py` | staging auto; production requires commit token; rollback runbook |
| `ecc_tools/core/engine.py` | add `emit_evidence(run_id, commit)` after each analyzer; include tool versions |
| `shared/protocols/agent_protocol.py` | add Pydantic models mirroring concept schemas (`schema_version`) |
| `main.py` | add `ewds gate evaluate|propose|commit|evidence` subcommands for the bridge |
| `workflows/new-project.yaml` | add gate edges and the scheduled outcome review reference |
| *(new)* `gatekeeper/` (Python) | policy, proposals, tokens, evidence registry, gate engine |

Nothing in `agents/*/templates/` changes in the first migration. Generated applications are unaffected.

---

## 8. Migration phases

| Phase | Weeks | Deliverable | Exit criteria |
|---|---|---|---|
| **M0** | 1 | Concept merged; DTOs; effect matrix + gate catalogue loaded by Python; doc CI | `check-doc` and policy parse in CI; no behavior change |
| **M1** | 2 | Python gatekeeper core (policy, proposals, commit tokens) | Conformance fixtures from the TS core pass 100% |
| **M2** | 2 | ECC → evidence adapter; GATE_D over records | A run produces 4 evidence records; a planted HIGH finding blocks |
| **M3** | 2 | Role specs and guardrails in agents; worktree isolation | Out-of-scope write denied; verifier has no write path |
| **M4** | 2 | FDE handoff, KPI contract, GATE_G, pilot repo | First outcome review executed; pilot success criteria measured |

Standing rule: no phase removes the old path before its replacement has a negative test (attempt → deny).

---

## 9. Conformance between the two implementations

- Fixtures: effect decisions (role × effect × guardrails), proposal lifecycle, token verification, gate
  predicates. Stored as JSON under `concept/gatekeeper/fixtures/` (P1 addition).
- The Python port replays fixtures and must match the TypeScript reference exactly, including error codes.
- Any divergence is a bug in the port, not a new decision; a needed semantic change updates the concept
  first, then both implementations.

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| Two implementations drift | Shared fixtures; CI conformance job; one decision record per semantic change |
| In-process gate can be bypassed by orchestrator code | Gate reads only the evidence registry; the orchestrator cannot write records |
| ECC false positives block runs | Stack policy pack with documented suppressions; a suppression is evidence, not silence |
| Python/TS runtime split | Bridge is Python-first; TS core is reference only until DSH composition exists |
| Migration stalls halfway | M-phases are independently useful; M2 delivers value even if M3–M4 slip |
| Secrets in evidence artifacts | Redaction at capture; secret scan of artifacts; evidence paths outside the repo |

---

## 11. What does not change

Templates in `agents/*/templates/`, the generated application stack, the CLI flags, the demo output, and
the ECC rule files. The migration changes **who decides**, not how code is rendered.