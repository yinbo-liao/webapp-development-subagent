# Concept v3.1 — Full-Stack Engineer Agent

**Status:** adopted concept · **Supersedes:** v3.0 (2026-11-04) · **Substrate:** DSH-native (ADR-001)
**Implementation today:** the Python system in `v3/agents`, `v3/ecc_tools`, `v3/workflows` (bridge, see [MIGRATION.md](./MIGRATION.md))

This folder is the authoritative concept for the enterprise full-stack engineer agent. It keeps v3.0's
four-layer model, roster, gates and contracts, and corrects the parts that could not be enforced: evidence
records instead of URIs, a scheduled business-outcome review instead of a parked run, guardrails instead of
per-action approvals, and one substrate instead of three.

---

## 1. What changed from v3.0

| v3.0 | v3.1 | Why |
|---|---|---|
| LangGraph + Keelgate + PostgreSQL as the stack | **DSH-native**; LangGraph only as an outer workflow | One policy plane; the enforcement substrate already exists |
| `evidence_uri` as proof | **EvidenceRecord** (hash, producer, command, exit code, environment, scope, freshness) | A URI is fabricable and not verifiable |
| GATE_G waits in-run for the KPI window | **Scheduled outcome review**; blocks expansion, never release | No weeks-long parked run; honest attribution |
| Thin KPI contract | Contract with guardrails, attribution, cost, source, decision rule, pre-registration | Resists noise and gaming |
| Model-written lessons injected freely | **GATE_M** + facts/procedures split | Memory is a prompt-injection channel |
| Builder actions need approval | **Guardrails**: autonomous inside boundaries, DENY outside | Approval fatigue; boundaries are the real control |
| Ad hoc model choice | **Explicit routing policy** with independence invariant | Cost, latency and comparability |
| FDE implied, authority undefined | **One accountable FDE**, bounded by non-waivable security/T3 rules | Governance clarity without a single point of failure |
| 10-week order: build agents first | **Gatekeeper + evidence + eval first**, roles second | Instrument before the machine |

The full assessment of v3.0 is in [ASSESSMENT.md](./ASSESSMENT.md); the detailed plan remains in
[REVIEW-AND-PLAN.md](./REVIEW-AND-PLAN.md). This document is the concise, current concept.

---

## 2. Four layers, one substrate

| Layer | Owns | Contract upward | DSH implementation |
|---|---|---|---|
| **Agent Loop** | one agent's turn | `SubagentResult` with evidence ids | DSH agent loop, configured per role (steps, stop conditions, no-progress, changed-hypothesis retry) |
| **Harness** | execution substrate | `HarnessState` (checkpoint, budget, tool versions) | `dsh-secure-mesh` + `dsh-gatekeeper` + sessions/presets/sandbox |
| **Loop Engineering** | workflow, gates, evaluation | `GateEvaluation` | supervisor workflow + gate engine + evidence registry |
| **FDE** | business integration | `BusinessImpactReport` | a human role, a KPI contract, an approval surface |

**Contract rule.** Each layer reports upward with a typed artifact, and each artifact is checked by a gate
or a test. A layer that cannot report evidence has not finished.

---

## 3. Composition

```text
Profile: fullstack-engineer
├── dsh-secure-mesh        # egress, tool deny/ask, untrusted fencing, audit, claim validation
├── dsh-gatekeeper         # effect policy, proposals, evidence registry, gates, budget, kill switch
└── role presets
    ├── supervisor          dispatch/gate tools only; no write tools
    ├── analyst             read/search + spec writer (docs/specs)
    ├── architect           read + ADR writer (docs/adr)
    ├── builder-{backend,frontend,data}  own worktree; no deploy tools
    ├── verifier-{blind,edge,acceptance,security,performance}  read/test/scan; no write tools
    └── operator            deploy staging; deploy prod gated; read observability
FDE is a human role, not a preset.
```

A role's capability is its composition: a tool it does not mount cannot be called, and a boundary it
crosses is denied by policy. Prompts explain; composition and policy enforce.

---

## 4. Roles

| Role | Responsibility | Output | Maps to existing v3 agent |
|---|---|---|---|
| supervisor | route phases, collect evidence, evaluate gates | `OrchestrationReport` | `orchestrator` |
| analyst | testable spec, flagged assumptions | `SpecArtifact` | *(new)* |
| architect | smallest safe architecture, ADRs, trust boundaries | `ArchitectureArtifact` | *(new)* |
| builder (backend) | FastAPI/data vertical slices | `BackendPatch` + evidence | `backend_agent` |
| builder (frontend) | React/UX slices | `FrontendPatch` + evidence | `frontend_agent` |
| builder (data) | schema, migrations (write, never apply) | migration + evidence | `database_agent` |
| verifier | independent verification, tests, scans | `VerificationReport` | `qa_agent` (+ ECC tools) |
| operator | deploy, observe, rollback | `OperationReport` | `devops_agent` |
| **FDE** (human) | business scope, KPI contract, exceptions, adoption | `BusinessImpactReport` | *(human, new)* |

The concept's earlier roster had six subagents; v3.1 keeps that shape and makes the human FDE explicit.
The repo's `security`, `performance`, `maintenance` entries in `config/agents.yaml` become **verifier modes
and ECC evidence producers**, not separate agents.

---

## 5. Enforcement map

| Guarantee | Seam | Test that proves it |
|---|---|---|
| A role cannot call a tool it was not granted | preset composition + secure-mesh deny | bypass corpus → 0 successes |
| A builder cannot write outside its worktree | per-role cwd + fs sandbox + path allowlist | out-of-scope diff denied and audited |
| No production effect without an approved proposal | gatekeeper pre-execute + commit token | forged/stale/expired/replayed token denied |
| Evidence cannot be fabricated | gate reads the registry, not prose | fabricated record → BLOCKED |
| Verifier cannot modify code | no write tools + read-only session | write attempt → tool absent |
| Approval cannot be widened | args hash + intent hash + TTL + single use | re-plan → `stale_args` |
| Budget cannot be exceeded silently | ledger + denial + checkpoint | 120% budget → `BUDGET_EXHAUSTED`, escalate |
| Kill switch stops effects without a deploy | runtime flag in pre-execute/guard | flip → effects denied, reads allowed |
| Audit cannot be truncated silently | hash chain + off-box ship | edit a line → verification fails |
| Context does not leak between phases | spawn child + slice + redaction | planted secret outside slice → contamination flag |
| Verifier is independent | routing policy invariant | same-provider config → config test fails |
| Gates cannot be self-graded | gate owner ≠ artifact producer | self-evaluation denied |

---

## 6. Gates

| Gate | When | Owner | Blocks | Statuses |
|---|---|---|---|---|
| A | after spec | analyst | run | PASS/FAIL/BLOCKED/TIMED_OUT |
| B | after design | architect + design verifier | run | PASS/FAIL/BLOCKED |
| C | after build | supervisor | run | PASS/FAIL/BLOCKED |
| D | after verification | verifier | run | PASS/FAIL/BLOCKED/TIMED_OUT |
| E | per production effect | human approver | effect | PASS/FAIL/BLOCKED |
| F | per deploy | operator | deploy completion | PASS/FAIL/ROLLBACK |
| **G** | scheduled after release | **FDE + product owner** | **rollout expansion only** | PASS/ITERATE/ROLLBACK/**INCONCLUSIVE** |
| R | routing releases | engineering lead | routing release | PASS/FAIL |
| M | memory writes | supervisor | write | PASS/BLOCKED |

Risk tiers T0–T3 select the gate set; the tier comes from the effect matrix, never from the model.
GATE_F ends the release. GATE_G never retroactively blocks a verified release; it decides whether the
change expands.

---

## 7. Evidence

```ts
interface EvidenceRecord {
  id: string; runId: string; dispatchId: string; role: string
  kind: EvidenceKind
  command: string; exitCode: number; startedAt: string; endedAt: string
  artifact: { path: string; sha256: string; bytes: number; mediaType: string }
  environment: { commit: string; imageDigest?: string; toolVersions: Record<string, string> }
  scope: string[]; producer: 'ci' | 'tool' | 'human'; signature?: string
}
```

**Kinds.** `spec`, `adr`, `diff-manifest`, `build`, `unit-tests`, `integration-tests`, `e2e-trace`,
`coverage`, `sast`, `dependency-scan`, `container-scan`, `sbom`, `static-analysis`, `performance`,
`maintainability`, `secret-scan`, `migration-check`, `restore-drill`, `smoke-tests`, `observability-check`,
`design-review`, `blind-review`, `approval-record`, `human-ack`, `routing-eval-run`, `kpi-snapshot`.

**Verification rules.** record exists; hash matches bytes; producer trusted for the kind; commit matches
the run; scope covers the requirement; fresh within the window; no open HIGH/CRITICAL for security kinds.
The ECC tools in this repository are natural producers for `sast`, `static-analysis`, `performance`,
`maintainability`, and `secret-scan` — see [MIGRATION.md](./MIGRATION.md).

---

## 8. Proposals, approvals, commit tokens

```text
propose_action(tool, args, intent, blastRadius, rollbackPlan, verificationPlan)
   → pending → approve(checklist) → approved → commit(token) → consumed → verified
```

- Approval binds `(tool, args hash, intent hash)`, with TTL, checklist acknowledgement and single use.
- The commit token is an HMAC over the binding; the effect tool presents it, the gate recomputes the
  hash from the actual arguments and consumes the proposal once.
- A re-plan, a retry with different bytes, or a redirect to another object cannot reuse the approval.
- In-turn approvals use `ctx.approval`; cross-turn approvals use the gatekeeper record. Chat is not an
  approval.
- The FDE is the accountable business approver; T3 changes also require security/platform as a second
  approver (ADR-005).

---

## 9. Builder guardrails (ADR-003)

| Boundary | Enforced by | Evidence |
|---|---|---|
| Repository scope | worktree + path allowlist | diff manifest |
| Branch scope | feature branches; integration merge after C/D | merge record |
| Dependencies | allowlist + lockfile + license + registry proxy | SBOM + dependency scan |
| Secrets | no repo secrets; no prod credentials in builder preset | secret scan |
| Network | registry proxy only; docs via `secure_fetch` allowlist | egress audit |
| Security | stack policy pack at GATE_D | scan + test evidence |
| Budget | per-dispatch and per-run ceilings | ledger |

Autonomy relaxes approval, never the gate. A builder may write a migration; applying it outside the
ephemeral environment remains operator work behind GATE_E.

---

## 10. Model routing (ADR-004)

Role and risk tier select a route class; the policy file (`policy/model-routing.yaml`) names the primary
and ordered fallback. No tool argument may select a provider or model. The resolved route is recorded in
evidence. The verifier must never share a provider with the builder; if the only available fallback would
violate that, the run blocks with `PROVIDER_INDEPENDENCE_UNAVAILABLE`.

---

## 11. Business loop (ADR-006, ADR-007)

- The KPI contract is pre-registered and dual-signed before GATE_E; it is immutable afterwards.
- It names one authoritative source (`policy/kpi-sources.yaml`), guardrails, attribution method, cost cap
  and decision rule. Schema and validator: [`contracts/`](./contracts/).
- GATE_G runs on a schedule (2–4 weeks), returns PASS / ITERATE / ROLLBACK / INCONCLUSIVE, and only
  blocks rollout expansion. An iteration opens a new run with a new contract.

---

## 12. FDE authority (ADR-005)

One accountable FDE for business scope, KPI, exceptions and adoption. Non-waivable: security findings,
T3 two-person approval, audit/evidence integrity, the synthetic-data rule. Exceptions are time-boxed
(≤ 14 days), logged, and reviewed. Details: [FDE-AUTHORITY.md](./FDE-AUTHORITY.md).

---

## 13. Pilot (ADR-002)

A dedicated pilot repository with synthetic data, no production access, branch protection, three seeded
tasks and machine-checked success criteria. Details: [PILOT-REPO-CHARTER.md](./PILOT-REPO-CHARTER.md).
The platform repository (this one) is not the pilot target.

---

## 14. Delivery outline

| Phase | Weeks | Outcome |
|---|---|---|
| P0 | 1 | Decisions, contracts, effect matrix, gate catalogue, document repair |
| P1 | 2 | Gatekeeper core: policy, proposals, commit tokens, budget, kill switch |
| P2 | 2 | Eval harness, routing baseline, evidence adapters (ECC among them) |
| P3 | 2 | Role presets and isolation |
| P4 | 2 | End-to-end GATE_A–F on the pilot |
| P5 | 2 | FDE handoff, KPI contract, first scheduled outcome review |
| P6 | 2 | Red-team corpora, SLOs, production readiness |

The full work breakdown is in [REVIEW-AND-PLAN.md](./REVIEW-AND-PLAN.md) §6.

---

## 15. Document integrity

This concept is checked by [`tools/check-doc.mjs`](./tools/check-doc.mjs) in CI: balanced fences, real
headings, no model meta-commentary, and a test section for any document that claims to be
implementation-ready. The v3.0 document failed this check (one unclosed fence, 39 plain-text sections);
this package passes.

---

## 16. Limits

- The concept is substrate-ready, not yet a running DSH composition; the P1 core exists as a reference
  implementation in [`gatekeeper/`](./gatekeeper/README.md).
- Evidence records are specified; the registry and gate engine are P1 work.
- The Python v3 system remains the current implementation and needs the bridge described in
  [MIGRATION.md](./MIGRATION.md).
- Memory gating, budget ledger and routing evaluation are specified but not implemented.