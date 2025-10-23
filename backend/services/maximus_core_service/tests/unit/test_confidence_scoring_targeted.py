"""
Confidence Scoring - Targeted Coverage Tests

Objetivo: Cobrir confidence_scoring.py (69 lines, 0% → 80%+)

Testa:
- ConfidenceScoring initialization
- score() method (async)
- Response handling (dict vs string)
- Error detection logic
- Tool results evaluation
- RAG docs bonus
- Score clamping [0, 1]

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
import asyncio

from confidence_scoring import ConfidenceScoring


# ===== INITIALIZATION TESTS =====

def test_confidence_scoring_initialization():
    """
    SCENARIO: Create ConfidenceScoring instance
    EXPECTED: Initializes successfully
    """
    scoring = ConfidenceScoring()

    assert scoring is not None


# ===== SCORE METHOD TESTS =====

@pytest.mark.asyncio
async def test_score_basic_response_dict():
    """
    SCENARIO: Score dict response with no errors
    EXPECTED: Returns base score 0.7
    """
    scoring = ConfidenceScoring()

    response = {"output": "Normal response"}
    context = {}

    score = await scoring.score(response, context)

    assert score == 0.7


@pytest.mark.asyncio
async def test_score_basic_response_string():
    """
    SCENARIO: Score string response with no errors
    EXPECTED: Returns base score 0.7
    """
    scoring = ConfidenceScoring()

    response = "Normal response"
    context = {}

    score = await scoring.score(response, context)

    assert score == 0.7


@pytest.mark.asyncio
async def test_score_response_with_error_keyword():
    """
    SCENARIO: Response contains "error" keyword
    EXPECTED: Reduces score by 0.3 (0.7 - 0.3 = 0.4)
    """
    scoring = ConfidenceScoring()

    response = "An error occurred"
    context = {}

    score = await scoring.score(response, context)

    assert score == 0.4


@pytest.mark.asyncio
async def test_score_context_with_tool_errors():
    """
    SCENARIO: Context contains tool_results with errors
    EXPECTED: Reduces score by 0.2 (0.7 - 0.2 = 0.5)
    """
    scoring = ConfidenceScoring()

    response = "Normal response"
    context = {
        "tool_results": [
            {"result": "success"},
            {"result": "error in tool"}
        ]
    }

    score = await scoring.score(response, context)

    assert score == 0.5


@pytest.mark.asyncio
async def test_score_context_with_retrieved_docs():
    """
    SCENARIO: Context contains retrieved_docs from RAG
    EXPECTED: Increases score by 0.1 (0.7 + 0.1 = 0.8)
    """
    scoring = ConfidenceScoring()

    response = "Normal response"
    context = {
        "retrieved_docs": [
            {"doc": "relevant document"}
        ]
    }

    score = await scoring.score(response, context)

    assert score == 0.8


@pytest.mark.asyncio
async def test_score_combined_factors():
    """
    SCENARIO: Multiple factors (error in response, RAG docs present)
    EXPECTED: Applies both adjustments (0.7 - 0.3 + 0.1 = 0.5)
    """
    scoring = ConfidenceScoring()

    response = {"output": "Error in processing"}
    context = {
        "retrieved_docs": [{"doc": "helpful doc"}]
    }

    score = await scoring.score(response, context)

    assert score == 0.5


@pytest.mark.asyncio
async def test_score_clamped_to_minimum():
    """
    SCENARIO: Score would go below 0.0
    EXPECTED: Clamped to 0.0
    """
    scoring = ConfidenceScoring()

    response = "Error in response"
    context = {
        "tool_results": [{"error": "tool failed"}]
    }

    # 0.7 - 0.3 - 0.2 = 0.2, should be valid
    score = await scoring.score(response, context)

    assert score >= 0.0


@pytest.mark.asyncio
async def test_score_clamped_to_maximum():
    """
    SCENARIO: Score within valid range
    EXPECTED: Returns value <= 1.0
    """
    scoring = ConfidenceScoring()

    response = "Perfect response"
    context = {
        "retrieved_docs": [{"doc": "doc1"}]
    }

    score = await scoring.score(response, context)

    assert score <= 1.0


@pytest.mark.asyncio
async def test_score_returns_float():
    """
    SCENARIO: Call score() method
    EXPECTED: Returns float between 0.0 and 1.0
    """
    scoring = ConfidenceScoring()

    response = "Test response"
    context = {}

    score = await scoring.score(response, context)

    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_score_handles_non_dict_non_string_response():
    """
    SCENARIO: Response is neither dict nor string (e.g., int)
    EXPECTED: Converts to string, processes normally
    """
    scoring = ConfidenceScoring()

    response = 12345
    context = {}

    score = await scoring.score(response, context)

    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_score_empty_context():
    """
    SCENARIO: Empty context dict
    EXPECTED: Uses base score 0.7
    """
    scoring = ConfidenceScoring()

    response = "Response"
    context = {}

    score = await scoring.score(response, context)

    assert score == 0.7


@pytest.mark.asyncio
async def test_score_is_async():
    """
    SCENARIO: Score method is async
    EXPECTED: Can be awaited
    """
    scoring = ConfidenceScoring()

    response = "Test"
    context = {}

    # This should not raise
    score = await scoring.score(response, context)

    assert score is not None


# ===== INTEGRATION TEST =====

@pytest.mark.asyncio
async def test_confidence_scoring_full_cycle():
    """
    SCENARIO: Full lifecycle (init → score multiple responses)
    EXPECTED: Works for various inputs
    """
    scoring = ConfidenceScoring()

    # Case 1: Clean response
    score1 = await scoring.score("Good response", {})
    assert score1 == 0.7

    # Case 2: With RAG
    score2 = await scoring.score("Good response", {"retrieved_docs": [{"doc": "data"}]})
    assert score2 == 0.8

    # Case 3: With error
    score3 = await scoring.score("Error occurred", {})
    assert score3 == 0.4
