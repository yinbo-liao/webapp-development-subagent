# Security Learnings

## Purpose
Security-specific patterns, remediation templates, and vulnerability response playbooks.

## Contents
- `vulnerability-patterns.md` — Known vulnerability patterns and their fixes
- `remediation-templates.md` — Copy-paste remediation code for common vulns
- `incident-postmortems.md` — Security incident postmortems

## Quick Reference: Common Fixes

### SQL Injection → Parameterized Queries
```python
# BAD
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# GOOD
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### XSS → Output Encoding
```tsx
// BAD
<div>{userInput}</div>

// GOOD
<div>{sanitizeHTML(userInput)}</div>
// Or use React's built-in escaping: React escapes { } content by default
```

### Secrets in Code → Environment Variables
```python
# BAD
API_KEY = "sk-abc123"

# GOOD
API_KEY = os.environ["API_KEY"]
```
