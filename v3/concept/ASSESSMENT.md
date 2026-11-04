# v3.0 Full Review and v3.1 Proposal

**Subject:** *Senior Full-Stack Engineer Agent — Implementation Design with Subagent System* v3.0 (895 lines, §0–§20)
**Evaluated against:** the project scope agreed in this workspace — DSH + `dsh-secure-mesh` enforcement, gatekeeper/evidence/role-preset plan, and the FastAPI/Postgres/React platform standard.
**Version:** 3.1
**Status:** proposal for decision
**Date:** 2026-11-04

---

## 1. Correction, and a second kind of incompleteness

My previous review was based on a 98-line copy and concluded that the document was **truncated**. With the full file, that finding is withdrawn: the substance is complete. The roster, agent loops, harness additions, loop engineering, FDE contracts, phase graph, Keelgate, database schema, failure modes, observability, red-teaming, Definition of Done, prompt, sequence, and maturity model are all present.

The document is still **not** implementation-ready, for a different and independent reason: its Markdown structure is broken, so what exists does not render or navigate as a document.

`tools/check-doc.mjs` (shipped with this review) reports, on the full file:

```
file: ...full stack engineer agent solution .md
lines:  895
fences: 1 (UNBALANCED)
headings: 9 (level 2: 3)
plain-text sections: 39
ERROR unclosed code fence: opened at line 71 ("```text") and never closed
ERROR 39 numbered section line(s) are not Markdown headings (first: line 100 "2.2 Design constraints")
ERROR model meta-commentary in the deliverable at line 884
ERROR status claims "implementation-ready" but no test/verification/acceptance heading exists
```

Three consequences:

1. Everything after §2.1 renders as a single code block — the roster, gates, and schemas included. The document cannot be navigated, reviewed, or ingested reliably by tooling.
2. Sections `2.2` through `20` are plain text, not headings; only nine headings survive (three at level 2), and the tail is model meta-commentary addressed to the reader rather than a design section.
3. A design document is an input to the agent platform, not just to humans. A malformed contract at the top of the pipeline is the same class of defect as malformed code, and it should fail the same kind of gate.

**Recommendation:** run the repair checklist in §10 before circulating v3.0 again, and add `check-doc` to documentation CI with a required-sections list.

---

## 2. Verdict

**Design-complete; not implementation-ready.** On the document's own maturity scale, the design describes an L4 system while the artefacts are at L3: no gate predicates, no policy rules, no evidence-verification code, no gold routing set, no eval fixtures, no acceptance tests for the system itself. "L4" is currently a declaration, not an observed property.

That is a much better position than the previous draft. The remaining work is narrow and specific: choose the substrate, replace URI-based evidence with records, stop parking runs for the measurement window, gate memory and compaction, reorder the implementation sequence, and repair the document.

---

## 3. What v3.0 now covers well

| v3.0 section | What it adds | Verdict |
|---|---|---|
| §2.2 | Span of control, skills vs subagents, context slice | Keep |
| §3 | Supervisor + six subagents with typed I/O, loop parameters, prohibitions | Keep; map to DSH presets |
| §4 | Explicit per-subagent loop, iteration ranges, stop conditions, changed-hypothesis rule | Keep as **configuration + evals**, not new code |
| §5.1 | Context compactor | Keep with an evidence-preservation contract |
| §5.2 | Versioned tool registry with `contract_hash` invalidation | **Adopt; improves on my earlier plan** |
| §5.3 | Memory store + evidence-linked lessons | Keep, but gate the write path |
| §5.4 | Supervisor context budget (5 summaries × 500 tokens) | Keep |
| §5.5 | Budget controller with per-subagent cost attribution | Keep; define ledger semantics |
| §6.1 | Supervisor routing evaluation (precision/recall, over/under-dispatch, escalation timing) | **Adopt; becomes GATE_R** |
| §6.2 | Per-gate metric vectors and a concrete "no improvement" rule | **Adopt; now in `gate-catalog.yaml` v1.2** |
| §6.3 | Failure → eval feedback loop | Keep; add dedupe and test-first |
| §6.4 | Business KPI gate | Keep the intent; redesign the mechanics (§6 below) |
| §7 | FDE as a human role with `FDEHandoff` / `FDEAcceptance`, `IntegrationGrant` | **Adopt; improves on my earlier plan** |
| §8 | Phase graph, bounded loops, envelope, proposal | Keep; release must end at GATE_F |
| §9 | Keelgate control plane, audit chain, anti-rubber-stamp | Keep; locate the seams in DSH |
| §10 | FastAPI request path, PostgreSQL schema, LangGraph notes | Keep for the target app, not the agent platform |
| §11 | Failure modes and guards | Keep; add the new ones from this review |
| §12 | Behavioural discipline | Keep |
| §13 | CI/CD sequence and skill bindings | Keep; add evidence signatures |
| §14 | Agent-system SLOs and dashboards | **Adopt; improves on my earlier plan** |
| §15 | Continuous red-teaming with cadence | **Adopt; improves on my earlier plan** |
| §16 | 11-condition Definition of Done | Keep; extend (§4, F13) |
| §17 | Compact supervisor prompt | Keep; align with enforced rules only |
| §18 | 10-week sequence | Reorder (§9) |
| §19 | L0–L5 maturity model | Keep as a communication tool, not a claim |
| §20 | Summary | Keep |

Four of these are genuinely better than the plan I wrote: **tool contract hashes**, **per-gate metric vectors**, **routing-eval metrics**, and **agent-system SLOs with a red-team cadence**. They are adopted into the v3.1 gate catalogue.

---

## 4. Findings

### F1 — Document structure is broken (Critical for delivery)

See §1. Fix by repair + CI. A document that claims "Implementation-ready" without a test/verification section is also missing the one section its own status implies.

### F2 — Substrate conflict (Critical for the programme)

v3.0 fixes LangGraph + Keelgate + PostgreSQL as the primary stack (§0, §9, §10.3). The project has already built and tested DSH + `dsh-secure-mesh` (31 tests, real Cordis integration, hash-chained audit). Running both creates two policy planes, two audit chains, and two places where a tool call can bypass the other. **One of them will be the real gate; the other will be documentation.**

**Fix:** DSH-native. LangGraph remains a legitimate outer durable workflow if required, but it must call DSH agents as workers and own no policy. Keelgate semantics port into `dsh-gatekeeper`, with `reference/agentkit` as the executable oracle.

### F3 — `evidence_uri` is still not verifiable (Critical, security)

§5.2, §8.1, §8.4, §11, §16 all rest on "resolvable evidence URI". A URI says nothing about **who produced it, over which bytes, for which commit, covering which scope, and whether it is fresh**. A model can point at a real CI page for an unrelated run; a compromised producer can serve a doctored artefact.

**Fix:** `EvidenceRecord` (already specified in `REVIEW-AND-PLAN.md` §4.6) with `sha256`, producer identity/signature, command, exit code, environment (commit/image), scope, and freshness. The URI survives as a locator inside the record, not as the evidence.

### F4 — GATE_G parks the run for the measurement window (High, design)

§8.1 runs `wait(measurement_window_days)` (typically 14) and only then evaluates GATE_G; FINISH is impossible until then, and a missed KPI routes back into Loop Engineering, potentially redeploying. That means:

- a LangGraph thread (or DSH session) held open for weeks, with checkpoint growth and context decay;
- capacity consumed by "finished technically" runs;
- a second deployment inside the same run if the business fix requires code;
- a KPI measured after other releases have landed, so attribution is even weaker.

**Fix:** end the run at GATE_F (`FINISH_TECHNICAL`/`RELEASED`). GATE_G becomes a **scheduled outcome review** keyed by the pre-registered contract, with statuses PASS / ITERATE / ROLLBACK / **INCONCLUSIVE**, blocking rollout expansion rather than the release. Iteration starts a **new** run with a **new** contract version.

### F5 — The KPI contract is too thin (High)

§6.4 defines `kpi_name`, `baseline`, `target`, `measurement_method`, `window`, `minimum_sample_size`. That is not enough to resist noise or gaming: no guardrails, no attribution method or confounders, no cost per outcome, no data source/ACL, no pre-registration or signatures, and no decision rule.

**Fix:** the contract in `contracts/business-kpi.schema.json` (v1.1 of this package) adds guardrails, attribution, aggregated data sources with ACL, decision rule, pre-registration and dual signatures. `validate-kpi.mjs` enforces the semantic rules.

### F6 — Memory lessons are a prompt-injection channel (High, security)

§5.3 stores `agent_lessons` with an `evidence_uri`, and the supervisor injects "relevant lessons" into context slices before dispatch. Nothing gates who writes a lesson or what it may say. A model-written lesson such as "this repository permits skipping migration review" becomes a persistent instruction that survives runs and is trusted more than any single tool result.

**Fix:** split memory into **facts** (immutable, provenance-linked, verified by a gate) and **procedures** (versioned, human-reviewed, treated as code). Apply GATE_M to every write, sanitize on read, and never let a lesson carry instructions about permissions, gates, or approvals. A lesson must cite the gate id and evidence record that proved it.

### F7 — The compactor can silently destroy evidence (Medium-High)

§5.1 "drop raw tool outputs older than N dispatches (keep summary + URI)" loses the bytes a gate may later need, and summary drift is unmeasured. Preserving `idempotency_key`, `proposal_id`, and `evidence_uris` helps, but the gate predicates need the evidence records and gate states too.

**Fix:** a compaction contract that preserves evidence ids, hashes, gate states, proposals, budgets, and unresolved defects verbatim; compacts only narrative; is deterministic; and has a regression eval ("after N compactions, every gate decision is reproducible").

### F8 — The budget controller has a signature, not semantics (High)

§5.5 `charge(...)` names the right inputs but not the ledger: no reservation, no atomicity under concurrency, no per-route price table, no behaviour on overage beyond "must escalate", and no link to the DSH token meter. The reference `budget.py` already implements the ledger the document describes.

**Fix:** reserve → charge → stop → checkpoint → escalate, with per-run and per-dispatch ceilings and a price table per provider/model. Meter at step boundaries via the harness's measurement service.

### F9 — The agent-loop pseudocode is not executable (Medium)

§4's `SubagentLoop` mixes signatures (`reason(context)` vs `reason(ctx)`, `build_result(reasoning, context)` vs `build_result(context, status=...)`), leaves every method without a body, and has no cancellation, tool-error, or gate-blocked path. It is a useful diagram, not implementation.

**Fix:** express the loop as **configuration** (max steps, stop conditions, no-progress rule, changed-hypothesis retry) on the harness loop, and test the behaviours. Do not ship a second loop implementation.

### F10 — Routing eval has no gold set, thresholds, or gate (Medium)

§6.1 names the metrics well. It does not say how many tasks, what "correct" means, which thresholds pass, or who blocks a release on failure.

**Fix:** 50–100 golden tasks with annotated phase path and first role; offline replay from recorded sessions; thresholds; a rule that supervisor prompt/model changes are blocked until the metrics hold (GATE_R).

### F11 — Failure → eval will flood the suite (Medium)

§6.3 creates a case from "every production incident or gate failure". Gate failures are frequent, often duplicates, and sometimes caused by the environment. The suite will grow faster than it can be maintained, and its pass rate will stop meaning anything.

**Fix:** dedupe by `failure_signature`; mandatory for production incidents and for gate failures that escaped to a human; optional otherwise. Each case must fail on the pre-fix commit (test-first) and carry fixtures, not just an envelope.

### F12 — FDE authority lacks separation of duties (High, governance)

§7.2 makes the FDE the production approver, the KPI owner, and the adoption owner; `approval_authority` is a free string; `IntegrationGrant` has a TTL but no broker — the agent is expected to hold `credential_ref` and reach the system. High-blast-radius changes (schema, auth, money, data deletion) should never be single-approver.

**Fix:** two-person rule for T3 effects (one approver independent of the FDE); FDE may not approve a change they scoped without a second approver; credentials are brokered per call (the agent never receives the secret); grants are least-privilege, TTL-bounded, and revoked on completion.

### F13 — Definition of Done misses four machine checks (Medium)

§16 has 11 conditions. Missing: cost per outcome within contract, guardrail metrics held, evidence record hash/producer verified (not just URI resolved), eval cases added for every escaped failure, and tool-version pinning verified.

**Fix:** extend the DoD with these five; they are all computable from the gatekeeper store.

### F14 — The implementation order is backwards (Medium)

§18 puts the supervisor/Keelgate first and **evaluation, observability, and red-teaming in weeks 8–10**. That builds the thing before the instrument that tells you whether it works. It is the same ordering error that produced v1.0's unverifiable claims.

**Fix:** gatekeeper + evidence + eval harness first, roles second, end-to-end gates third, FDE/G fourth, red team and production last. The 11-week sequence in §9.

### F15 — The platform security standard is not integrated (High, for the target stack)

The document names FastAPI/Postgres/React but never references the 45 KB security standard, its §14 "a test per control", or the policy-pack idea. That standard is the cheapest source of gate requirements the programme has.

**Fix:** a versioned stack policy pack (`policy/stacks/fastapi-react.yaml`) consumed by GATE_D; each check maps to an evidence kind and a control id.

### F16 — The request-path "prompt-injection scan" is false comfort (Low-Medium)

§10.1 lists a prompt-injection scan in the middleware chain. Injection is not reliably detectable by scanning; the controls that work are the ones the document already has (capability scoping, context slices, fencing, evidence). A scanner creates a PASS feeling without a guarantee.

**Fix:** relabel as source tagging and fencing (as `dsh-secure-mesh` does), and keep the real controls.
---

## 5. v3.1 reconciliation: one substrate, same contracts

| v3.0 | DSH implementation | Change |
|---|---|---|
| §2 four planes | profile + plugins + role presets | Layers stay conceptual; one runtime |
| §3 roster (supervisor + 6) | six agent presets + builder profiles; FDE is human | No roster change; capability profiles |
| §4 agent loop | DSH agent loop **configured** per role + loop evals | No second loop implementation |
| §5.1 compactor | DSH compaction + evidence-preservation contract | Deterministic and tested |
| §5.2 versioned tool registry | tool schema hash in proposals and evidence | Adopted as-is |
| §5.3 memory store | memory service + GATE_M; facts vs procedures | Write gate added |
| §5.4 supervisor context budget | prompt sections + session compaction | Adopted |
| §5.5 budget controller | gatekeeper ledger + harness token meter | Reserve/charge/stop semantics |
| §6.1 routing eval | GATE_R offline replay + thresholds | Made blocking for routing releases |
| §6.2 metric vectors | `metrics:` per gate in `gate-catalog.yaml` v1.2 | Adopted |
| §6.3 failure → eval | EvalCase + dedupe + test-first rule | Hardened |
| §6.4 GATE_G | scheduled outcome review (§7 below) | Redesigned |
| §7 FDE layer | human role in `effect-matrix.yaml`; T3 two-person rule; credential broker | Hardened |
| §8 phase graph | supervisor workflow; release ends at GATE_F | Split from outcome review |
| §9 Keelgate | `dsh-secure-mesh` + `dsh-gatekeeper` | Single policy plane |
| §10 FastAPI/Postgres | the target application's standard, not the agent runtime | Scope clarified |
| §11 failure modes | plus F3, F6, F7, F12 from this review | Extended |
| §12 discipline | prompt/policy parity test | Made testable |
| §13 CI sequence | evidence producers sign records | Added signatures |
| §14 SLOs | metrics from gatekeeper store + session events | Adopted |
| §15 red-teaming | corpora in the eval harness | Adopted |
| §16 DoD | plus cost, guardrails, evidence integrity, eval coverage, tool pinning | Extended |
| §17 supervisor prompt | only rules that a hook enforces | Aligned |
| §18 sequence | reordered, 11 weeks (§9) | Reordered |
| §19 maturity | levels earned by evidence, not declared | Caveated |

### 5.1 Gate model v3.1

| Gate | When | Owner | Blocks | Statuses |
|---|---|---|---|---|
| A | per run, after spec | analyst | run | PASS / FAIL / BLOCKED / TIMED_OUT |
| B | per run, after design | architect + design verifier | run | PASS / FAIL / BLOCKED |
| C | per run, after build | supervisor | run | PASS / FAIL / BLOCKED |
| D | per run, after verification | verifier | run | PASS / FAIL / BLOCKED / TIMED_OUT |
| E | per production effect | human approver | effect | PASS / FAIL / BLOCKED |
| F | per deploy | operator | deploy completion | PASS / FAIL / ROLLBACK |
| **G** | **scheduled after release** | **FDE + product owner** | **rollout expansion only** | **PASS / ITERATE / ROLLBACK / INCONCLUSIVE** |
| R | per routing release | engineering lead | routing release | PASS / FAIL |
| M | per memory write | supervisor | write | PASS / BLOCKED |

Risk tiers T0–T3 decide which gates apply; the tier comes from the effect matrix, not the model.

### 5.2 The outcome loop (GATE_G, redesigned)

```text
release ──► GATE_F ──► RELEASED (run ends; checkpoints closed)
                          │
                          │ scheduled at contract.reviewDate
                          ▼
                   OutcomeReview  (separate process, not a parked run)
                     ├─ PASS          → expand rollout, archive contract
                     ├─ ITERATE       → new run + new contract version
                     ├─ ROLLBACK      → run the operator rollback runbook
                     └─ INCONCLUSIVE  → extend once, then decide
```

Rules:

- the contract is pre-registered and dual-signed **before** GATE_E; it is immutable after that;
- PASS requires the target delta, every guardrail within bounds, sufficient sample, and cost per outcome within the contract;
- INCONCLUSIVE is a real outcome and never converted to PASS;
- rollout expansion is the only thing G blocks; a verified release is never retroactively blocked;
- every iteration opens a new run with a new contract id, so attribution stays honest.

### 5.3 Memory and compaction contracts

**Memory.** Two stores with different rules: *facts* (immutable, gate-verified, provenance = evidence record id) and *procedures* (versioned like code, human-reviewed, never model-written without review). GATE_M checks provenance, conflict, ACL, and retention. On read, lessons are sanitized and may not contain instructions about permissions, gates, or approvals.

**Compaction.** Preserve verbatim: evidence ids and hashes, gate states, proposal ids and statuses, budgets, unresolved defects, tool versions. Summarize only narrative. Deterministic given the same input. A regression eval asserts that after any number of compactions, every gate decision remains reproducible.

### 5.4 Budget ledger

Reserve before dispatch, charge at each step from the harness measurement, release on completion; per-run and per-dispatch ceilings for iterations, tokens, wall clock, and cost; on exhaustion stop, checkpoint, and escalate — never throw. Price table per provider/model; weekly cost report by role and gate.

---

## 6. What to keep from v3.0, unchanged

The roster and contracts (§3), the phase graph shape (§8), the proposal record with idempotency key (§8.4), Keelgate's capability → policy → approval → audit order (§9.1), the tool classes READ/PROPOSE/WRITE (§9.1), anti-rubber-stamp (§9.4), the failure-mode table (§11), behavioural discipline (§12), the CI sequence (§13.1), red-teaming probes and cadence (§15), the DoD structure (§16), the supervisor prompt (§17), and the maturity vocabulary (§19). These are sound; they need seams and evidence, not replacement.

---

## 7. Plan delta: 11 weeks, reordered

| Phase | Weeks | Content | Exit criteria |
|---|---|---|---|
| **P0** | 1 | Repair v3.0; ADRs (substrate, control plane, roster, state); effect matrix; gate catalog v1.2; KPI contract schema | `check-doc` passes with required sections; every guarantee has a seam and a test |
| **P1** | 2 | `dsh-gatekeeper`: proposals, evidence registry, commit tokens, budget ledger, kill switch | §4.4 rows 3,4,7,8,9,10,13 pass; conformance vs `reference/agentkit` |
| **P2** | 2 | Eval harness, routing gold set, evidence adapters (CI, Semgrep, Playwright, coverage) | Golden tasks + routing baseline recorded; one signed record per kind |
| **P3** | 2 | Six role presets, tool compositions, worktrees, model routes | Capability-absence tests; verifier has no write tool; prompt/policy parity green |
| **P4** | 2 | End-to-end GATE_A–F on the pilot repository | Every PASS resolves to a record; a planted defect blocks at the right gate |
| **P5** | 2 | FDE handoff, KPI contract, first scheduled outcome review, two-person T3 | One contract pre-registered; one review completed with a decision |
| **P6** | 2 | Red-team corpora, SLO dashboards, production readiness | Injection/fabrication/bypass corpora at 0 PASS; SLOs live |

Total ~11 weeks, ~84 person-days (the earlier estimate stands; the ordering changes).

---

## 8. Document repair checklist (v3.0 → v3.1-doc)

1. Close the fence at line 71 and make §2.2–§20 real Markdown headings.
2. Delete the model meta-commentary at the tail (lines 883–895).
3. Add a `**Schema-Version:**` field to `TaskEnvelope`, `ActionProposal`, `FDEHandoff`, `BusinessKPIContract`, `EvidenceRecord`, with a compatibility rule.
4. Add a test/verification section: gate predicates, acceptance tests, and failure-injection cases.
5. Replace every `evidence_uri` with the evidence-record contract (URI remains a locator).
6. Rewrite GATE_G as a scheduled outcome review with INCONCLUSIVE.
7. Expand the KPI contract to the schema in `contracts/`.
8. Add the memory write gate and the facts/procedures split.
9. Add the T3 two-person rule and the credential broker.
10. Add the platform policy pack (security v2 §14) and bind it to GATE_D.
11. Add `tools/check-doc.mjs` to documentation CI with `--require "0.,1.,2.,3.,4.,5.,6.,7.,8.,9.,10.,11.,16.,18."`.

---

## 9. Decisions (accepted 2026-11-04)

> These decisions were accepted on 2026-11-04; see [`DECISIONS.md`](./DECISIONS.md). D2 is revised to a dedicated pilot repository (ADR-002); D3 becomes guardrails-not-approvals (ADR-003).

| # | Decision | Recommendation |
|---|---|---|
| D1 | Substrate | DSH-native; LangGraph only as an optional outer workflow |
| D2 | Pilot repository | One existing FastAPI + React repo, frozen for six weeks |
| D3 | Builder autonomy | Open PRs; humans merge; promote to a `dev` branch after four clean weeks |
| D4 | Model routes | Two providers (builder and verifier on different routes) |
| D5 | Hosting | Single VM for the pilot; managed Postgres when approvals must survive HA |
| D6 | Mandatory security checks | Token validation, BOLA, RLS, headers/CSP, parameterized SQL, SafeMarkdown, idempotency, readiness, audit grants |
| D7 | FDE identity and authority | One named human; two-person rule for T3; no chat-based approvals |
| D8 | KPI data source and ACL | Aggregated analytics only; read-only role; query ref recorded in the contract |
| D9 | Outcome window and decision rule | 4 weeks for adoption, 2 weeks for latency/error; INCONCLUSIVE extends once |
| D10 | Whether G blocks release | No; it blocks rollout expansion only |
| D11 | Whether LangGraph is required | Only if durable workflow state beyond DSH sessions is a hard requirement |

---

## Appendix A — Reproducing the document finding

```text
node tools/check-doc.mjs "<the v3.0 file>" --require "0.,1.,2.,3.,16.,18."
→ FAIL (7 errors): unclosed fence at line 71; 39 plain-text sections;
  meta-commentary at 884; implementation-ready claim without a test section;
  sections 3, 16, 18 not present as headings
```

The checker is part of this package and is meant to run in CI for every design document, including this one (it passes).

## Appendix B — Gate metrics adopted from v3.0 §6.2

`gate-catalog.yaml` v1.2 now carries a `metrics:` vector per gate and a `no_improvement` rule: no metric in the current gate's vector improved by more than 5% **and** at least one requirement is still failing → escalate. This is v3.0's §6.2 definition, made part of the catalogue rather than prose.