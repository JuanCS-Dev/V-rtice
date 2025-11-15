"""
Input Sanitizer Tests
=====================

Comprehensive test suite for input sanitization middleware.
Target: 100% coverage for security-critical code.

Boris Cherny Pattern: Security code must have exhaustive tests.
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from input_sanitizer import (
    InputSanitizationMiddleware,
    sanitize_string,
    sanitize_dict,
    sanitize_list,
    validate_and_sanitize,
    MAX_STRING_LENGTH,
    MAX_DEPTH,
)
from fastapi import HTTPException


# =============================================================================
# STRING SANITIZATION TESTS
# =============================================================================


class TestStringSanitization:
    """Test string sanitization."""

    def test_normal_string(self):
        """Normal strings pass through unchanged."""
        result = sanitize_string("Hello World")
        assert result == "Hello World"

    def test_sql_injection_select(self):
        """SQL SELECT injection is detected."""
        with pytest.raises(HTTPException) as exc:
            sanitize_string("'; SELECT * FROM users--")
        assert exc.value.status_code == 400
        assert "SQL" in exc.value.detail

    def test_sql_injection_union(self):
        """SQL UNION injection is detected."""
        with pytest.raises(HTTPException) as exc:
            sanitize_string("1' UNION SELECT password FROM users--")
        assert exc.value.status_code == 400

    def test_sql_injection_drop(self):
        """SQL DROP injection is detected."""
        with pytest.raises(HTTPException) as exc:
            sanitize_string("'; DROP TABLE users--")
        assert exc.value.status_code == 400

    def test_command_injection_pipe(self):
        """Command injection with pipe is detected."""
        with pytest.raises(HTTPException) as exc:
            sanitize_string("test | cat /etc/passwd")
        assert exc.value.status_code == 400
        assert "command" in exc.value.detail.lower()

    def test_command_injection_semicolon(self):
        """Command injection with semicolon is detected."""
        with pytest.raises(HTTPException) as exc:
            sanitize_string("test; rm -rf /")
        assert exc.value.status_code == 400

    def test_path_traversal(self):
        """Path traversal is detected."""
        with pytest.raises(HTTPException) as exc:
            sanitize_string("../../etc/passwd")
        assert exc.value.status_code == 400

    def test_null_byte_removal(self):
        """Null bytes are removed."""
        result = sanitize_string("test\x00null")
        assert "\x00" not in result
        assert result == "testnull"

    def test_whitespace_normalization(self):
        """Whitespace is normalized."""
        result = sanitize_string("test    multiple   spaces")
        assert result == "test multiple spaces"

    def test_max_length_exceeded(self):
        """Strings exceeding max length are rejected."""
        long_string = "a" * (MAX_STRING_LENGTH + 1)
        with pytest.raises(HTTPException) as exc:
            sanitize_string(long_string)
        assert exc.value.status_code == 400
        assert "too long" in exc.value.detail.lower()

    def test_empty_string(self):
        """Empty strings are allowed."""
        result = sanitize_string("")
        assert result == ""


# =============================================================================
# DICT SANITIZATION TESTS
# =============================================================================


class TestDictSanitization:
    """Test dictionary sanitization."""

    def test_simple_dict(self):
        """Simple dicts are sanitized."""
        data = {"name": "John", "age": 30}
        result = sanitize_dict(data)
        assert result == {"name": "John", "age": 30}

    def test_nested_dict(self):
        """Nested dicts are sanitized recursively."""
        data = {
            "user": {"name": "John", "address": {"city": "NYC"}},
        }
        result = sanitize_dict(data)
        assert result == data

    def test_dangerous_key_proto(self):
        """__proto__ key is rejected."""
        data = {"__proto__": "malicious"}
        with pytest.raises(HTTPException) as exc:
            sanitize_dict(data)
        assert exc.value.status_code == 400
        assert "Forbidden key" in exc.value.detail

    def test_dangerous_key_constructor(self):
        """constructor key is rejected."""
        data = {"constructor": "malicious"}
        with pytest.raises(HTTPException) as exc:
            sanitize_dict(data)
        assert exc.value.status_code == 400

    def test_max_depth_exceeded(self):
        """Deeply nested dicts are rejected."""
        # Create dict with depth > MAX_DEPTH
        data = {"level1": {}}
        current = data["level1"]
        for i in range(MAX_DEPTH + 1):
            current[f"level{i+2}"] = {}
            current = current[f"level{i+2}"]

        with pytest.raises(HTTPException) as exc:
            sanitize_dict(data)
        assert exc.value.status_code == 400
        assert "too deep" in exc.value.detail.lower()

    def test_sql_injection_in_value(self):
        """SQL injection in dict values is detected."""
        data = {"query": "'; DROP TABLE users--"}
        with pytest.raises(HTTPException) as exc:
            sanitize_dict(data)
        assert exc.value.status_code == 400


# =============================================================================
# LIST SANITIZATION TESTS
# =============================================================================


class TestListSanitization:
    """Test list sanitization."""

    def test_simple_list(self):
        """Simple lists are sanitized."""
        data = ["apple", "banana", "cherry"]
        result = sanitize_list(data)
        assert result == data

    def test_nested_list(self):
        """Nested lists are sanitized."""
        data = [1, [2, [3, [4]]]]
        result = sanitize_list(data)
        assert result == data

    def test_list_with_sql_injection(self):
        """SQL injection in lists is detected."""
        data = ["normal", "'; DROP TABLE users--"]
        with pytest.raises(HTTPException) as exc:
            sanitize_list(data)
        assert exc.value.status_code == 400

    def test_mixed_types_list(self):
        """Lists with mixed types are sanitized."""
        data = ["string", 123, True, None, {"key": "value"}]
        result = sanitize_list(data)
        assert len(result) == 5


# =============================================================================
# MIDDLEWARE INTEGRATION TESTS
# =============================================================================


class TestMiddlewareIntegration:
    """Test middleware in FastAPI application."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app with middleware."""
        app = FastAPI()
        app.add_middleware(InputSanitizationMiddleware)

        @app.post("/api/test")
        async def test_endpoint(request: Request):
            body = await request.json()
            return {"received": body}

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_normal_request(self, client):
        """Normal requests pass through."""
        response = client.post(
            "/api/test",
            json={"name": "John", "age": 30},
        )
        assert response.status_code == 200

    def test_sql_injection_blocked(self, client):
        """SQL injection attempts are blocked."""
        response = client.post(
            "/api/test",
            json={"query": "'; DROP TABLE users--"},
        )
        assert response.status_code == 400
        assert "SQL" in response.json()["detail"]

    def test_command_injection_blocked(self, client):
        """Command injection attempts are blocked."""
        response = client.post(
            "/api/test",
            json={"command": "test | cat /etc/passwd"},
        )
        assert response.status_code == 400
        assert "command" in response.json()["detail"].lower()

    def test_payload_too_large(self, client):
        """Large payloads are rejected."""
        large_data = {"data": "x" * (6 * 1024 * 1024)}  # 6MB
        response = client.post("/api/test", json=large_data)
        assert response.status_code == 413
        assert "too large" in response.json()["detail"].lower()

    def test_get_request_bypasses_sanitization(self, client):
        """GET requests bypass body sanitization."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_exempt_paths(self, client):
        """Exempt paths bypass sanitization."""
        response = client.get("/docs")
        # /docs might not exist but shouldn't crash
        assert response.status_code in [200, 404]

    def test_invalid_json(self, client):
        """Invalid JSON is rejected."""
        response = client.post(
            "/api/test",
            data="not valid json",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 400


# =============================================================================
# STANDALONE FUNCTION TESTS
# =============================================================================


class TestValidateAndSanitize:
    """Test standalone validation function."""

    def test_dict_validation(self):
        """Dict validation works."""
        data = {"name": "John", "age": 30}
        result = validate_and_sanitize(data)
        assert result == data

    def test_list_validation(self):
        """List validation works."""
        data = ["apple", "banana"]
        result = validate_and_sanitize(data)
        assert result == data

    def test_string_validation(self):
        """String validation works."""
        result = validate_and_sanitize("Hello World")
        assert result == "Hello World"

    def test_sql_injection_rejected(self):
        """SQL injection is rejected."""
        with pytest.raises(HTTPException):
            validate_and_sanitize("'; DROP TABLE users--")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
