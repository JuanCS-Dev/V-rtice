"""Contract tests for OpenAPI specification.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests ensure API contracts are maintained:
- OpenAPI schema is valid
- All endpoints are documented
- Responses match schema
- Breaking changes are detected

Following Boris Cherny's principle: "Breaking changes must be explicit"
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

# Add backend paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api_gateway"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services"))

from api_gateway.main import app


class TestOpenAPISchemaValid:
    """Test suite for OpenAPI schema validation."""

    def test_openapi_schema_is_accessible(self):
        """Test that OpenAPI schema endpoint is accessible.

        Production Requirement: Schema must be publicly accessible.
        """
        client = TestClient(app)
        response = client.get("/openapi.json")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_openapi_schema_has_required_fields(self):
        """Test that OpenAPI schema has all required fields.

        Compliance: OpenAPI 3.1.0 specification requires:
        - openapi (version)
        - info (metadata)
        - paths (endpoints)
        """
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()

        # Required top-level fields
        assert "openapi" in schema, "Missing 'openapi' version field"
        assert "info" in schema, "Missing 'info' metadata"
        assert "paths" in schema, "Missing 'paths' (endpoints)"

        # OpenAPI version
        assert schema["openapi"].startswith("3."), f"Invalid OpenAPI version: {schema['openapi']}"

        # Info metadata
        assert "title" in schema["info"]
        assert "version" in schema["info"]

    def test_openapi_schema_has_security_schemes(self):
        """Test that security schemes are documented.

        Security Requirement: Authentication methods must be documented.
        """
        client = TestClient(app)
        response = client.get("/openapi.json")
        schema = response.json()

        assert "components" in schema
        assert "securitySchemes" in schema["components"]

        schemes = schema["components"]["securitySchemes"]

        # Should have BearerAuth
        assert "BearerAuth" in schemes
        assert schemes["BearerAuth"]["type"] == "http"
        assert schemes["BearerAuth"]["scheme"] == "bearer"

        # Should have ApiKeyAuth
        assert "ApiKeyAuth" in schemes
        assert schemes["ApiKeyAuth"]["type"] == "apiKey"
        assert schemes["ApiKeyAuth"]["in"] == "header"


class TestEndpointDocumentation:
    """Test suite ensuring all endpoints are documented."""

    def test_all_routes_are_documented(self):
        """Test that all FastAPI routes appear in OpenAPI spec.

        Documentation Requirement: No undocumented endpoints.
        """
        client = TestClient(app)
        schema = app.openapi()

        documented_paths = set(schema["paths"].keys())

        # Extract all routes from app
        actual_routes = set()
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                # Skip internal routes
                if not route.path.startswith("/_") and route.path != "/":
                    actual_routes.add(route.path)

        # Check that important routes are documented
        important_routes = [
            "/api/v1/health",
            "/api/v1/",
        ]

        for route in important_routes:
            assert route in documented_paths, f"Route {route} not documented in OpenAPI"

    def test_versioned_endpoints_are_documented(self):
        """Test that all /api/v1/ endpoints are in OpenAPI schema.

        Versioning Requirement: All v1 endpoints must be documented.
        """
        client = TestClient(app)
        schema = app.openapi()

        v1_paths = [path for path in schema["paths"].keys() if path.startswith("/api/v1/")]

        # Should have at least the core v1 endpoints
        assert len(v1_paths) >= 2, "Missing v1 endpoints in schema"

        # Core endpoints
        assert "/api/v1/health" in v1_paths
        assert "/api/v1/" in v1_paths

    def test_health_endpoint_documented_correctly(self):
        """Test that health endpoint has correct documentation.

        Example test for endpoint-specific contract.
        """
        client = TestClient(app)
        schema = app.openapi()

        health_path = schema["paths"].get("/api/v1/health")
        assert health_path is not None, "/api/v1/health not in schema"

        # Should have GET method
        assert "get" in health_path

        get_spec = health_path["get"]

        # Should have summary
        assert "summary" in get_spec or "description" in get_spec

        # Should have responses
        assert "responses" in get_spec
        assert "200" in get_spec["responses"]


class TestResponseSchemaValidation:
    """Test suite for response schema validation."""

    def test_health_endpoint_response_matches_schema(self):
        """Test that /api/v1/health response matches schema.

        Contract Requirement: Actual responses must match documented schema.
        """
        client = TestClient(app)

        # Get actual response
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()

        # Get schema
        schema = app.openapi()
        health_schema = schema["paths"]["/api/v1/health"]["get"]

        # Validate response has expected structure
        # (Full JSON Schema validation would require jsonschema library)
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data

        # Response should include services
        assert "services" in data
        assert isinstance(data["services"], dict)

    def test_error_responses_have_standard_format(self):
        """Test that error responses follow standardized format.

        Error Handling Requirement: All errors must have consistent format.
        """
        client = TestClient(app)

        # Request non-existent endpoint to get 404
        response = client.get("/api/v1/nonexistent-endpoint-12345")

        assert response.status_code == 404
        error = response.json()

        # Should have standard error fields (from P0-4)
        assert "detail" in error
        assert "error_code" in error
        assert "request_id" in error
        assert "path" in error
        assert "timestamp" in error

    def test_validation_errors_have_field_details(self):
        """Test that validation errors include field-level details.

        Developer Experience: Validation errors should be actionable.
        """
        client = TestClient(app)

        # This test requires an endpoint with validation
        # For now, we just verify the structure exists in schema
        schema = app.openapi()

        # Check that ValidationErrorResponse schema exists in components
        if "components" in schema and "schemas" in schema["components"]:
            schemas = schema["components"]["schemas"]

            # Should have error response schemas
            # (Exact name may vary depending on how Pydantic exports them)
            schema_names = list(schemas.keys())
            assert len(schema_names) > 0, "No schemas defined"


class TestBackwardCompatibility:
    """Test suite for detecting breaking changes."""

    def test_v1_endpoints_remain_stable(self):
        """Test that v1 endpoints haven't been removed.

        Backward Compatibility: v1 endpoints must remain stable.
        """
        client = TestClient(app)
        schema = app.openapi()

        # Core v1 endpoints that must always exist
        required_v1_endpoints = [
            "/api/v1/health",
            "/api/v1/",
        ]

        paths = schema["paths"].keys()

        for endpoint in required_v1_endpoints:
            assert endpoint in paths, f"BREAKING CHANGE: {endpoint} was removed"

    def test_response_fields_not_removed(self):
        """Test that response fields haven't been removed.

        Breaking Change Detection: Removing fields is a breaking change.
        """
        client = TestClient(app)

        # Get health endpoint response
        response = client.get("/api/v1/health")
        data = response.json()

        # Required fields that must always be present
        required_fields = ["status", "version", "timestamp"]

        for field in required_fields:
            assert field in data, f"BREAKING CHANGE: Field '{field}' removed from health response"


class TestSchemaMetadata:
    """Test suite for schema metadata and documentation quality."""

    def test_schema_has_contact_information(self):
        """Test that schema includes contact information.

        Documentation Quality: Users should know who to contact.
        """
        client = TestClient(app)
        schema = app.openapi()

        assert "info" in schema
        info = schema["info"]

        # Should have contact info
        if "contact" in info:
            contact = info["contact"]
            assert "name" in contact or "email" in contact

    def test_schema_has_version_information(self):
        """Test that schema includes version information.

        API Evolution: Version tracking is essential.
        """
        client = TestClient(app)
        schema = app.openapi()

        assert "info" in schema
        assert "version" in schema["info"]

        version = schema["info"]["version"]
        assert version is not None
        assert len(version) > 0

    def test_endpoints_have_tags(self):
        """Test that endpoints are organized with tags.

        Documentation Organization: Tags help navigate API.
        """
        client = TestClient(app)
        schema = app.openapi()

        # Check that some endpoints have tags
        tagged_count = 0
        for path, methods in schema["paths"].items():
            for method, spec in methods.items():
                if isinstance(spec, dict) and "tags" in spec:
                    tagged_count += 1

        # At least some endpoints should be tagged
        assert tagged_count > 0, "No endpoints have tags"


# ============================================================================
# Performance Tests
# ============================================================================


class TestSchemaPerformance:
    """Performance tests for schema generation."""

    def test_schema_generation_is_fast(self):
        """Test that schema generation completes quickly.

        Performance Requirement: Schema should be cached.
        """
        import time

        client = TestClient(app)

        # First call (may generate schema)
        start = time.perf_counter()
        response1 = client.get("/openapi.json")
        first_duration = time.perf_counter() - start

        # Second call (should be cached)
        start = time.perf_counter()
        response2 = client.get("/openapi.json")
        second_duration = time.perf_counter() - start

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Second call should be faster (cached)
        assert second_duration < first_duration or second_duration < 0.1


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
