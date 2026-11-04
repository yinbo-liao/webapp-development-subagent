# Full-Stack Engineer Agent — Integration Review, Target Design and Delivery Plan

**Status:** proposal for decision · **Date:** 2026-11-04
**Inputs reviewed**

| Input | Size | Role in this review |
|---|---|---|
| `Full_Stack_Engineer_Agent_Platform.md` (v3.0) | 4 KB | Vision, five domains, 20-role catalogue |
| `Full stack engineer -agent concept.txt` (v2.0) | 32 KB | The real design: supervisor + 6 subagents, gates, proposals |
| `Agent design with security v2.md` | 45 KB | Platform security standard for the apps the agent builds (FastAPI/Postgres/React/Entra) |
| `dsh-secure-mesh` v2.0.0 (this workspace) | 3.5 K LOC + 31 tests | Enforcement substrate: egress, tool denial, approvals, fencing, audit, claim validation |
| `reference/agentkit` (this workspace) | ~20 modules | Executable prototype of proposals, policy, budgets, trace, evals — the concept's Keelgate in Python |

**Deliverables in this folder:** this document, `effect-matrix.yaml` (machine-readable autonomy policy), `gate-catalog.yaml` (gates as deterministic predicates over evidence). The v3.0 four-layer revision, its risks, and the v3.1 reconciliation are in [`V3-REVIEW-AND-PROPOSAL.md`](./V3-REVIEW-AND-PROPOSAL.md); GATE_G and the KPI contract live in `gate-catalog.yaml` v1.1 and `contracts/`.

---

## 1. Executive verdict

**The concept is worth building, but not in the shape it is written.**

What the attachments contain is a **governance architecture and a role catalogue**. What they do not contain is (a) a substrate decision, (b) an enforcement map from each guarantee to a runtime seam and a test, (c) an evidence contract a machine can verify, and (d) a durable approval model that survives a run ending. Those four omissions are exactly the failure mode the secure-mesh audit found in v1: *a control that is not on a harness seam is a prompt, and a prompt is not a control.*

**Recommendation, in six decisions:**

1. **One control plane: DSH.** Build the role system as a DSH profile composed of plugins and presets, with `dsh-secure-mesh` as the enforcement substrate. If organisational policy mandates LangGraph for long-running durability, use it only as an *outer* workflow that calls DSH agents as workers — never as a second policy plane. Two gate implementations guarantee that one of them is bypassed.
2. **Six roles, not twenty.** Supervisor, analyst, architect, builder (backend/frontend/data profiles), verifier (blind/edge/acceptance/security/performance modes), operator. Knowledge and memory become services with a write gate, not agents. Self-healing becomes an operator runbook mode with a tighter autonomy ceiling.
3. **Capability = composition, not a token.** Each role is a DSH agent preset that mounts only the tools it may use, its own model route, its own worktree, and its own `dsh-secure-mesh` config. A capability a role does not have is *absent from its context*, not "discouraged by its prompt". Capability tokens remain as audit records, not permissions.
4. **Gates are code over recorded evidence.** A gate is a deterministic predicate over content-addressed evidence records produced by trusted producers. A PASS requires resolution, hash match, freshness, scope coverage, and exit status — not prose. This is the only way "evidence over claims" becomes real.
5. **Proposals are bound to bytes.** Approval binds `(tool, canonical args hash, intent hash)`, with TTL, single use, and a checklist acknowledgement. `ctx.approval` covers the in-turn case; a persistent gatekeeper record covers the "approved two days later" case, because DSH approval requires an open turn.
6. **Build the evaluator before the builders.** The system that writes and deploys code must itself be measured: task success, unsafe effects, evidence fabrication attempts, gate-bypass attempts, cost per success, rework rate. Without that harness, "the agent works" is a claim, not a measurement.

**Effort reality:** 10 weeks to a safe pilot on one repository; about 6 months to guarded, pre-approved self-healing. The 6-week sequence in the concept covers roughly the first three of those phases and none of the evaluation programme.

---

## 2. What each attachment actually contributes

### 2.1 Platform v3 (4 KB) — the org chart

A vision statement: five domains (Product, Engineering, Verification, Governance, Knowledge), 20+ named roles, a delivery workflow, a technology list, success criteria. Its durable value is the principle set — separation of duties, evidence over claims, human authority, bounded autonomy — and the insight that governance is a domain rather than a step. It contains no contracts, no substrate, and no enforcement mechanism, so it cannot be implemented as written.

### 2.2 Concept v2 (32 KB) — the design

This is the strongest document and the one to build from. Six subagents with typed inputs/outputs and hard prohibitions, a supervisor that routes but does not produce, a phase state machine with gate edges, bounded revision counters, propose-then-commit with blast radius and rollback, capability grants, context slices, parallel blind/edge/acceptance verification, evidence URIs, failure-mode guards, a Definition of Done, and a supervisor prompt. It is roughly 70% of a correct design; the missing 30% is the part that makes it enforceable (see §3).

### 2.3 Security v2 (45 KB) — the standard the agent must satisfy

A platform security standard for a specific product (TTAS/P-82: FastAPI, PostgreSQL + pgvector, React/Vite, Entra ID, Graph, Foundry). It is well above average: parameterized SQL over blocklists, object-level authorization with 404 semantics, `FORCE ROW LEVEL SECURITY` with transaction-local context, SafeMarkdown, upload hardening, request-path vs work-path split, outbox, expand/contract migrations, restore drills, SLOs, append-only audit, and — most valuable — **§14, a test per control**. Its main limitation for this programme is that it is stack-specific: for the agent platform it must be parameterised as a *policy pack*, not copied as universal truth.

### 2.4 Reusable assets already in this workspace

- `dsh-secure-mesh` v2.0.0: real Cordis plugin, 31 passing tests, SSRF-hardened fetch, tool deny/ask, approval tool, untrusted-content fencing, hash-chained audit, claim validators. This is the enforcement substrate; it does not need to be rebuilt.
- `reference/agentkit`: proposals bound to args and intent hashes with TTL and single use (`proposals.py`), effect-class autonomy with a kill switch (`policy.py`), six-budget ledger (`budget.py`), causal trace (`trace.py`), eval harness and scorecard. The gatekeeper plugin should **port these semantics**, with the Python module kept as the executable oracle for property tests (same inputs → same decisions).

---

## 3. Evaluation

### 3.1 What to keep (and why)

1. **Separation of duties** — builder ≠ verifier, verify ≠ approve, approve ≠ deploy. This is the cheapest structural control against self-grading and one of the few that survives model improvements.
2. **Deterministic gates** — "the LLM proposes; deterministic code decides" is the correct inversion. Keep it literally: gate results are computed, never generated.
3. **Proposal before effect** — persisting intent, blast radius, rollback, and idempotency *before* a side effect is the right shape, and the workspace prototype already implements the hash binding.
4. **Bounded loops with escalation** — revision counters plus "two loops without metric improvement → escalate" prevents the expensive failure mode of agents optimising against a gate.
5. **Parallel independent verification** — blind / edge / acceptance is the generator–verifier pattern done properly: the blind reviewer never sees the spec that would bias it.
6. **Typed task envelopes** — passing a filtered context slice rather than a shared transcript is the main defence against context contamination.
7. **One enforcement point per guarantee + a test that fails if removed** (security v2 §1) — adopt this as the platform's own invariant, not just the product's.
8. **Failure-mode table** (concept v2 §6) — scope creep, fabricated evidence, rubber-stamping, infinite loops, contamination, privilege escalation, collusion. These are the right threats; each needs a mechanism and a test in §4.

### 3.2 Blocking gaps

**G1 — Three substrates, no decision.** Platform v3 lists LangGraph/CrewAI/AutoGen/Semantic Kernel plus Temporal, Postgres, pgvector, Redis, Neo4j. Concept v2 assumes LangGraph + PostgreSQL checkpoints + OPA/Rego. The security guide assumes FastAPI + Postgres + Entra. DSH already provides agents, sessions, presets, subagents, workflow, approvals, sandbox, and a tool pipeline. Composing all of them yields several policy planes, several state stores, and several places where "the gate" can be skipped. **Decision required (ADR-0001).**

**G2 — Enforcement is described, never located.** Concept v2 says "every tool call traverses Keelgate", but never names the hook that denies a call. In DSH the seams are `tools/pre-execute` (deny/ask), `ctx.tools.guard` (monotonic deny), `ctx.approval` (human decision), the sandbox (process/fs), and preset composition (tool existence). In LangGraph it is a tool wrapper. Pick one runtime and write down guarantee → seam → test for every control (§4.4). Without that table, the design repeats the v1 secure-mesh failure.

**G3 — Capability tokens are advisory unless the tool is absent.** A short-lived token in a prompt does not prevent a call. DSH can make the capability structural: the child's preset composition decides which tools exist, the fs sandbox decides which paths are writable, and the model route decides which provider is billed. Keep tokens as auditable records; never treat them as the permission itself.

**G4 — "Context slice is the only context" is not true by construction.** DSH children inherit origin metadata and permission roots; preset composition and prompt construction minimise context but do not prove isolation. Treat the slice as *context minimisation*, add output-side contamination checks, and state the residual risk instead of claiming a boundary.

**G5 — "Subagents cannot append to the audit chain" needs architecture, not a sentence.** Plugins share a process; any plugin with the path can append. Enforce with an append-only file plus OS ACL, a single writer service, hash-chain verification by an independent checker, and off-box shipping. "The supervisor is the only writer" is a convention unless the filesystem says so.

**G6 — Durable approval is mis-modelled.** DSH `ctx.approval.request()` requires an open turn (verified: it throws between turns, because the `approval/asked` + `approval/decided` pair must be turn-enclosed). Concept v2's "approval arriving two days later finds the workflow intact" therefore needs a **gatekeeper proposal store** and a human decision endpoint/CLI; the commit path re-validates hash, TTL, checklist, and single use. `ctx.approval` remains the in-turn UX, not the durable record.

**G7 — Evidence URIs are underspecified.** A URL can be fabricated by a model, and "resolves" is not enough. Evidence must be a content-addressed record with producer identity, command, exit code, environment fingerprint, scope, and timestamp; the gate reads the registry, never the model's prose. §4.6 defines the record.

**G8 — The budget manager is assumed, not designed.** DSH exposes replay-based token measurement (`ctx.tokenMeter`), not per-call cost enforcement. A per-run/dispatch ledger must be built: meter at step boundaries, deny effectful calls when exhausted, checkpoint, and escalate. Define the terminal state; do not let exhaustion throw an opaque error.

**G9 — Independence is asserted, not engineered.** Builder and verifier on the same model with shared history fail together. Require a different model route for the verifier, no builder transcript (blind mode), a separate worktree, and an eval that measures verifier–builder agreement on planted defects.

**G10 — Self-healing has no autonomy ceiling.** "Auto Remediation Agent" in platform v3 is the highest-blast-radius role in the system and has no effect matrix, no runbook allowlist, no kill switch. Defer it; when built, allow only pre-approved runbooks with a bounded blast radius, no schema/data deletion, and a human-owned kill switch.

**G11 — Memory as an agent is a poisoning vector.** "Memory Agent" writing its own store can self-approve and poison future runs. Make memory a service with a write gate: only gate-verified artifacts, provenance required, conflict detection, TTL, ACL-filtered retrieval, and no automatic ingestion of model output.

**G12 — No definition of done for the agent system itself.** The DoD in concept v2 §9 covers a *run*. The platform needs release gates: eval suite, injection corpus, gate-bypass corpus, cost per success, and a red-team review — or the agent system will ship unmeasured.

**G13 — The roster violates the concept's own span-of-control rule.** Platform v3 lists 20+ roles; concept v2 correctly caps at 5 active subagents. Twenty roles also multiply evaluation surface. Consolidate to six roles with capability profiles.

**G14 — The 6-week plan is not credible.** It sequences agents before the evidence/gate substrate, and omits evaluation, memory gating, and security-pack automation. A 10-week MVP is realistic; self-healing is a later, separately gated programme.

### 3.3 Contradiction matrix

| Dimension | Platform v3 | Concept v2 | Security v2 | DSH reality |
|---|---|---|---|---|
| Orchestrator | "LangGraph preferred" list | LangGraph `StateGraph` + PG checkpoints | FastAPI worker | Cordis agent + subagents + workflow |
| Policy plane | "Keelgate" (domain) | Keelgate + OPA/Rego | FastAPI middleware + DB roles | `tools/pre-execute`, `guard`, `approval`, sandbox, presets |
| Roles | 20+ agents | 6 subagents | — | presets (child plugin compositions) |
| State | PG + pgvector + Redis + Neo4j | PG proposals/audit/checkpoints | PG RLS/outbox | sessions + JSONL; SQLite/PG optional |
| Approval | "Approval Service" | Persisted proposal + `interrupt()` | Approval endpoint + idempotency | in-turn `ctx.approval` + gatekeeper record |
| Evidence | "verifiable artifacts" | `evidence_uri` + DoD | A test per control (§14) | tool results + registry + audit chain |
| Budget | "Budget Manager" | Keelgate budgeted loops | per-user cost budgets | token meter + jobs/goal limits; ledger must be built |
| Autonomy | "human authority" | effect classes + 6 gates | kill switch, RLS | deny/ask/guard + sandbox + approvals |
| Delivery | self-healing | operator + canary | blue/green + rollback | external CI/CD, gate evidence |

### 3.4 Maturity scorecard (0 = absent, 4 = verified in production)

| Dimension | Now (docs) | Target | The gap in one line |
|---|---|---|---|
| Substrate decision | 1 | 4 | Three stacks, no ADR |
| Role model | 2 | 4 | 20 roles, no contracts |
| Enforcement | 1 | 4 | No seam → no test → no control |
| Evidence | 1 | 4 | URIs, not records |
| Approvals | 2 | 4 | In-turn only; no durable binding |
| Budgets | 1 | 3 | Assumed, not metered |
| Observability | 1 | 3 | No trace/audit join on DSH events |
| Memory | 1 | 3 | Agent-owned, no write gate |
| Evaluation | 0 | 4 | No harness for the agent itself |
| Security baseline | 3 | 4 | Excellent, but manual and stack-specific |

### 3.5 Verdict per document

- **Platform v3:** keep the principles and the domain model; discard the roster as an implementation target. It is a charter, not a design.
- **Concept v2:** adopt as the baseline. Correct four things: locate enforcement on seams, make evidence records, make approvals durable, right-size the roster. Add budgets and evaluation as first-class.
- **Security v2:** adopt as a **policy pack** with automated gates for the FastAPI/React/Azure stack. Its §14 is the highest-value content in all three attachments; it should become executable checks, not a PDF.
- **Secure mesh + agentkit:** the substrate already exists. Build the missing orchestration pieces (gatekeeper, evidence registry, role presets, budget ledger) on top of it rather than beside it.

---

## 4. Target architecture

### 4.1 Principles

1. **One control plane, one record, one gate implementation.** DSH owns agent lifecycle, sessions, tools, approvals, and presets. The gatekeeper plugin owns proposals, evidence, and gates. No second policy engine.
2. **Capability = composition.** A role can use exactly the tools its preset mounts. Prompts explain; composition constrains.
3. **Evidence is data.** A PASS is computed from content-addressed records, never from model prose.
4. **Approvals bind bytes.** `(tool, args hash, intent hash)` + TTL + single use + checklist.
5. **Default deny for effects; fail closed for writes; fail open with a marker for reads.**
6. **Bounded loops and budgets are hard stops**, with a typed terminal state and a checkpoint, not an exception.
7. **Prompt/policy parity.** Every rule in a role prompt has a hook that enforces it and a test that fails if the rule is removed. A rule with no hook is deleted from the prompt.

### 4.2 Composition

```text
Profile: fullstack-engineer
├── plugins
│   ├── dsh-secure-mesh           # egress, deny/ask, fence, audit, claim validation
│   ├── dsh-gatekeeper            # proposals, evidence registry, gates, budget, kill switch
│   └── dsh-tool-*                # the tools roles may mount
├── presets (one per role)
│   ├── supervisor   → dispatch_* tools, gate tools, no write tools
│   ├── analyst      → read/search/fetch + write_spec (docs/specs only)
│   ├── architect    → read + write_adr (docs/adr only)
│   ├── builder-be   → read/edit/bash/tests, own worktree, no deploy
│   ├── builder-fe   → read/edit/node/tests, own worktree, no deploy
│   ├── builder-data → read/sql/migrations (write file, never apply)
│   ├── verifier     → read/test/scan/ephemeral-deploy, no write tools
│   └── operator     → deploy_staging auto, deploy_prod gated, read observability
└── orchestration
    ├── supervisor session drives phases with the workflow tool
    └── one `subagent` tool instance per role → child preset + depth + cwd
```

**Dispatch path.** The supervisor calls `dispatch_architect` (a `subagent`-family tool bound to the architect provider with `childPreset: architect`). The child runs with only the architect tools, its own cwd (a worktree), its own model route, and returns a completion notice plus evidence ids. The supervisor then calls `evaluate_gate({ gate: 'GATE_B', runId })`; the gate reads the evidence registry and the artifacts, never the child's prose. A failed gate returns a bounded revision request.

**Why not "one general subagent with a prompt"?** Because a prompt-level capability is bypassable by the model and unverifiable by the reviewer. Composition makes the capability testable: the child either has the tool or it does not, and `tools/change` plus the schema list prove it.

### 4.3 Role roster v1

| Role | Preset | Mounted tools (summary) | Write scope | Model route | Output artifact |
|---|---|---|---|---|---|
| supervisor | `fs-supervisor` | `dispatch_*`, `evaluate_gate`, `record_evidence`, `read_gate_state`, `escalate_human` | none | strong reasoning model | `OrchestrationReport` |
| analyst | `fs-analyst` | `read`, `grep`, `glob`, `web_search`, `secure_fetch`, `write_spec`, `record_evidence` | `docs/specs/**` | fast model | `SpecArtifact` |
| architect | `fs-architect` | `read`, `grep`, `glob`, `write_adr`, `record_evidence` | `docs/adr/**` | strong reasoning model | `ArchitectureArtifact` |
| builder-be | `fs-builder-backend` | `read`, `edit`, `write`, `bash`, `pwsh`, test runner, `record_evidence` | own worktree | coding model | `Patch + Evidence` |
| builder-fe | `fs-builder-frontend` | same + node/package tools, browser test runner | own worktree | coding model | `Patch + Evidence` |
| builder-data | `fs-builder-data` | `read`, SQL client (read-only), migration file writer | worktree `db/**` | coding model | `Migration + Evidence` |
| verifier | `fs-verifier-{blind,edge,acceptance,security,perf}` | `read`, test runner, scanners, ephemeral deploy, `record_evidence` | **none** (evidence store only) | **different provider** | `VerificationReport` |
| operator | `fs-operator` | `deploy_staging`, `deploy_prod` (gated), `rollback`, observability read | none | ops model | `OperationReport` |

> **Model routing caveat.** A DSH preset chooses tools, prompt sections and skills; it does not by itself pin a model. Workflow agents accept explicit `provider`/`model` overrides, while a local subagent child inherits the entry point's default route unless its provider exposes a child route. Verifier independence therefore must be established per delegation route and asserted by a config test. This is the one open item in the isolation design and the reason for day 4 of the first-10-days plan.

**Mapping from platform v3.** Business Analyst → analyst; Product Strategist → analyst drafts, **human decides priority**; Solution Architect → architect; Frontend/Backend/Database/Integration/AI Engineer → builder profiles; DevOps → operator; the seven verifier roles → verifier modes; Keelgate/Approval/Audit/Budget → gatekeeper + secure-mesh + budget ledger; Memory/ADR/Incident/Pattern → memory service with a write gate; Self-Healing → operator runbook mode, deferred. Twenty roles become six roles and five verifier modes — the same decision rights with a fraction of the evaluation surface.

### 4.4 Guarantee → seam → test

Every row is a control the platform claims. The third column is the test that must fail if the seam is removed.

| # | Guarantee | Seam in DSH | Test that proves it |
|---|---|---|---|
| 1 | A role cannot call a tool it was not granted | Preset composition (tool absent) + secure-mesh `denyTools` | Child calls a sibling tool → `UNKNOWN_TOOL`; eval corpus of bypass prompts → 0 successes |
| 2 | A builder cannot write outside its worktree/scope | Per-role cwd + fs sandbox + branch allowlist | Attempt to edit `../` or push `main` → denied, audited |
| 3 | No production effect without an approved proposal | Gatekeeper pre-execute requires a one-time commit token bound to `(tool, argsHash)` | Forged token, changed args, expired token, replayed token → all denied |
| 4 | Evidence cannot be fabricated | Gate reads the evidence registry; records carry producer identity + hash | Model claims PASS with no record → gate FAIL; forged record hash → BLOCKED |
| 5 | Verifier cannot modify code | Verifier preset has no write tools + read-only fs | Attempted `write`/`edit` → tool absent; evidence-store write only |
| 6 | Untrusted input cannot change policy | secure-mesh fencing; policy reads records/args, never prose | Injection corpus in tickets/docs → no policy change; fence tokens present |
| 7 | Approval cannot be replayed or widened | Args hash + intent hash + TTL + consumed state | Re-submit approved bytes for a different order → `stale_args` |
| 8 | Budget cannot be exceeded silently | Ledger + pre-execute denial + checkpoint | Force 120% of token budget → `BUDGET_EXHAUSTED`, run checkpointed, escalated |
| 9 | Kill switch stops effects without a deploy | Runtime flag read in `tools/pre-execute`/guard | Flip flag → every effectful call denied within one call; reads still work |
| 10 | Audit cannot be silently truncated | Hash chain + off-box ship + verifier job | Edit/delete a line → `verifyRecords` fails from that point |
| 11 | Context does not leak between phases | Spawn (not fork) child + slice prompt + redaction | Plant a secret outside the slice → child references it → contamination flag |
| 12 | Verifier independence is real | Different provider/model route pinned in preset | Same-route configuration fails a config test; agreement metric monitored |
| 13 | Gates cannot be self-graded | Gate owner ≠ artifact producer; gate runs in gatekeeper, not child | Child calls `evaluate_gate` on its own artifact → denied by role check |
| 14 | Memory cannot be poisoned | Write gate (GATE_M) + provenance + conflict check | Unverified artifact write → blocked; conflicting entry → needs resolution |

### 4.5 Proposal and approval lifecycle

```text
propose_action(tool, args, intent, blastRadius, rollbackPlan, verificationPlan)
        │  computes argsHash, intentHash; TTL; idempotencyKey
        ▼
   pending ──approve(checklistAck)──► approved ──commit(token)──► consumed
        │                                  │                         │
        └──reject──► rejected              └──expire──► expired      └──verify──► verified
```

- **In-turn approvals** use `ctx.approval` (the Web client answerer) and are logged as the durable `approval/asked` + `approval/decided` pair. This is the normal path for a live run.
- **Cross-turn approvals** (the "two days later" case) cannot use `ctx.approval`; the gatekeeper records the proposal and exposes `approve_proposal` / `reject_proposal` to a human surface (CLI, web page, or ChatOps). The decision is stored with reviewer identity and checklist hash.
- **Commit is bound to bytes.** `commit_proposal(proposalId)` verifies approved + unexpired + checklist + `argsHash` of the actual pending call, then mints a single-use commit token. The effect tool requires the token; `tools/pre-execute` recomputes the args hash, rejects mismatches (`stale_args`), and consumes the token. A re-plan, a retry with different arguments, or a redirect to another object cannot reuse the approval.
- **Rubber-stamp mitigation.** The approval surface renders a checklist derived from `blastRadius` and `rollbackPlan`; a decision without acknowledgement is stored, flagged `rubber_stamp_suspected`, and does not authorise the commit.
- **Idempotency.** `idempotencyKey = hash(runId, tool, argsHash)`; a retry returns the existing proposal instead of creating a second executable one. Commit is exactly-once per proposal.

```ts
export interface ActionProposal {
  readonly id: string
  readonly runId: string
  readonly dispatchId: string
  readonly role: RoleId
  readonly tool: string
  readonly effect: EffectId
  readonly args: Readonly<Record<string, unknown>>
  readonly argsHash: string          // sha256(canonicalJson({tool, args})).slice(0, 32)
  readonly intentHash: string        // hash of the user's stated scope (ticket/order/feature)
  readonly blastRadius: string
  readonly rollbackPlan: string
  readonly verificationPlan: string
  readonly idempotencyKey: string
  readonly createdAt: string
  readonly expiresAt: string
  status: 'pending' | 'approved' | 'rejected' | 'expired' | 'consumed' | 'verified'
  decision?: { by: string; at: string; checklistHash: string; rubberStampSuspect: boolean }
  commitTokenHash?: string
}
```

### 4.6 Evidence registry

Evidence is the only currency a gate accepts.

```ts
export type EvidenceKind =
  | 'spec' | 'adr' | 'diff-manifest'
  | 'build' | 'unit-tests' | 'integration-tests' | 'e2e-trace'
  | 'coverage' | 'sast' | 'dependency-scan' | 'container-scan' | 'sbom'
  | 'migration-check' | 'restore-drill' | 'smoke-tests'
  | 'observability-check' | 'design-review' | 'blind-review'
  | 'approval-record' | 'human-ack'

export interface EvidenceRecord {
  readonly id: string                  // ev_<sha256(canonical payload).slice(0,16)>
  readonly runId: string
  readonly dispatchId: string
  readonly role: RoleId
  readonly kind: EvidenceKind
  readonly command: string             // exact command, no shell interpolation
  readonly exitCode: number
  readonly startedAt: string
  readonly endedAt: string
  readonly artifact: { path: string; sha256: string; bytes: number; mediaType: string }
  readonly environment: {
    commit: string
    imageDigest?: string
    worktree?: string
    toolVersions: Record<string, string>
  }
  readonly scope: string[]             // files, routes, or criteria covered
  readonly producer: 'ci' | 'tool' | 'human'
  readonly signature?: string          // HMAC by the CI producer; absent for local tool runs
}
```

**Verification rules** (all must hold, otherwise the gate is BLOCKED, never PASS):

1. Record exists in the registry for this run and kind.
2. `artifact.sha256` matches the bytes at `artifact.path`.
3. Producer is trusted for the kind (`ci` for build/scan/e2e; `tool` for tests run in the sandbox; `human` for approvals).
4. `environment.commit` equals the run's integration commit.
5. `scope` covers the gate's requirement (e.g. every changed file is covered by a test record, every critical route by an e2e trace).
6. `endedAt` is within the freshness window (default 24 h) and after the last relevant change.
7. For security kinds, no open HIGH/CRITICAL finding remains.

### 4.7 Gate engine

```ts
export interface GateSpec {
  readonly id: GateId
  readonly name: string
  readonly ownerRole: RoleId
  readonly requiredEvidence: readonly { kind: EvidenceKind; min?: number; scope?: 'changed' | 'critical' | 'all' }[]
  readonly artifacts: readonly string[]
  readonly predicate: (ctx: GateContext) => GateResult   // pure; no I/O, no clock, no random
  readonly onFail: 'revise' | 'block' | 'escalate' | 'rollback'
  readonly maxRevisions: number
}

export type GateResult =
  | { status: 'PASS'; checks: CheckResult[] }
  | { status: 'FAIL'; checks: CheckResult[]; defect: { criterion: string; evidence: string } }
  | { status: 'BLOCKED'; reason: string }
  | { status: 'TIMED_OUT'; afterMs: number }
```

- The predicate receives a snapshot (`GateContext`) built by the gatekeeper from the store: artifacts, evidence records, proposal state, budget, changed-file list. It performs no I/O so it is replayable and testable.
- **No self-grading:** `evaluate_gate` rejects when the caller role produced the artifact or evidence under review. The supervisor owns the call, but the gate's `ownerRole` defines who may produce the required evidence.
- **Revision semantics:** a revision requires a specific failed check mapped to a requirement and an evidence id. "Make it better" is invalid. Counters persist; reset is impossible through the tool surface. Two consecutive full loops without a strictly higher pass ratio → `ESCALATE`.
- **Statuses never collapse:** timeout ≠ fail ≠ blocked. None of them pass.

### 4.8 Budget ledger and kill switch

- **Metering:** at each step boundary, read `ctx.tokenMeter.measure(session)` for the run; attribute tokens to the active dispatch; for subagent children, measure their sessions. Cost = tokens × route price table in config (per provider/model). Wall clock from dispatch start. This is approximate but monotone and auditable; provider-reported usage is reused when available.
- **Enforcement:** `tools/pre-execute` denies effectful calls once a budget unit is exhausted; reads may continue until the wall clock ends. The run stops with `BUDGET_EXHAUSTED`, a checkpointed state, and an escalation record — never an opaque throw.
- **Cost attribution:** per run, role, model, and gate; the supervisor's report carries the breakdown; dashboards show cost per successful run.
- **Kill switch:** a runtime flag (file + SQLite row, cached ≤2 s) read by pre-execute and the guard. Flipping it turns every `severity > 0` effect to `FORBIDDEN` without a restart or deploy; reads remain available for triage. It is set only by the `human` role (or a delegated operator with an approval), is audited, and is drilled quarterly.

### 4.9 Isolation matrix

| Role | Tool surface | Working dir | Network | Write paths | Secrets | Model route |
|---|---|---|---|---|---|---|
| supervisor | dispatch/gate only | run root (read) | none | none | none | strong reasoning |
| analyst | read/search/fetch | run root (read) | `secure_fetch` allowlist (docs hosts) | `docs/specs/**` | none | fast |
| architect | read + ADR writer | run root (read) | none | `docs/adr/**` | none | strong reasoning |
| builder-* | read/edit/shell/tests | **own worktree** | registry allowlist via package proxy; no general egress | worktree only | repo-scoped deploy tokens **absent** | coding |
| verifier | read/test/scan/ephemeral | worktree at the diff commit (read) | scanner DB mirrors; ephemeral deploy API | evidence store only | ephemeral env creds only | **different provider** |
| operator | deploy/rollback/observe | run root (read) | deploy API + observability | none | deploy creds, production-scoped | ops |

Two of these columns are native DSH mechanisms rather than design wishes: `dsh-fs-sandbox` confines each **session** to its own workspace root and sandbox mode (`read-only` for the verifier, `workspace-write` inside the builder's worktree), and a child's `cwd` is set at dispatch. The model column is the exception: route selection is a delegation-route concern (see the caveat under §4.3), so it is verified by a test rather than assumed.

The important negative claims are testable: a builder has no deploy credential, the verifier has no write tool, and the supervisor has no write tool. Those are composition facts, not prompt requests.

### 4.10 Memory and the learning loop

Memory is a service, not an agent. The write gate (`GATE_M`) accepts only artifacts already verified by a gate (ADR after GATE_B, incident after the postmortem is approved, pattern after a human review), records provenance and the verifying gate id, and refuses conflicting entries until a human resolves them. Retrieval is ACL-filtered and marks staleness. This closes the poisoning loop: the model cannot write its own memory directly, and what it retrieves carries a provenance chain.

### 4.11 The security guide as an executable policy pack

`Agent design with security v2.md` §14 lists one test per control — the most valuable content in all three attachments. Turn it into a **stack policy pack** consumed by GATE_D when the project's stack profile matches (FastAPI/Postgres/React/Azure):

| Security v2 control | Pack check (machine) | Evidence kind |
|---|---|---|
| §3.1 Entra token validation | Expired/wrong-aud/wrong-tenant/unsigned token tests pass | `integration-tests` with scope `auth` |
| §3.2 Object-level authZ | Every `/{id}` route has a BOLA test returning 404 | `integration-tests` scope `bola` |
| §5.3 RLS | Query without context → 0 rows; `SET` vs `SET LOCAL` leak test | `integration-tests` scope `rls` |
| §4.2 Headers/CSP | Header assertions on HTML and API responses | `integration-tests` scope `headers` |
| §4.3 Parameterized SQL | Lint rule active; sort/filter allowlist rejects unknown fields | `sast` + `unit-tests` scope `sql` |
| §4.6 Idempotency | Same key twice → one effect, same response | `integration-tests` scope `idempotency` |
| §6.2 SafeMarkdown | XSS corpus renders inert; external images removed | `unit-tests` scope `xss` |
| §7.3 Uploads | Oversize, wrong magic, macro, zip bomb, traversal rejected | `integration-tests` scope `uploads` |
| §8.5 Health/readiness | Graph down → `/ready` 200; DB down → 503 | `integration-tests` scope `ready` |
| §9.4 Restore | Drill record with measured RTO in the last 30 days | `restore-drill` |
| §12.5 Audit | `audit_writer` has INSERT only; no UPDATE/DELETE | `integration-tests` scope `audit-grants` |
| §14 | The control-to-test table itself is the pack manifest | pack version pinned in the run |

A project that does not use this stack uses its own pack; the gate mechanism is unchanged. That is how a 45 KB standard becomes a gate instead of a hope.

---

## 5. What I would change in the concept (ranked)

| # | Change | Why | Effort |
|---|---|---|---|
| 1 | **Freeze one substrate** (DSH primary; LangGraph only as an optional outer durable workflow) | Two policy planes = one bypass; two state stores = no single record | S |
| 2 | **Six roles + capability profiles**, not 20 | Span of control, evaluation cost, and the concept's own 5-subagent rule | S |
| 3 | **Capability is composition**; tokens become audit records | A grant in a prompt cannot deny a call | M |
| 4 | **EvidenceRecord registry** instead of `evidence_uri` | A URL is fabricable; a hash + producer is not | M |
| 5 | **Gates as code** with no self-grading, explicit `BLOCKED`/`TIMED_OUT`, persisted revision counters | Removes the "LLM grades itself" failure and silent timeouts | M |
| 6 | **Durable proposal store** + human decision surface; `ctx.approval` only for in-turn | "Approve two days later" is impossible with turn-scoped approval | M |
| 7 | **Budget ledger + kill switch as plugins** | The docs assume Keelgate does this; DSH does not ship it | M |
| 8 | **Engineer verifier independence** (different provider, blind input, separate worktree, agreement metric) | Same model + shared history fails together | S–M |
| 9 | **Security guide → versioned policy pack** with evidence kinds per check | Turns 45 KB of prose into gate requirements | M |
| 10 | **Build the eval harness before the builders** | Otherwise "it works" is unmeasured, and gate regressions ship silently | M |
| 11 | **Memory as a service with GATE_M** | An agent that writes its own memory can self-approve and poison | S |
| 12 | **Defer self-healing; define its ceiling now** | Highest blast radius, least specified control | S (now), L (later) |
| 13 | **Context-contamination checks + redaction at the dispatch boundary** | Slices minimise context but do not prove isolation | S |
| 14 | **Prompt/policy parity test in CI** | Prevents documentation drift back into "advisory controls" | S |
| 15 | **10-week MVP + 6-month programme**, with exit criteria and a pilot repo | The 6-week plan omits evaluation, memory, and the security pack | S |
| 16 | **Single-writer audit by architecture** (ACL + off-box shipping), not by convention | In-process plugins share the filesystem | S |

---

## 6. Delivery plan

### 6.1 Phases, deliverables, exit criteria

Assumed team: 1 tech lead, 2 engineers, 0.5 security engineer, 0.5 platform engineer. Durations are elapsed weeks.

| Phase | Weeks | Deliverables | Exit criteria (all must hold) |
|---|---|---|---|
| **P0 — Decisions & contracts** | 1 | 4 ADRs (substrate, control plane, roster, state store); threat model; effect matrix; gate catalog; role/preset designs; eval plan | Signed ADRs; every guarantee in §4.4 has a named seam and a test; no open ambiguity on approval durability |
| **P1 — Gatekeeper substrate** | 2–3 | `dsh-gatekeeper` plugin: proposal store, evidence registry, gate engine, budget ledger, kill switch, commit tokens; unit + property tests | 100% of §4.4 rows 3,4,7,8,9,10,13 pass; conformance vs `reference/agentkit` decisions; audit chain verifies |
| **P2 — Roles & isolation** | 3–4 | 6 role presets, tool compositions, worktrees, model routes, role prompts, `dispatch_*` tools, supervisor workflow | A builder child cannot see deploy tools; verifier has no write tool; child cwd isolation proven; prompt/policy parity test green |
| **P3 — End-to-end gates & evidence adapters** | 5–6 | CI evidence producer (build/test/SARIF/coverage/e2e/SBOM), approval surface, GATE_A–F, DoD evaluator | One real feature runs A→F on a pilot repo; every PASS has resolvable evidence; a planted failure blocks at the right gate |
| **P4 — Eval, security pack, red team** | 7–8 | Eval harness (golden tasks, injection corpus, bypass corpus, fabrication corpus), fastapi-react pack v1, red-team report | Task success baseline recorded; unsafe effects 0; fabrication corpus 0 PASS; pack checks run in GATE_D |
| **P5 — Pilot in limited production** | 9–10 | Dashboards, SLOs, runbooks, cost attribution, memory write gate, kill-switch drill | 2 weeks of pilot runs; cost per success within budget; approval latency measured; zero unreviewed production effects |
| **P6 — Guarded self-healing (optional)** | 11+ | Pre-approved runbook executor, blast-radius caps, auto-rollback, quarterly drill | Only runbooks that have been executed manually N times; no schema/data deletion; kill switch proven |

### 6.2 Work packages and estimates

| Package | Contents | Person-days |
|---|---|---|
| WP1 Gatekeeper core | store (SQLite/JSONL), proposals, evidence, gates, commit tokens, kill switch | 12 |
| WP2 Budget ledger | token meter hook, price table, denial, checkpoint/escalation | 5 |
| WP3 Evidence adapters | GitHub Actions, pytest/vitest, Playwright, Semgrep SARIF, coverage, SBOM, signed records | 8 |
| WP4 Role presets | 6 presets, prompts, tool compositions, worktree helper, model routes | 8 |
| WP5 Orchestration | supervisor workflow, dispatch tools, gate loop, escalation, DoD report | 8 |
| WP6 Approval surfaces | CLI + web page/ChatOps, checklist rendering, rubber-stamp flags | 5 |
| WP7 Eval harness | golden tasks, corpora, runner, scorecard, CI gate | 10 |
| WP8 Security pack | fastapi-react pack v1, mapping table, pack runner | 6 |
| WP9 Observability | dashboards, SLOs, alerts, cost attribution | 5 |
| WP10 Docs/ADR/runbooks | decisions, operator guide, incident runbooks | 4 |
| **Total** | | **~71 person-days (≈ 7–8 weeks for 2 engineers, plus review time)** |

### 6.3 Repository layout

```text
dsh-engineering-agent/
├── packages/
│   ├── gatekeeper/                # @acme/dsh-gatekeeper  (bundle + plugin)
│   │   ├── src/
│   │   │   ├── index.ts           # apply(ctx, config): tools, hooks, guard
│   │   │   ├── store.ts           # runs, dispatches, proposals, evidence, gates
│   │   │   ├── proposals.ts       # hash binding, TTL, single use
│   │   │   ├── evidence.ts        # registry + verification rules
│   │   │   ├── gates.ts           # GateSpec engine + predicates
│   │   │   ├── budget.ts          # ledger + meter hook
│   │   │   ├── killswitch.ts      # runtime flag
│   │   │   └── policy.ts          # effect matrix -> PreToolDecision
│   │   └── tests/
│   ├── role-analyst/
│   ├── role-architect/
│   ├── role-builder/              # profile: backend | frontend | data
│   ├── role-verifier/             # mode: blind | edge | acceptance | security | perf
│   ├── role-operator/
│   └── evidence-adapters/
├── profiles/fullstack-engineer/
│   ├── package.json               # dsh.profile.bundles
│   └── cordis.patch.yml
├── policy/
│   ├── effect-matrix.yaml
│   ├── gate-catalog.yaml
│   └── stacks/fastapi-react.yaml
├── evals/
│   ├── golden/ injection/ bypass/ fabrication/
│   └── run.mjs
└── docs/{ADR,runbooks}/
```

### 6.4 Interfaces (implementation detail)

**Task envelope.** Every dispatch carries it; the child receives only `objective`, `contextSlice`, `acceptanceCriteria`, and `constraints`.

```ts
export interface TaskEnvelope {
  readonly taskId: string
  readonly parentRunId: string
  readonly phase: 'A' | 'B' | 'C' | 'D' | 'E' | 'F'
  readonly objective: string
  readonly scope: { in: string[]; out: string[] }
  readonly acceptanceCriteria: Array<{ id: string; criterion: string; testMethod: string }>
  readonly constraints: string[]
  readonly riskLevel: 'low' | 'medium' | 'high' | 'critical'
  readonly budget: { iterations: number; tokens: number; wallClockMs: number; costUsd: number }
  readonly contextSlice: { files: string[]; artifacts: string[]; redactions: string[] }
  readonly idempotencyKey: string
}
```

**Gate evaluation.** The gatekeeper builds the context from its store, so predicates are pure.

```ts
export function evaluateGate(spec: GateSpec, ctx: GateContext): GateResult {
  const checks: CheckResult[] = []
  for (const req of spec.requiredEvidence) {
    const records = ctx.evidence.filter(e => e.kind === req.kind)
    checks.push(checkEvidence(req, records, ctx))
  }
  for (const artifact of spec.artifacts) checks.push(checkArtifact(artifact, ctx))
  if (checks.some(c => c.status === 'BLOCKED')) return { status: 'BLOCKED', reason: firstBlocked(checks) }
  if (checks.some(c => c.status === 'TIMED_OUT')) return { status: 'TIMED_OUT', afterMs: ctx.elapsedMs }
  const failed = checks.filter(c => c.status === 'FAIL')
  return failed.length === 0
    ? { status: 'PASS', checks }
    : { status: 'FAIL', checks, defect: toDefect(failed[0]!) }
}
```

**Commit binding.**

```ts
const material = `${p.id}|${p.argsHash}|${p.intentHash}|${p.expiresAt}`
const token = hmacSha256(secret, material)
// tools/pre-execute for an effectful tool:
const { proposalId, commitToken } = readCommitFields(exec.arguments)
const p = store.getProposal(proposalId)
const expected = hmacSha256(secret, `${p.id}|${argsHash(exec.name, exec.arguments)}|${p.intentHash}|${p.expiresAt}`)
if (!timingSafeEqual(commitToken, expected)) return { kind: 'deny', reason: 'stale or forged approval' }
if (p.status !== 'approved' || Date.now() >= Date.parse(p.expiresAt)) return { kind: 'deny', reason: 'approval expired or not approved' }
store.consume(p.id)      // exactly once
return next()
```

**Budget gate.**

```ts
ctx.on('tools/pre-execute', async (exec, next) => {
  const run = store.activeRun()
  if (run === undefined) return next()
  const spent = ledger.snapshot(run.id)
  if (spent.costUsd >= run.budget.costUsd || spent.wallClockMs >= run.budget.wallClockMs) {
    if (EFFECTS[exec.name].severity > 0) {
      return { kind: 'deny', reason: 'BUDGET_EXHAUSTED: run checkpointed, escalate to a human' }
    }
  }
  return next()
})
```

**Role preset (illustrative; exact composition validated in the P0 spike).** A preset composes child plugins — tools, prompt sections and skills. Model routing is not a preset field; it belongs to the delegation route (workflow agent override or a provider that exposes a child route).

```yaml
- id: preset-fs-builder-backend
  name: '@deepseek-ai/dsh-agent-preset'
  config:
    id: fs-builder-backend
    name: 'Full-stack builder — backend'
    plugins:
      - name: 'dsh-role-builder'
        config:
          profile: backend
          worktree: '{{run.worktree}}'
          writePaths: ['services/**', 'tests/**']
      - name: 'dsh-secure-mesh'
        config:
          secureFetch: true
          denyTools: ['deploy_prod', 'deploy_staging', 'write_shared']
          askTools: ['bash']
          wrapTools: ['web_fetch', 'web_search']
      - name: '@deepseek-ai/dsh-tool-fs'
      - name: '@deepseek-ai/dsh-tool-bash'
```

### 6.5 CI/CD integration

Each pipeline publishes evidence; nothing else may produce a PASS:

1. `build` job → `ev-build` (image digest, commit).
2. `unit` / `integration` jobs → JUnit XML + coverage XML → `ev-tests`, `ev-coverage` with changed-file scope.
3. `sast` (Semgrep) → SARIF; `ev-sast` includes the open-finding summary; HIGH/CRITICAL blocks.
4. `sca` / container scan / SBOM → `ev-dependency-scan`, `ev-sbom`.
5. `e2e` (Playwright) → trace + per-route results → `ev-e2e-trace` with critical-path scope.
6. Staging deploy + smoke → `ev-staging-smoke`; production proposal references it.
7. Restore drill (separate monthly job) → `ev-restore-drill` with measured RTO.

The producer signs the record (HMAC with a CI-only key, or Sigstore); the gatekeeper verifies before accepting. The agent never writes CI evidence directly; it can only *request* a run and read the records.

### 6.6 Test strategy

| Layer | What | Gate |
|---|---|---|
| Unit | policy decisions, proposal state machine, gate predicates, budget arithmetic | P1 CI |
| Property/conformance | TS port vs `reference/agentkit` decisions on generated inputs (args hashes, TTL, states) | P1 |
| Integration | real Cordis `Context` + `ToolRuntime` + `SystemPrompt` + presets; tool denial with body spy; approval fail-closed | P2 |
| Red team | injection corpus, forged evidence, gate bypass, TOCTOU, approval replay, kill switch, context leak | P4 |
| Evals | 20–30 golden tasks across greenfield/feature/bugfix; metrics: task success, unsafe effects, evidence resolution rate, cost per success, rework rate | P4/P5 |
| Release | eval regression + pack checks + kill-switch drill | every release |

### 6.7 Operations

- **Dashboards:** runs by terminal state; gate pass rate by gate and role; approval latency and rubber-stamp flags; cost per success by role/model; unsafe effects (target 0); evidence resolution failures; kill-switch state.
- **SLOs:** gate evaluation p95 < 2 s; approval routing < 5 min (P1 incidents < 15 min); zero unreviewed production effects; evidence resolution 100%.
- **Runbooks:** budget exhaustion, approval stuck, evidence producer down, kill switch, rollback, model provider outage (degradation ladder: verifier fallback is *not* the builder model; if no independent route exists, block).
- **Drills:** quarterly kill switch; monthly restore/evidence audit (sample 10 records, re-verify hashes).

---

## 7. Risks and mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Approval fatigue → rubber stamping | High | High | Risk-tier only the irreversible; checklists derived from blast radius; latency + flag metrics; sample human review of approvals |
| R2 | Evidence theatre (stale, wrong-scope, fabricated) | Medium | High | Signed records, freshness, commit binding, producer allowlist, monthly sample audit, hash re-verification |
| R3 | Cost blow-up | High | Medium | Hard budgets, model tiering, stop on no metric improvement, cost per success as a release gate |
| R4 | Verifier correlates with builder | High | High | Different provider route, blind input, separate worktree, disagreement metric, planted-defect calibration |
| R5 | Gate bypass through an unclassified tool | Medium | Critical | Complete tool inventory test: every registered tool must have an effect; unknown effect = FORBIDDEN; weekly drift check |
| R6 | Prompt injection through docs, tickets, web | High | High | secure-mesh fencing, summarise-then-cite, policy reads records not prose, injection corpus in evals |
| R7 | The agent modifies its own guardrails | Low | Critical | Policy, gate catalog, and gatekeeper config live outside the agent's writable roots; signed; changing them requires a human-approved proposal |
| R8 | DSH upgrade breaks a seam | Medium | Medium | Pin harness versions, adapter layer, integration tests in CI, upgrade ADR |
| R9 | Multi-day approval state divergence | Medium | High | Single gatekeeper store; TTL; revalidate hash at commit; no side channel approvals |
| R10 | v1 scope creep | High | Medium | Roster freeze, single pilot repo, phase exit criteria, explicit deferrals (self-healing, 20 roles) |
| R11 | Secrets leak into evidence or logs | Medium | High | Redaction at capture, secret scanning of artifacts, no env dumps, evidence retention policy |
| R12 | Generated code passes gates but is insecure | Medium | High | Stack policy pack, SAST + dependency scan as mandatory evidence, adversarial review, threat-model checks |
| R13 | Operator causes destructive change | Low | Critical | Effect matrix forbids `delete_data`/`change_iam`; separate credentials; backups + restore drill; kill switch |

---

## 8. Decisions (accepted 2026-11-04)

> **Status:** the decisions below were accepted on 2026-11-04 and are recorded in full, with consequences and follow-ups, in [`DECISIONS.md`](./DECISIONS.md). One revision: D2 (pilot target) is now a **dedicated pilot repository**, not an existing production repo (ADR-002).

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | Substrate | (a) DSH-native; (b) LangGraph outer durable workflow calling DSH workers; (c) full LangGraph re-implementation | **(a)**, with (b) as an option only if workflow durability beyond DSH sessions is a hard requirement |
| D2 | Pilot target | (a) existing FastAPI + React repo; (b) greenfield service; (c) a maintenance/bugfix workload | **(a)**, because it exercises the security pack and the verifier meaningfully; pick one repo and freeze it for 6 weeks |
| D3 | Builder autonomy | (a) open PRs, humans merge; (b) merge to a `dev` branch after gates; (c) no pushes, patches only | **(a)** for the pilot; promote to (b) after 4 weeks of clean gate history |
| D4 | Model routes | (a) two providers (one for builder, one for verifier); (b) one provider, different model sizes; (c) one model | **(a)**; if (b)/(c), add compensating controls (human sample review, stronger eval corpus) and record the residual risk |
| D5 | Hosting for the platform | (a) single VM + Docker; (b) Azure Container Apps + managed Postgres | **(a)** for the pilot; move to (b) when the approval store and audit need HA |
| D6 | Compliance scope | Which security-v2 P0 checks are mandatory at GATE_D for the pilot | Start with token validation, BOLA, RLS, headers/CSP, parameterized SQL, SafeMarkdown, idempotency, readiness, audit grants; defer uploads/restore until the pilot feature touches them |

---

## 9. First 10 working days

| Day | Work | Output |
|---|---|---|
| 1 | ADR-0001 substrate; tool/effect inventory; roster freeze | Signed ADRs, effect matrix v1 |
| 2 | Threat model workshop (security + platform); gate catalog review | Threat model, gate catalog v1 |
| 3 | Spike: one role preset (builder-be) + one `dispatch_*` tool; prove tool absence and cwd isolation | Spike report, preset prototype |
| 4 | Spike: child model route + permission roots; confirm what DSH inherits | Isolation findings, residual-risk note |
| 5 | Gatekeeper skeleton: store + proposals + args/intent hashes + TTL | `@acme/dsh-gatekeeper` v0.1 with unit tests |
| 6 | Commit token + pre-execute denial + guard; replay/TOCTOU tests | Proposal lifecycle tests green |
| 7 | Evidence record schema + one CI producer (unit tests) | `ev-tests` records with hashes |
| 8 | Supervisor workflow skeleton (GATE_A → GATE_B) + `evaluate_gate` | End-to-end A→B demo on a toy repo |
| 9 | Eval harness skeleton: one golden task, one injection case, one bypass case | `evals/run.mjs` baseline |
| 10 | Demo + go/no-go review against phase P1 exit criteria | Decision memo |

---

## Appendix A — Gate catalogue

See [`gate-catalog.yaml`](./gate-catalog.yaml) for the machine-readable gates (GATE_A–GATE_F, GATE_M), their required evidence, predicates, revision policy and failure actions. The gates in the catalogue are the ones this plan implements; additions require an ADR.

## Appendix B — Stack policy pack sample

```yaml
# policy/stacks/fastapi-react.yaml (excerpt)
id: fastapi-react
version: 1.0.0
applies_when:
  files_any: ['backend/app/main.py', 'frontend/package.json']
checks:
  - id: auth-token-validation
    source: 'Agent design with security v2.md §3.1'
    evidence: integration-tests
    scope: auth
    assert: [expired_rejected, wrong_audience_rejected, wrong_tenant_rejected, unsigned_rejected]
  - id: bola-404
    source: '§3.2'
    evidence: integration-tests
    scope: bola
    assert: [every_id_route_has_test, cross_tenant_returns_404]
  - id: rls-transaction-local
    source: '§5.3'
    evidence: integration-tests
    scope: rls
    assert: [no_context_zero_rows, set_local_no_leak]
  - id: csp-and-headers
    source: '§4.2'
    evidence: integration-tests
    scope: headers
    assert: [csp_present, nosniff, referrer_policy, frame_ancestors]
  - id: parameterized-sql-lint
    source: '§4.3'
    evidence: sast
    scope: sql
    assert: [no_fstring_sql, sort_filter_allowlist]
```

The pack is versioned and pinned per run; a PASS cites the pack version and the evidence ids.

## Appendix C — Source map

| Claim in this plan | Where it comes from |
|---|---|
| Six subagents, typed envelopes, gates, proposals, failure modes | `Full stack engineer -agent concept.txt` §2–§11 |
| Security controls and their tests | `Agent design with security v2.md` §3–§14 |
| Enforcement seams (`pre-execute`, `guard`, `approval`, `restrict`, `post-execute`, prompt section) | `dsh-secure-mesh` v2.0.0 implementation + DSH source verified during its audit |
| Proposal hash binding, TTL, single use; effect autonomy; budget ledger; trace | `reference/agentkit/proposals.py`, `policy.py`, `budget.py`, `trace.py` |
| Presets as child-plugin compositions; subagent provider per role; token meter | DSH package READMEs (`dsh-agent-preset`, `dsh-tool-subagent`, `dsh-token-meter`) |
| Evidence record/freshness/producer rules | This plan (§4.6), derived from the audit lesson: a claim without a resolvable artifact is not evidence |

---

*This document is a proposal. The effect matrix and gate catalogue are v1 drafts to be reviewed with security and platform before any agent is allowed to write code.*

