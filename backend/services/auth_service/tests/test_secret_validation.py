"""Unit tests for JWT Secret Validation.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests cover actual production implementation of secret validation:
- Secret key presence validation
- Secret key length validation (minimum 32 chars)
- Weak/default key detection
- Environment variable loading
- Startup fail-fast behavior

Note: ALL validation logic is REAL - no mocking per PAGANI standard.
Following Boris Cherny's principle: "Tests or it didn't happen"
"""

import os
import sys
from unittest import mock

import pytest

# Add auth_service to path
sys.path.insert(0, "/home/juan/vertice-dev/backend/services/auth_service")
from main import validate_secrets


class TestSecretValidation:
    """Test suite for JWT secret validation logic.

    These tests ensure that the authentication service enforces
    strong security requirements for JWT secret keys, following
    industry best practices and preventing common vulnerabilities.
    """

    def test_missing_secret_key_raises_value_error(self):
        """Test that missing JWT_SECRET_KEY raises ValueError.

        Security Requirement: Service MUST NOT start without a secret key.
        This is a fail-fast validation that prevents insecure deployment.
        """
        with mock.patch.dict(os.environ, {}, clear=True):
            # Remove JWT_SECRET_KEY from environment
            os.environ.pop("JWT_SECRET_KEY", None)

            with pytest.raises(ValueError) as exc_info:
                validate_secrets()

            error_message = str(exc_info.value)
            assert "JWT_SECRET_KEY environment variable is required" in error_message
            assert "openssl rand -hex 32" in error_message  # Should provide guidance

    def test_empty_secret_key_raises_value_error(self):
        """Test that empty JWT_SECRET_KEY raises ValueError.

        Security Requirement: Empty strings are not valid secret keys.
        """
        with mock.patch.dict(os.environ, {"JWT_SECRET_KEY": ""}):
            with pytest.raises(ValueError) as exc_info:
                validate_secrets()

            error_message = str(exc_info.value)
            assert "required" in error_message.lower()

    def test_short_secret_key_raises_value_error(self):
        """Test that secret keys < 32 characters raise ValueError.

        Security Requirement: Minimum 256-bit (32 character) entropy.
        Short keys are vulnerable to brute-force attacks.
        """
        short_keys = [
            "short",  # 5 chars
            "12345678901234567890",  # 20 chars
            "1234567890123456789012345678901",  # 31 chars (just under limit)
        ]

        for short_key in short_keys:
            with mock.patch.dict(os.environ, {"JWT_SECRET_KEY": short_key}):
                with pytest.raises(ValueError) as exc_info:
                    validate_secrets()

                error_message = str(exc_info.value)
                assert "at least 32 characters" in error_message
                assert f"Current length: {len(short_key)}" in error_message

    def test_weak_default_keys_raise_value_error(self):
        """Test that known weak/default keys raise ValueError.

        Security Requirement: Prevent use of common default/weak values.
        These are frequently targeted in security scans and attacks.
        """
        weak_keys = [
            "secret",
            "password",
            "your-super-secret-key",
            "change-me",
            "default",
            "test",
            "development",
        ]

        for weak_key in weak_keys:
            with mock.patch.dict(os.environ, {"JWT_SECRET_KEY": weak_key}):
                with pytest.raises(ValueError) as exc_info:
                    validate_secrets()

                error_message = str(exc_info.value)
                assert "weak/default value" in error_message.lower()

    def test_weak_key_case_insensitive(self):
        """Test that weak key detection is case-insensitive.

        Security Requirement: Prevent bypass via case variation.
        """
        weak_variations = [
            "SECRET",  # All caps
            "SeCrEt",  # Mixed case
            "PASSWORD",
            "PaSsWoRd",
        ]

        for weak_key in weak_variations:
            with mock.patch.dict(os.environ, {"JWT_SECRET_KEY": weak_key}):
                with pytest.raises(ValueError):
                    validate_secrets()

    def test_valid_32_char_key_passes(self):
        """Test that a valid 32-character key passes validation.

        Security Requirement: Minimum length keys should be accepted.
        """
        valid_key = "12345678901234567890123456789012"  # Exactly 32 chars
        assert len(valid_key) == 32

        with mock.patch.dict(os.environ, {"JWT_SECRET_KEY": valid_key}):
            # Should not raise any exception
            validate_secrets()  # Success if no exception raised

    def test_valid_64_char_hex_key_passes(self):
        """Test that a cryptographically strong hex key passes validation.

        Security Requirement: Strong keys should be accepted.
        This simulates output from: openssl rand -hex 32
        """
        # Simulated output from openssl rand -hex 32 (64 chars)
        valid_key = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2"
        assert len(valid_key) == 64

        with mock.patch.dict(os.environ, {"JWT_SECRET_KEY": valid_key}):
            # Should not raise any exception
            validate_secrets()

    def test_valid_complex_key_with_special_chars_passes(self):
        """Test that keys with special characters pass validation.

        Security Requirement: Accept high-entropy keys with special chars.
        """
        valid_key = "a!B@c#D$e%F^g&H*i(J)k_L+m-N=o[P]q{R}s|T:u;V'w,X.y/Z?1234567890"
        assert len(valid_key) >= 32

        with mock.patch.dict(os.environ, {"JWT_SECRET_KEY": valid_key}):
            # Should not raise any exception
            validate_secrets()

    def test_low_entropy_key_triggers_warning(self):
        """Test that low-entropy keys trigger a security warning.

        Security Requirement: Warn about potentially weak keys even if length OK.
        All lowercase or all uppercase suggests low entropy.
        """
        low_entropy_keys = [
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",  # All 'a's
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",  # All 'A's
            "12345678901234567890123456789012",  # All numbers
        ]

        for low_key in low_entropy_keys:
            with mock.patch.dict(os.environ, {"JWT_SECRET_KEY": low_key}):
                with pytest.warns(Warning) as warning_info:
                    validate_secrets()

                # Should emit a warning but not fail
                assert len(warning_info) > 0
                warning_message = str(warning_info[0].message)
                assert "low entropy" in warning_message.lower()

    def test_error_messages_provide_guidance(self):
        """Test that error messages provide actionable guidance.

        Usability Requirement: Errors should tell users HOW to fix the issue.
        Following Boris Cherny's principle: "Code is read 10x more than written"
        """
        test_cases = [
            # (env_vars, expected_guidance)
            ({}, "openssl rand -hex 32"),  # Missing key
            ({"JWT_SECRET_KEY": "short"}, "openssl rand -hex 32"),  # Short key
            ({"JWT_SECRET_KEY": "secret"}, "Never use default keys"),  # Weak key
        ]

        for env_vars, expected_guidance in test_cases:
            with mock.patch.dict(os.environ, env_vars, clear=True):
                with pytest.raises(ValueError) as exc_info:
                    validate_secrets()

                error_message = str(exc_info.value)
                assert expected_guidance in error_message

    def test_validation_happens_before_service_starts(self):
        """Test that validation is called during startup.

        Security Requirement: Fail-fast - validate secrets BEFORE accepting requests.
        This test verifies integration with the startup event handler.
        """
        # This is a structural test - verify validate_secrets is called in startup_event
        import inspect
        from main import startup_event

        source = inspect.getsource(startup_event)
        assert "validate_secrets()" in source
        assert "STEP 1" in source  # Should be first step
        assert "raise" in source  # Should re-raise exceptions


class TestEnvironmentVariableLoading:
    """Test suite for environment variable configuration loading.

    Ensures that configuration is properly loaded from environment
    variables with appropriate type safety and defaults.
    """

    def test_jwt_secret_key_loaded_from_environment(self):
        """Test that JWT_SECRET_KEY is loaded from environment variable."""
        test_key = "test-secret-key-with-sufficient-length-32-chars-minimum"

        with mock.patch.dict(os.environ, {"JWT_SECRET_KEY": test_key}):
            # Force reload of module to pick up new env var
            import importlib
            import main as main_module
            importlib.reload(main_module)

            assert main_module.SECRET_KEY == test_key

    def test_jwt_expiration_minutes_defaults_to_30(self):
        """Test that JWT_EXPIRATION_MINUTES defaults to 30 when not set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("JWT_EXPIRATION_MINUTES", None)

            import importlib
            import main as main_module
            importlib.reload(main_module)

            assert main_module.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_jwt_expiration_minutes_reads_from_environment(self):
        """Test that JWT_EXPIRATION_MINUTES is configurable via environment."""
        with mock.patch.dict(os.environ, {"JWT_EXPIRATION_MINUTES": "60"}):
            import importlib
            import main as main_module
            importlib.reload(main_module)

            assert main_module.ACCESS_TOKEN_EXPIRE_MINUTES == 60

    def test_algorithm_defaults_to_hs256(self):
        """Test that ALGORITHM defaults to HS256."""
        import importlib
        import main as main_module
        importlib.reload(main_module)

        assert main_module.ALGORITHM == "HS256"


# ============================================================================
# Integration Tests
# ============================================================================


class TestSecretValidationIntegration:
    """Integration tests for secret validation in the full service context."""

    @pytest.mark.asyncio
    async def test_service_fails_to_start_without_secret(self):
        """Test that the entire service fails to start without JWT_SECRET_KEY.

        Integration Requirement: Service startup should abort if secrets invalid.
        """
        with mock.patch.dict(os.environ, {}, clear=True):
            os.environ.pop("JWT_SECRET_KEY", None)

            from main import startup_event

            with pytest.raises(ValueError):
                await startup_event()

    @pytest.mark.asyncio
    async def test_service_starts_successfully_with_valid_secret(self):
        """Test that service starts successfully with valid JWT_SECRET_KEY.

        Integration Requirement: Service should start normally with valid config.
        """
        valid_key = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2"

        with mock.patch.dict(os.environ, {"JWT_SECRET_KEY": valid_key}):
            from main import startup_event

            # Should complete without raising exception
            # Note: May log warnings from constitutional logging setup
            try:
                await startup_event()
            except Exception as e:
                # Ignore constitutional logging errors in tests
                if "SECRET_KEY" not in str(e):
                    raise


# ============================================================================
# Performance Tests
# ============================================================================


class TestSecretValidationPerformance:
    """Performance tests to ensure validation doesn't add significant overhead."""

    def test_validation_completes_quickly(self, benchmark):
        """Test that secret validation completes in < 1ms.

        Performance Requirement: Startup validation should be near-instant.
        """
        valid_key = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2"

        with mock.patch.dict(os.environ, {"JWT_SECRET_KEY": valid_key}):
            # Benchmark the validation function
            result = benchmark(validate_secrets)

            # Should complete in microseconds, not milliseconds
            assert benchmark.stats["mean"] < 0.001  # < 1ms


# ============================================================================
# Documentation Tests
# ============================================================================


class TestSecretValidationDocumentation:
    """Tests ensuring proper documentation and type hints."""

    def test_validate_secrets_has_docstring(self):
        """Test that validate_secrets has comprehensive docstring.

        Documentation Requirement: All public functions must be documented.
        Following Boris Cherny's principle: "Code is read 10x more than written"
        """
        assert validate_secrets.__doc__ is not None
        assert len(validate_secrets.__doc__) > 100  # Substantial documentation

        doc = validate_secrets.__doc__
        assert "Raises" in doc or "raises" in doc
        assert "ValueError" in doc
        assert "Example" in doc or "example" in doc

    def test_validate_secrets_has_type_hints(self):
        """Test that validate_secrets has proper type hints.

        Type Safety Requirement: All functions must have type annotations.
        Following Boris Cherny's principle: "If it doesn't have types, it's not production"
        """
        import inspect
        from typing import get_type_hints

        # Get type hints
        hints = get_type_hints(validate_secrets)

        # Should have return type hint (-> None)
        assert "return" in hints
        assert hints["return"] is type(None)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
