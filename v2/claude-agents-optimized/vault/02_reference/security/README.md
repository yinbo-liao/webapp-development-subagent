# Security Reference

## OWASP Top 10 Mapping
See `owasp-mapping.yaml` for the full vulnerability-to-code-pattern mapping.

## Secrets Policy
1. **Never in code**: Secrets live in environment variables or a vault (HashiCorp Vault, GitHub Secrets, AWS Secrets Manager).
2. **Never in logs**: Secrets must be redacted from log output. Use structlog processors.
3. **Never in commits**: Pre-commit hooks scan for secret patterns. TruffleHog in CI.
4. **Rotation**: Secrets rotate every 90 days. Rotation scripts in `vault/06_system/`.

## Authentication
- **Session management**: HTTP-only, Secure, SameSite=Strict cookies
- **JWT**: RS256, 15-minute access tokens, 24-hour refresh tokens
- **Password policy**: Minimum 12 characters, not in HIBP breach database
- **MFA**: Required for all admin accounts

## API Security
- **Rate limiting**: 100 req/min per user, 1000 req/min per IP
- **CORS**: Explicit origin whitelist, no wildcard
- **Content Security Policy**: Strict CSP with no `unsafe-inline` (use nonces)
- **HTTPS only**: HSTS with 1-year max-age, includeSubDomains

## Dependency Security
```bash
# Python
pip-audit --strict

# Node.js
npm audit --production

# Check for known CVEs weekly
```
