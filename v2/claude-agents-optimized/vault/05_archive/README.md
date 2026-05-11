# 05 — Archive Vault

## Purpose
Historical records: deprecated ADRs, retired features, old deployment logs, and completed project retrospectives. Nothing here is actively referenced by agents, but everything is preserved for audit and learning.

## Retention Policy
- **ADRs**: Keep indefinitely (superseded ADRs reference their replacement)
- **Feature specs**: Keep 1 year after deprecation
- **Deployment logs**: Keep 90 days
- **Test reports**: Keep 30 days
- **Retrospectives**: Keep indefinitely

## Archive Metadata
All archived files must include:
```yaml
---
archived: <YYYY-MM-DD>
reason: deprecated|superseded|retired|completed
superseded_by: <path-to-replacement>  # if applicable
---
```
