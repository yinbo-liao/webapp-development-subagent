# Testing Standards

## Test Hierarchy
```
E2E (critical journeys)         ← ~10% of tests
   └── Integration (endpoint/feature)  ← ~30% of tests
       └── Unit (functions, components) ← ~60% of tests
```

## Naming Convention
```
test_<what>_<scenario>_<expected_result>
```

### Examples
```python
# Backend
def test_create_user_valid_input_returns_201()
def test_create_user_duplicate_email_returns_409()
def test_create_user_missing_password_returns_422()

# Frontend
describe('LoginForm', () => {
  it('submits valid credentials and redirects to dashboard')
  it('shows error message on invalid password')
  it('disables submit button while loading')
})
```

## Coverage Targets
| Layer | Line Coverage | Branch Coverage |
|-------|--------------|-----------------|
| Business logic (services) | 90% | 85% |
| API endpoints (routers) | 85% | 80% |
| UI components | 80% | 75% |
| Data access (repositories) | 85% | 80% |
| Utilities | 95% | 90% |

## Test Data
- Use factories/fixtures, never production data
- Reset database between integration test suites
- Mock external services in unit tests, use test doubles in integration

## CI Requirements
- All tests must pass before merge
- Coverage must not drop more than 2%
- Flaky tests are quarantined within 24 hours
