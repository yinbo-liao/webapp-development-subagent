import pytest
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
    """Test password hashing and verification"""
    
    def test_password_hashing(self):
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False
    
    def test_password_hash_uniqueness(self):
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2

class TestJWTToken:
    """Test JWT token creation and verification"""
    
    def test_create_access_token(self):
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
    
    def test_token_expiration(self):
        data = {"sub": "test@example.com"}
        token = create_access_token(data, expires_delta=timedelta(minutes=1))
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload
    
    def test_verify_valid_token(self):
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        email = verify_token(token)
        assert email == "test@example.com"
    
    def test_verify_invalid_token(self):
        with pytest.raises(Exception):
            verify_token("invalid_token")

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_exceeded(self, client):
        for _ in range(101):
            response = client.get("/health")
        assert response.status_code == 429
