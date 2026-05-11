# 04 — Published Vault

## Purpose
Final, approved documentation. This is the source of truth for shipped features, API docs, and user-facing documentation.

## Contents
- `api-docs/` — Generated OpenAPI/Swagger documentation
- `feature-docs/` — Shipped feature documentation
- `test-reports/` — Latest test execution reports
- `deployment-logs/` — Deployment history and changelogs
- `changelog.md` — Human-readable changelog

## Publishing Rules
1. Feature specs move from `vault/03_creating/` → `vault/04_published/feature-docs/` on ship.
2. API docs are regenerated on every deployment from the OpenAPI spec.
3. Test reports are archived here after every CI run on main.
4. Never edit published docs directly — fix the source and re-publish.
