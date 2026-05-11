---
name: thinking-vault
description: Architecture decisions, MOCs (Maps of Content), and design rationale
section: 01_thinking
---

# 01 — Thinking Vault

## Purpose
This vault holds architectural decisions, design rationales, and Maps of Content (MOCs) that explain *why* the system works the way it does. Agents read this to understand context before making changes.

## Files
- `adr-*.md` — Architecture Decision Records (see template below)
- `moc-*.md` — Maps of Content linking related decisions
- `tech-debt.md` — Known technical debt and remediation plans

## ADR Template
```markdown
---
adr: <number>
status: proposed|accepted|deprecated|superseded
date: <YYYY-MM-DD>
deciders: [agent-names]
---

# ADR-<number>: <Title>

## Context
<What problem are we solving? What constraints exist?>

## Decision
<What did we choose and why?>

## Alternatives Considered
- **Option A**: <description> — Rejected because <reason>
- **Option B**: <description> — Rejected because <reason>

## Consequences
- Positive: <benefits>
- Negative: <trade-offs, risks>
```
