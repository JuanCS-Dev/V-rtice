"""
Google OSINT Service - Targeted Coverage Tests

Objetivo: Cobrir main.py (126 lines, 0% → 95%+)

Testa FastAPI endpoints: health_check, query_osint with all search types
Direct function testing (no TestClient due to version incompatibility)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
Dedicado a Jesus Cristo - Honrando com Excelência Absoluta
"""

import pytest
from datetime import datetime
from fastapi import HTTPException


# ===== PYDANTIC MODEL TESTS =====

def test_osint_query_request_model():
    """
    SCENARIO: OsintQueryRequest created with all fields
    EXPECTED: Model validates and stores data correctly
    """
    from main import OsintQueryRequest

    request = OsintQueryRequest(
        query="APT29 malware",
        search_type="web",
        limit=20
    )

    assert request.query == "APT29 malware"
    assert request.search_type == "web"
    assert request.limit == 20


def test_osint_query_request_defaults():
    """
    SCENARIO: OsintQueryRequest with only required field
    EXPECTED: Defaults applied (search_type=web, limit=10)
    """
    from main import OsintQueryRequest

    request = OsintQueryRequest(query="ransomware")

    assert request.query == "ransomware"
    assert request.search_type == "web"  # Default
    assert request.limit == 10  # Default


def test_osint_query_request_custom_search_type():
    """
    SCENARIO: OsintQueryRequest with news search type
    EXPECTED: Custom search_type stored
    """
    from main import OsintQueryRequest

    request = OsintQueryRequest(
        query="zero-day exploit",
        search_type="news",
        limit=5
    )

    assert request.search_type == "news"
    assert request.limit == 5


# ===== FASTAPI APP TESTS =====

def test_fastapi_app_creation():
    """
    SCENARIO: FastAPI app instance created
    EXPECTED: App has correct title and version
    """
    from main import app

    assert app.title == "Maximus Google OSINT Service"
    assert app.version == "1.0.0"


# ===== HEALTH ENDPOINT TESTS (DIRECT) =====

@pytest.mark.asyncio
async def test_health_check_function():
    """
    SCENARIO: health_check() called directly
    EXPECTED: Returns healthy status dict
    """
    from main import health_check

    result = await health_check()

    assert result["status"] == "healthy"
    assert result["message"] == "Google OSINT Service is operational."


# ===== QUERY_OSINT ENDPOINT - WEB SEARCH =====

@pytest.mark.asyncio
async def test_query_osint_web_search():
    """
    SCENARIO: query_osint() with search_type=web
    EXPECTED: Returns web search results
    """
    from main import query_osint, OsintQueryRequest

    request = OsintQueryRequest(
        query="ransomware attack",
        search_type="web",
        limit=10
    )

    result = await query_osint(request)

    assert result["query"] == "ransomware attack"
    assert result["search_type"] == "web"
    assert "timestamp" in result
    assert "results" in result
    assert len(result["results"]) == 2  # Example returns 2 results
    assert result["results"][0]["title"] == "Example Web Result 1"
    assert "url" in result["results"][0]
    assert "snippet" in result["results"][0]


@pytest.mark.asyncio
async def test_query_osint_web_default_params():
    """
    SCENARIO: query_osint() with only query (defaults to web)
    EXPECTED: Returns web search results with defaults
    """
    from main import query_osint, OsintQueryRequest

    request = OsintQueryRequest(query="phishing campaign")

    result = await query_osint(request)

    assert result["search_type"] == "web"
    assert len(result["results"]) > 0


# ===== QUERY_OSINT ENDPOINT - NEWS SEARCH =====

@pytest.mark.asyncio
async def test_query_osint_news_search():
    """
    SCENARIO: query_osint() with search_type=news
    EXPECTED: Returns news search results
    """
    from main import query_osint, OsintQueryRequest

    request = OsintQueryRequest(
        query="cyberattack",
        search_type="news",
        limit=5
    )

    result = await query_osint(request)

    assert result["query"] == "cyberattack"
    assert result["search_type"] == "news"
    assert len(result["results"]) == 1
    assert result["results"][0]["title"] == "Breaking News: Cyberattack on Major Corp"
    assert "source" in result["results"][0]
    assert result["results"][0]["source"] == "News Outlet A"


# ===== QUERY_OSINT ENDPOINT - SOCIAL SEARCH =====

@pytest.mark.asyncio
async def test_query_osint_social_search():
    """
    SCENARIO: query_osint() with search_type=social
    EXPECTED: Returns social media search results
    """
    from main import query_osint, OsintQueryRequest

    request = OsintQueryRequest(
        query="APT group",
        search_type="social",
        limit=10
    )

    result = await query_osint(request)

    assert result["search_type"] == "social"
    assert len(result["results"]) == 1
    assert result["results"][0]["user"] == "@threat_analyst"
    assert result["results"][0]["platform"] == "X"
    assert "text" in result["results"][0]
    assert "timestamp" in result["results"][0]


# ===== QUERY_OSINT ENDPOINT - ERROR HANDLING =====

@pytest.mark.asyncio
async def test_query_osint_invalid_search_type():
    """
    SCENARIO: query_osint() with invalid search_type
    EXPECTED: Raises HTTPException with 400 status
    """
    from main import query_osint, OsintQueryRequest

    request = OsintQueryRequest(
        query="test",
        search_type="invalid",
        limit=10
    )

    with pytest.raises(HTTPException) as exc_info:
        await query_osint(request)

    assert exc_info.value.status_code == 400
    assert "Invalid search type" in exc_info.value.detail


# ===== QUERY_OSINT ENDPOINT - VARIOUS QUERIES =====

@pytest.mark.asyncio
async def test_query_osint_different_queries():
    """
    SCENARIO: Multiple queries with different search terms
    EXPECTED: All return results with correct query echoed back
    """
    from main import query_osint, OsintQueryRequest

    queries = [
        ("malware analysis", "web"),
        ("data breach", "news"),
        ("threat intel", "social"),
    ]

    for query_text, search_type in queries:
        request = OsintQueryRequest(
            query=query_text,
            search_type=search_type
        )
        result = await query_osint(request)

        assert result["query"] == query_text
        assert result["search_type"] == search_type
        assert len(result["results"]) > 0


# ===== TIMESTAMP TESTS =====

@pytest.mark.asyncio
async def test_query_osint_includes_timestamp():
    """
    SCENARIO: query_osint() result
    EXPECTED: Response includes valid ISO format timestamp
    """
    from main import query_osint, OsintQueryRequest

    request = OsintQueryRequest(
        query="test",
        search_type="web"
    )

    result = await query_osint(request)

    assert "timestamp" in result

    # Verify timestamp is valid ISO format
    try:
        datetime.fromisoformat(result["timestamp"])
    except ValueError:
        pytest.fail("Timestamp is not valid ISO format")


# ===== VALIDATION TESTS =====

def test_osint_query_request_validation_missing_query():
    """
    SCENARIO: OsintQueryRequest without required query field
    EXPECTED: Pydantic validation error
    """
    from main import OsintQueryRequest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        OsintQueryRequest(
            search_type="web",
            limit=10
            # Missing required 'query' field
        )


# ===== RESULT STRUCTURE TESTS =====

@pytest.mark.asyncio
async def test_query_osint_result_structure_web():
    """
    SCENARIO: query_osint() web search
    EXPECTED: Results have correct structure (title, url, snippet)
    """
    from main import query_osint, OsintQueryRequest

    request = OsintQueryRequest(
        query="test",
        search_type="web"
    )

    result = await query_osint(request)

    for item in result["results"]:
        assert "title" in item
        assert "url" in item
        assert "snippet" in item


@pytest.mark.asyncio
async def test_query_osint_result_structure_news():
    """
    SCENARIO: query_osint() news search
    EXPECTED: Results have correct structure (title, url, source)
    """
    from main import query_osint, OsintQueryRequest

    request = OsintQueryRequest(
        query="test",
        search_type="news"
    )

    result = await query_osint(request)

    for item in result["results"]:
        assert "title" in item
        assert "url" in item
        assert "source" in item


@pytest.mark.asyncio
async def test_query_osint_result_structure_social():
    """
    SCENARIO: query_osint() social search
    EXPECTED: Results have correct structure (user, platform, text, timestamp)
    """
    from main import query_osint, OsintQueryRequest

    request = OsintQueryRequest(
        query="test",
        search_type="social"
    )

    result = await query_osint(request)

    for item in result["results"]:
        assert "user" in item
        assert "platform" in item
        assert "text" in item
        assert "timestamp" in item


# ===== INTEGRATION TESTS =====

@pytest.mark.asyncio
async def test_complete_workflow_all_search_types():
    """
    SCENARIO: Complete workflow testing all search types
    EXPECTED: All endpoints work correctly
    """
    from main import query_osint, health_check, OsintQueryRequest

    # Health check
    health = await health_check()
    assert health["status"] == "healthy"

    # Web search
    web_request = OsintQueryRequest(
        query="malware",
        search_type="web"
    )
    web_response = await query_osint(web_request)
    assert web_response["search_type"] == "web"

    # News search
    news_request = OsintQueryRequest(
        query="breach",
        search_type="news"
    )
    news_response = await query_osint(news_request)
    assert news_response["search_type"] == "news"

    # Social search
    social_request = OsintQueryRequest(
        query="APT",
        search_type="social"
    )
    social_response = await query_osint(social_request)
    assert social_response["search_type"] == "social"


# ===== LIMIT PARAMETER TESTS =====

@pytest.mark.asyncio
async def test_query_osint_custom_limit():
    """
    SCENARIO: query_osint() with custom limit parameter
    EXPECTED: Limit parameter accepted (results may vary)
    """
    from main import query_osint, OsintQueryRequest

    request = OsintQueryRequest(
        query="test",
        search_type="web",
        limit=50
    )

    result = await query_osint(request)

    assert result is not None
    # Note: The example implementation returns fixed results
    # Real implementation would respect limit


# ===== EVENT HANDLER TESTS =====

@pytest.mark.asyncio
async def test_startup_event():
    """
    SCENARIO: startup_event() called
    EXPECTED: Executes without error (prints startup messages)
    """
    from main import startup_event

    # Should run without exceptions
    await startup_event()


@pytest.mark.asyncio
async def test_shutdown_event():
    """
    SCENARIO: shutdown_event() called
    EXPECTED: Executes without error (prints shutdown messages)
    """
    from main import shutdown_event

    # Should run without exceptions
    await shutdown_event()
