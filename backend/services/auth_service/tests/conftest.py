"""Pytest configuration and fixtures for auth_service tests.

This module sets up the test environment with proper configuration
for all tests, ensuring consistent and secure test execution.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
- No mocks for cryptographic operations (real bcrypt, real JWT)
- Real secret keys (but test-specific, not production)
- Proper environment isolation
"""

import os
import secrets
import sys
from typing import Generator

import pytest

# Add auth_service to path
sys.path.insert(0, "/home/juan/vertice-dev/backend/services/auth_service")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> Generator[None, None, None]:
    """Set up test environment with required configuration.

    This fixture runs automatically for all tests (autouse=True) and
    ensures that critical environment variables are set before any
    tests execute.

    Scope: session - runs once for entire test session
    Autouse: true - runs automatically without explicit request
    """
    # Generate a secure test-specific JWT secret
    # This is different from production but still cryptographically strong
    test_secret = secrets.token_hex(32)  # 64 characters (256 bits)

    # Set required environment variables for tests
    original_env = os.environ.copy()
    os.environ.update({
        "JWT_SECRET_KEY": test_secret,
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRATION_MINUTES": "30",
        "SERVICE_VERSION": "1.0.0-test",
        "LOG_LEVEL": "WARNING",  # Reduce noise in test output
    })

    yield  # Tests run here

    # Cleanup: restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="session")
def test_jwt_secret() -> str:
    """Provide the test JWT secret to tests that need it explicitly.

    Returns:
        str: The test JWT secret key (64 characters, cryptographically secure)
    """
    return os.environ["JWT_SECRET_KEY"]


@pytest.fixture(scope="session")
def weak_test_keys() -> list[str]:
    """Provide a list of known weak keys for negative testing.

    These keys should NEVER pass validation in production.

    Returns:
        list[str]: List of weak/default keys that should be rejected
    """
    return [
        "secret",
        "password",
        "your-super-secret-key",
        "change-me",
        "default",
        "test",
        "development",
    ]


@pytest.fixture
def generate_secure_key() -> callable:
    """Provide a function to generate secure keys for tests.

    Returns:
        callable: Function that generates cryptographically secure keys

    Example:
        def test_something(generate_secure_key):
            key = generate_secure_key(length=32)
            assert len(key) == 64  # hex encoding doubles length
    """
    def _generate(length: int = 32) -> str:
        """Generate a cryptographically secure random key.

        Args:
            length: Number of random bytes (default: 32 = 256 bits)

        Returns:
            str: Hex-encoded random key (length * 2 characters)
        """
        return secrets.token_hex(length)

    return _generate


@pytest.fixture
def isolated_environment(monkeypatch) -> dict[str, str]:
    """Provide an isolated environment for environment variable testing.

    This fixture clears all environment variables and provides a clean
    slate for tests that need to verify environment variable handling.

    Args:
        monkeypatch: pytest's monkeypatch fixture for env manipulation

    Returns:
        dict: Empty environment dict that can be populated by test

    Example:
        def test_env_loading(isolated_environment):
            isolated_environment["JWT_SECRET_KEY"] = "test-key"
            # Environment is now isolated with only JWT_SECRET_KEY set
    """
    # Clear all env vars for this test
    for key in list(os.environ.keys()):
        monkeypatch.delenv(key, raising=False)

    return {}


# ============================================================================
# Pytest configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings.

    Args:
        config: pytest configuration object
    """
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "security: mark test as a security-related test"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "performance: mark test as a performance test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically.

    Args:
        config: pytest configuration object
        items: list of collected test items
    """
    for item in items:
        # Auto-mark security tests
        if "security" in item.nodeid.lower() or "secret" in item.nodeid.lower():
            item.add_marker(pytest.mark.security)

        # Auto-mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        # Auto-mark performance tests
        if "performance" in item.nodeid.lower() or "benchmark" in item.fixturenames:
            item.add_marker(pytest.mark.performance)
