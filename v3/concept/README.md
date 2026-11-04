# Concept v3.1 — package index

The authoritative design for the full-stack engineer agent, updated from v3.0 and adapted to this repository.
Start with [CONCEPT.md](./CONCEPT.md); use [MIGRATION.md](./MIGRATION.md) to connect it to the Python v3
implementation in `../agents`, `../ecc_tools`, `../workflows`.

## Read in this order

| # | File | What it is |
|---|---|---|
| 1 | [CONCEPT.md](./CONCEPT.md) | The updated concept: four layers, roles, gates, evidence, guardrails, routing, business loop |
| 2 | [DECISIONS.md](./DECISIONS.md) | Seven accepted ADRs + one proposed bridge ADR (008) |
| 3 | [MIGRATION.md](./MIGRATION.md) | Agent/phase/ECC/config mapping and the M0–M4 migration plan |
| 4 | [effect-matrix.yaml](./effect-matrix.yaml) | Machine-readable autonomy: roles × effects, guardrails (v1.2) |
| 5 | [gate-catalog.yaml](./gate-catalog.yaml) | Gates A–G, R, M as deterministic predicates with metric vectors (v1.3) |
| 6 | [PILOT-REPO-CHARTER.md](./PILOT-REPO-CHARTER.md) | Dedicated pilot repository charter (ADR-002) |
| 7 | [FDE-AUTHORITY.md](./FDE-AUTHORITY.md) | Human accountability, exceptions, T3 separation (ADR-005) |
| 8 | [ASSESSMENT.md](./ASSESSMENT.md) | The full review of v3.0 that produced v3.1 (16 findings) |
| 9 | [REVIEW-AND-PLAN.md](./REVIEW-AND-PLAN.md) | Detailed target architecture, guarantee→seam→test map, 11-week plan |
| 10 | [policy/](./policy/) | `model-routing.yaml`, `kpi-sources.yaml`, generated `effect-matrix.json` |
| 11 | [contracts/](./contracts/) | `BusinessKPIContract` schema, example, zero-dependency validator |
| 12 | [gatekeeper/](./gatekeeper/README.md) | Reference implementation: policy, proposals, commit tokens; 15 tests |
| 13 | [tools/check-doc.mjs](./tools/check-doc.mjs) | Document-integrity checker (fences, headings, readiness claims) |

## Status

- Decisions ADR-001–ADR-007 accepted; ADR-008 (Python bridge) proposed.
- Reference core implemented and tested; the DSH plugin wiring, evidence registry and gate engine are P1.
- The Python v3 implementation is unchanged by this merge; migration starts at M0.

## Verification

```bash
node tools/check-doc.mjs CONCEPT.md
node contracts/validate-kpi.mjs contracts/example-kpi-contract.json
node gatekeeper/tests/run.mjs        # 15 passed
```

## Relationship to the repository

`v3/concept` is documentation and reference code. It does not alter the Python package, the CLI, or the
generated templates. `MIGRATION.md` is the bridge; ADR-001 is still the target.