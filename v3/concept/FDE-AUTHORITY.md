# FDE Authority and Exception Policy

**Decision:** ADR-005 · **Status:** draft for signature

## 1. Accountable authority

One named **Forward Deployed Engineer (FDE)** is accountable for business scope, the KPI contract, exceptions, and adoption. Accountability is personal and cannot be delegated; tasks can.

## 2. Decision rights

| Decision | FDE | Product owner | Security | Release manager | Architecture board |
|---|---|---|---|---|---|
| Scope in/out for a pilot task | **A** | C | I | I | I |
| KPI contract (baseline, target, guardrails, window) | **A** | **A** (co-sign) | I | I | I |
| Exception to a gate or boundary | **A** (time-boxed) | I | **V** (veto) | I | I |
| Production deploy approval | **A** | I | C (T3) | **A** (merge) | I |
| Rollout expansion after GATE_G | **A** | C | I | I | I |
| Change to a control, gate, or policy | I | I | **A** | I | **A** |

**A** accountable · **C** consulted · **I** informed · **V** veto.

## 3. Non-waivable limits

The FDE cannot waive, shorten, or reinterpret:

1. a HIGH or CRITICAL security finding;
2. the T3 two-person approval (security or platform must be the second approver);
3. audit-chain integrity, evidence requirements, or the single-writer rule;
4. the prohibition on production data or credentials in the pilot;
5. the rule that no agent may write its own evidence or reset a revision counter.

A request to change any of the above is an architecture-board decision, not an exception.

## 4. Exception process

1. **Request**: what rule, why, blast radius, compensating control, expiry (≤ 14 days).
2. **Record**: exception id, requester, FDE decision, security veto check, review date.
3. **Enforce**: the gatekeeper reads the exception register; an expired exception is treated as absent.
4. **Review**: at expiry, close or extend once (maximum 28 days total); extensions require security sign-off.
5. **Report**: exceptions appear in the weekly pilot report and the audit trail.

An exception never disables a gate; it narrows a gate's scope for a named run and a named artifact.

## 5. Separation of duties

- The FDE may approve a production deployment, but never for a change the FDE authored or scoped alone at T3.
- The release manager is independent of the builder and of the FDE for the default-branch merge.
- The security reviewer's T3 approval is mandatory and cannot be delegated to the FDE.
- No approver may approve a proposal whose `argsHash` they did not see; approval is bound to bytes.

## 6. Continuity

A named backup FDE holds the same authority during absence (recorded in the exception register). If neither is available, expansion and T3 approvals block; the release may still proceed if GATE_E/F already passed and no exception is required.

## 7. Interface with the gatekeeper

- Every approval is a gatekeeper record: reviewer identity, proposal id, `argsHash`, checklist hash, timestamp.
- Chat messages, emails, and meeting notes are **not** approvals.
- The FDE's KPI signature is stored with the contract and cannot be edited after pre-registration.