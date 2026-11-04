# Gatekeeper core (P1 slice)

Policy decisions, proposals and commit tokens for the DSH gatekeeper. Dependency-free
TypeScript, no DSH imports, so it can be tested and reviewed before it is wired into
`tools/pre-execute`, `ctx.tools.guard` and `ctx.approval`.

## What is implemented

| Module | Responsibility |
|---|---|
| `src/policy.ts` | Effect-matrix evaluation: AUTO / DRY_RUN / ASK / FORBIDDEN, kill switch, **guardrail verification that fails closed**, model-override detection (ADR-004) |
| `src/proposals.ts` | Proposal state machine: hash-bound args, intent hash, TTL, checklist acknowledgement, single use, verification, idempotent creation |
| `src/commit.ts` | HMAC commit token bound to `(proposalId, argsHash, intentHash, expiresAt)`; verify + consume exactly once |
| `src/index.ts` | Public surface + `loadMatrix()` for the generated JSON |

## Tests

```text
node gatekeeper/tests/run.mjs
→ 15 passed, 0 failed
```

Coverage: builder migration inside guardrails (allow) and without guardrail evidence (deny),
builder production deploy (deny), operator deploy (ask), kill switch (effects frozen, reads allowed),
unknown role/effect, human wildcard, model-override detection, idempotent proposals, stale-args
approval, missing checklist, single-use consume, intent mismatch, TTL expiry, rejected proposals,
token forgery, stale args at commit, double commit.

## Build

```text
Y:\DSH\dsh-secure-mesh\node_modules\.bin\tsc.cmd -p gatekeeper/tsconfig.json
```

The `typeRoots` entry points at the harness checkout's `@types/node`; replace it with a local
`node_modules` when the package is moved into a real workspace.

## Wiring (next)

```ts
// tools/pre-execute
const outcome = decide(matrix, role, effectOf(exec.name), {
  killSwitch: flags.killSwitch,
  guardrailsSatisfied: verifyGuardrails(exec, role, effectOf(exec.name)),
})
if (outcome.kind === 'deny') return { kind: 'deny', reason: `${outcome.code}: ${outcome.reason}` }
if (outcome.kind === 'ask') return { kind: 'ask', reason: outcome.reason }
return next()

// ctx.tools.guard: monotonic backstop for FORBIDDEN effects
// effect tool: require the commit token, recompute argsHash, call commitProposal()
```

## Limits of this slice

- In-memory store; persistence (SQLite/Postgres) is the next step.
- The matrix is loaded from generated JSON; the YAML remains the source and must be regenerated.
- No evidence registry or gate engine yet; those are the next P1 packages.
- No DSH dependency yet, so the seams are specified but not executed in a live harness.