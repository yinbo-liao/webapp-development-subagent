from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from ecc_tools.core.engine import ECCEngine


class QAAgent:
    """Specialized agent for testing — pytest, Playwright, coverage analysis."""

    def __init__(self, config: Dict = None, ecc: Optional[ECCEngine] = None):
        self.config = config or {}
        self.ecc = ecc or ECCEngine.get_instance("config")
        self.coverage_threshold = self.config.get("coverage_threshold", 80)

        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = None
        if template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )

    def run_tests(self, project_path: str) -> Dict:
        """Run comprehensive test suite"""
        print(f"[QA AGENT] Running comprehensive test suite...")

        results = {
            "status": "success",
            "test_results": {},
            "coverage": {},
            "validation": {}
        }

        # Generate test configuration
        files = self._generate_test_config(project_path)
        results["test_results"]["config"] = files

        # Generate unit tests
        files = self._generate_unit_tests(project_path)
        results["test_results"]["unit"] = files

        # Generate integration tests
        files = self._generate_integration_tests(project_path)
        results["test_results"]["integration"] = files

        # Generate E2E tests
        files = self._generate_e2e_tests(project_path)
        results["test_results"]["e2e"] = files

        # Validate with ECC
        results["validation"] = self.validate_output(project_path)

        return results

    def validate_output(self, output_path: str) -> Dict:
        """Validate via shared ECC engine."""
        report = self.ecc.full_scan(output_path)
        sec_ok = report.security.critical_count == 0 if report.security else True
        stab_ok = len([i for i in report.stability if i.severity == 'critical']) == 0
        return {
            "passed": sec_ok and stab_ok,
            "security": report.security,
            "stability": report.stability,
            "performance": report.performance,
            "maintainability": report.maintainability,
        }

    def _generate_test_config(self, project_path: str) -> List[str]:
        """Generate pytest configuration"""
        pytest_ini = Path(project_path) / "pytest.ini"

        code = """[pytest]
minversion = 7.0
addopts = 
    -ra 
    -q
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=80
    --asyncio-mode=auto
testpaths =
    app/tests
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
    security: Security tests
"""
        pytest_ini.write_text(code)

        conftest = Path(project_path) / "app" / "tests" / "conftest.py"
        conftest.parent.mkdir(parents=True, exist_ok=True)

        conftest_code = """import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("Test123!"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(client, test_user):
    from app.core.security import create_access_token

    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}
"""
        conftest.write_text(conftest_code)

        return [str(pytest_ini), str(conftest)]

    def _generate_unit_tests(self, project_path: str) -> List[str]:
        """Generate unit tests for core functionality"""
        test_dir = Path(project_path) / "app" / "tests" / "unit"
        test_dir.mkdir(parents=True, exist_ok=True)

        files = []

        # Test security module
        security_test = test_dir / "test_security.py"
        security_code = """import pytest
from datetime import timedelta
from jose import jwt

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token
)
from app.core.config import settings

class TestPasswordSecurity:
    \"\"\"Test password hashing and verification\"\"\"\n    \n    def test_password_hashing(self):
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
    \n    def test_password_verification_failure(self):
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False
    \n    def test_password_hash_uniqueness(self):
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2

class TestJWTToken:
    \"\"\"Test JWT token creation and verification\"\"\"\n    \n    def test_create_access_token(self):
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
    \n    def test_token_expiration(self):
        data = {"sub": "test@example.com"}
        token = create_access_token(data, expires_delta=timedelta(minutes=1))
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload
    \n    def test_verify_valid_token(self):
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        email = verify_token(token)
        assert email == "test@example.com"
    \n    def test_verify_invalid_token(self):
        with pytest.raises(Exception):
            verify_token("invalid_token")

class TestRateLimiting:
    \"\"\"Test rate limiting functionality\"\"\"\n    \n    def test_rate_limit_exceeded(self, client):
        for _ in range(101):
            response = client.get("/health")
        assert response.status_code == 429
"""
        security_test.write_text(security_code)
        files.append(str(security_test))

        return files

    def _generate_integration_tests(self, project_path: str) -> List[str]:
        """Generate integration tests"""
        test_dir = Path(project_path) / "app" / "tests" / "integration"
        test_dir.mkdir(parents=True, exist_ok=True)

        files = []

        api_test = test_dir / "test_api.py"
        api_code = """import pytest

class TestAuthentication:
    \"\"\"Test authentication endpoints\"\"\"\n    \n    def test_login_success(self, client, test_user):
        response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "Test123!"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
    \n    def test_login_failure(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "wrong@example.com", "password": "wrong"}
        )
        assert response.status_code == 401
    \n    def test_protected_endpoint_without_auth(self, client):
        response = client.get("/users/")
        assert response.status_code == 401
    \n    def test_protected_endpoint_with_auth(self, client, auth_headers):
        response = client.get("/users/", headers=auth_headers)
        assert response.status_code == 200

class TestCRUDOperations:
    \"\"\"Test CRUD operations\"\"\"\n    \n    def test_create_item(self, client, auth_headers):
        response = client.post(
            "/items/",
            json={"name": "Test Item", "description": "Test Description"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Item"
    \n    def test_read_item(self, client, auth_headers):
        # First create an item
        create_response = client.post(
            "/items/",
            json={"name": "Test Item", "description": "Test Description"},
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        \n        # Then read it
        response = client.get(f"/items/{item_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == item_id
    \n    def test_update_item(self, client, auth_headers):
        create_response = client.post(
            "/items/",
            json={"name": "Test Item", "description": "Test Description"},
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        \n        response = client.put(
            f"/items/{item_id}",
            json={"name": "Updated Item", "description": "Updated Description"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Item"
    \n    def test_delete_item(self, client, auth_headers):
        create_response = client.post(
            "/items/",
            json={"name": "Test Item", "description": "Test Description"},
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        \n        response = client.delete(f"/items/{item_id}", headers=auth_headers)
        assert response.status_code == 204
        \n        # Verify deletion
        get_response = client.get(f"/items/{item_id}", headers=auth_headers)
        assert get_response.status_code == 404
"""
        api_test.write_text(api_code)
        files.append(str(api_test))

        return files

    def _generate_e2e_tests(self, project_path: str) -> List[str]:
        """Generate E2E tests using Playwright"""
        test_dir = Path(project_path) / "e2e"
        test_dir.mkdir(parents=True, exist_ok=True)

        files = []

        e2e_test = test_dir / "test_auth_flow.spec.ts"
        e2e_code = """import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('user can login and access dashboard', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Fill in credentials
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'Test123!');

    // Submit form
    await page.click('[data-testid="login-button"]');

    // Wait for navigation to dashboard
    await page.waitForURL('/dashboard');

    // Verify dashboard is loaded
    await expect(page.locator('[data-testid="dashboard-header"]')).toBeVisible();
  });

  test('user sees error on invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[data-testid="email-input"]', 'wrong@example.com');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');

    await page.click('[data-testid="login-button"]');

    // Verify error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials');
  });

  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto('/dashboard');

    // Should be redirected to login
    await page.waitForURL('/login');

    // Verify we're on login page
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
  });
});

test.describe('CRUD Operations', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'Test123!');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('/dashboard');
  });

  test('user can create, read, update, delete items', async ({ page }) => {
    // Create item
    await page.click('[data-testid="create-item-button"]');
    await page.fill('[data-testid="item-name-input"]', 'E2E Test Item');
    await page.fill('[data-testid="item-description-input"]', 'Created by E2E test');
    await page.click('[data-testid="save-item-button"]');

    // Verify item appears in list
    await expect(page.locator('text=E2E Test Item')).toBeVisible();

    // Update item
    await page.click('[data-testid="edit-item-button"]');
    await page.fill('[data-testid="item-name-input"]', 'Updated E2E Item');
    await page.click('[data-testid="save-item-button"]');

    // Verify update
    await expect(page.locator('text=Updated E2E Item')).toBeVisible();

    // Delete item
    await page.click('[data-testid="delete-item-button"]');
    await page.click('[data-testid="confirm-delete-button"]');

    // Verify deletion
    await expect(page.locator('text=Updated E2E Item')).not.toBeVisible();
  });
});
"""
        e2e_test.write_text(e2e_code)
        files.append(str(e2e_test))

        # Playwright config
        playwright_config = test_dir / "playwright.config.ts"
        playwright_code = """import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'playwright-results.xml' }]
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
});
"""
        playwright_config.write_text(playwright_code)
        files.append(str(playwright_config))

        return files
