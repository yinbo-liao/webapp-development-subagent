# Decision Record — Full-Stack Engineer Agent Platform

**Date:** 2026-11-04 · **Status:** accepted (project direction)
**Supersedes:** the open decisions D1–D11 in `REVIEW-AND-PLAN.md` §8 and `V3-REVIEW-AND-PROPOSAL.md` §9.

These seven decisions fix the substrate, the pilot boundary, the autonomy model, model routing, business authority, the KPI source of truth, and the scope of the business gate. Each is recorded as an ADR: context, decision, consequences, follow-ups. Anything not decided here remains a P0 task.

---

## ADR-001 — Substrate: DSH-native

**Context.** v3.0 names LangGraph + Keelgate + PostgreSQL. The workspace already has a tested DSH + `dsh-secure-mesh` stack (31 tests, real Cordis integration, hash-chained audit). Two policy planes guarantee one is bypassed.

**Decision.** DSH is the orchestration and enforcement substrate. `dsh-secure-mesh` keeps egress, tool denial, approvals, fencing and audit; a new `dsh-gatekeeper` plugin adds proposals, evidence, gates, budgets and the kill switch. LangGraph is permitted **only** as an outer durable workflow that calls DSH agents as workers, and only if a compelling interoperability requirement exists (for example, an organisation-owned Temporal/LangGraph estate with durable timers that another team operates). Even then it owns no policy and no audit chain.

**Consequences.**
- One policy plane, one evidence store, one audit chain.
- The `reference/agentkit` Python modules remain the executable oracle for the TypeScript port (same inputs → same decisions).
- No OPA/Rego in the pilot; policy is TypeScript in the gatekeeper, versioned in `policy/*.yaml`.
- The LangGraph exception is a decision of the architecture board, not of a subagent.

**Follow-ups.** Pin harness versions; record the DSH version in every evidence record; revisit only on a written interop requirement.

---

## ADR-002 — Pilot repository: dedicated, not production

**Context.** Using a production repository for the pilot couples agent mistakes to live customers and makes "success" ambiguous.

**Decision.** Create a dedicated pilot repository that mirrors the target stack (FastAPI + PostgreSQL + Vite/React) with **synthetic data only**, no production credentials, and no production network path. It has clear ownership, branch protection, required checks, and written success criteria (charter: `PILOT-REPO-CHARTER.md`).

**Consequences.**
- The pilot can fail safely; production access is out of scope.
- The security policy pack runs against the pilot from day one.
- Success is measured on the pilot's seeded backlog and gates, not on production incident absence.
- Migration to a real repository is a later, separately gated programme.

**Follow-ups.** Name the repository owner (platform team) and the business owner (FDE); seed the three-task backlog; enable branch protection and required checks before the first agent run.

---

## ADR-003 — Builder autonomy: guardrails, not approvals

**Context.** Per-action human approval for every builder action creates approval fatigue and rubber-stamping, and slows the loop without improving safety. What actually constrains a builder is the boundary it cannot cross.

**Decision.** Builders are autonomous inside explicit boundaries. The gatekeeper enforces the boundary as **deny**, not as a prompt for permission. Approval is reserved for effects that cross a trust boundary (production deployment, IAM, destructive data operations), and those belong to the operator/approver roles, not the builder.

Boundaries (all machine-checked):

| Boundary | Enforcement | Evidence |
|---|---|---|
| Repository scope | worktree + path allowlist in the fs sandbox | diff manifest |
| Branch scope | feature branches; integration merge only after GATE_C/D | merge record |
| Dependencies | allowlist + lockfile + license check + registry proxy | SBOM + dependency scan |
| Secrets | no repository secrets; no production credentials in the builder preset | secret scan |
| Network | registry proxy only; `secure_fetch` allowlist for docs | egress audit |
| Security | stack policy pack checks at GATE_D | scan + test evidence |
| Budget | per-dispatch tokens/cost/wall clock | ledger |

**Consequences.**
- The policy's default answer to an out-of-boundary tool call is `deny`, not `ask`.
- The builder may write a migration file but may never apply one outside the ephemeral environment.
- Autonomy does not bypass gates: GATE_C/D still require evidence, and T3 changes still require the T3 gate set.
- "The agent was allowed to" and "the agent was correct" remain separate facts.

**Follow-ups.** Encode the boundaries in `effect-matrix.yaml` (v1.2) and in the builder preset; test each boundary with a negative case (attempt → deny + audit).

---

## ADR-004 — Model routing: explicit rules, no ad hoc selection

**Context.** Letting each agent choose a model (or a prompt pick one) makes cost, latency, quality, and independence unpredictable, and makes evaluations incomparable.

**Decision.** A single routing policy (`policy/model-routing.yaml`) maps **role + risk tier** to a route class, with a primary and an ordered fallback chain, cost ceilings, and an independence invariant: the verifier must never share a provider with the builder, and must **block** rather than fall back to the builder's provider. No tool argument may select a model. The resolved route is recorded in evidence and is part of the run's comparability key.

**Consequences.**
- Cost and latency are managed per role class, not per call.
- Routing changes require GATE_R (offline routing evaluation) and a recorded decision.
- A provider outage degrades to a declared fallback; if the fallback violates independence, the run blocks with `PROVIDER_INDEPENDENCE_UNAVAILABLE`.
- Evaluations are comparable only within the same route and tool versions.

**Follow-ups.** Fill the candidate table for the deployment; record cost per success per route; review routing monthly.

---

## ADR-005 — FDE: one accountable authority

**Context.** Business scope, KPI interpretation, exceptions, and adoption decisions need a single owner; ambiguity produces disputes and quiet scope changes.

**Decision.** One named **FDE** is the accountable authority for business scope, the KPI contract, exceptions, and adoption. The FDE cannot delegate accountability, only tasks. The authority is bounded by four non-waivable items: security findings, the T3 two-person approval, audit integrity, and evidence requirements.

**Consequences.**
- One throat to choke for business decisions; one signature on the KPI contract.
- Exceptions are time-boxed (≤ 14 days), logged, carry a compensating control, and are reviewed at expiry.
- The FDE may approve production deployment, but for T3 effects a second approver from security/platform is mandatory and may not be the FDE.
- The FDE cannot approve a change that removes a control or weakens a gate; that requires the architecture board.

**Follow-ups.** Name the FDE; publish the exception register; add the T3 rule to GATE_E_TWO_APPROVERS.

---

## ADR-006 — KPI source of truth: one authoritative source

**Context.** Business outcomes are contested when different dashboards compute the same KPI differently.

**Decision.** Each KPI contract names exactly one **authoritative source** from a registry. Telemetry collects events; the warehouse/BI layer computes the KPI; operational systems supply guardrails. The contract records `sourceId`, `queryRef`, `acl`, `refreshSla`, and `owner`. Disputes are resolved by the source owner, not by the agent.

**Consequences.**
- One number per KPI, one owner, one query.
- Agent access is read-only, aggregated, and ACL-filtered; row-level data never enters the contract.
- A missing or stale source makes the review `INCONCLUSIVE`, never `PASS`.
- Changing the source requires a new contract version.

**Follow-ups.** Publish `policy/kpi-sources.yaml`; select the pilot source; verify refresh SLA and ACL before the first contract is signed.

---

## ADR-007 — GATE_G scope: block expansion, not release

**Context.** Business KPIs lag releases by weeks and are noisy. Blocking a verified release on a lagging metric would either freeze delivery or invite metric gaming.

**Decision.** GATE_F ends the release. GATE_G is a scheduled **outcome review** that can PASS, ITERATE, ROLLBACK, or be INCONCLUSIVE. It blocks **rollout expansion** (wider cohort, customer, or feature exposure) and never retroactively blocks a release that passed GATE_E/F. Each iteration opens a new run with a new contract id.

**Consequences.**
- No run is parked for the measurement window.
- INCONCLUSIVE is honest and has a decision rule (extend once, then decide).
- Rollout expansion is the lever that keeps business accountability without holding delivery hostage.
- A rollback decision is executed by the operator through the rollback runbook, under GATE_E.

**Follow-ups.** Encode `release_blocking: false` / `expansion_blocking: true` in the gate catalogue; define expansion cohorts per feature; drill the rollback path.

---

## Open items (not decided here)

| # | Item | Needed by |
|---|---|---|
| O1 | Pilot repository URL and owner | P0 |
| O2 | FDE name and delegated approver | P0 |
| O3 | KPI source system and owner | P0 |
| O4 | Provider/model candidates per route class | P1 |
| O5 | Expansion cohort definition for the pilot feature | P5 |
---

## ADR-008 (proposed) — Python bridge while DSH composition is built

**Context.** The repository's running implementation is Python (agents, ECC, workflows). ADR-001 makes DSH
the target substrate, but the DSH composition does not exist yet. Rewriting the orchestrator before the
gates exist would repeat the v1.0 mistake: claims of enforcement with no executable seam.

**Decision (proposed).** Keep the Python system runnable and wrap it with a Python gatekeeper that
implements the same contracts as the TypeScript reference core (`gatekeeper/`): effect decisions,
hash-bound proposals, commit tokens, evidence records, gate evaluation, budget, kill switch. The TypeScript
core is the conformance oracle; shared fixtures must produce identical decisions and error codes. The DSH
composition replaces the bridge role by role, not in a flag day.

**Consequences.**
- Two runtimes temporarily, with one set of contracts and one decision record per semantic change.
- M0–M4 in `MIGRATION.md` are independently useful; M2 (ECC evidence + GATE_D) delivers value even if later
  phases slip.
- No new policy may exist only in Python; the concept and the TypeScript core are updated first.

**Status:** proposed — needs acceptance before M1 starts.
