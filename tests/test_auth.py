"""
Tests for authentication utilities.
"""

import pytest
from backend.auth.passwords import hash_password, verify_password
from backend.auth.api_keys import generate_api_key, hash_api_key
from backend.auth.jwt import create_access_token, create_refresh_token, decode_token, TokenError


class TestPasswords:
    def test_hash_and_verify(self):
        password = "secure_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_different_hashes(self):
        """Same password should produce different hashes (bcrypt salt)."""
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2


class TestAPIKeys:
    def test_generate_api_key(self):
        raw_key, key_hash, key_prefix = generate_api_key()
        assert raw_key.startswith("cb_")
        assert len(raw_key) > 20
        assert len(key_hash) == 64  # SHA-256 hex
        assert key_prefix == raw_key[:11]

    def test_hash_api_key(self):
        key = "cb_test_key_12345"
        h1 = hash_api_key(key)
        h2 = hash_api_key(key)
        assert h1 == h2  # deterministic

    def test_different_keys_different_hashes(self):
        _, h1, _ = generate_api_key()
        _, h2, _ = generate_api_key()
        assert h1 != h2


class TestJWT:
    def test_create_and_decode_access_token(self):
        token = create_access_token(
            subject="user-123",
            tenant_id="tenant-456",
        )
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["tenant_id"] == "tenant-456"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        token = create_refresh_token(
            subject="user-123",
            tenant_id="tenant-456",
        )
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_extra_claims(self):
        token = create_access_token(
            subject="user-123",
            tenant_id="tenant-456",
            extra_claims={"email": "test@example.com"},
        )
        payload = decode_token(token)
        assert payload["email"] == "test@example.com"

    def test_invalid_token(self):
        with pytest.raises(TokenError):
            decode_token("invalid.token.here")

    def test_tampered_token(self):
        token = create_access_token(subject="user", tenant_id="tenant")
        # Tamper with the token
        tampered = token[:-5] + "xxxxx"
        with pytest.raises(TokenError):
            decode_token(tampered)
