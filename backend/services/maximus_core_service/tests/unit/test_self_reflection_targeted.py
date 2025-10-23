"""
Self-Reflection - Targeted Coverage Tests

Objetivo: Cobrir self_reflection.py (76 lines, 0% → 80%+)

Testa:
- SelfReflection initialization
- reflect_and_refine() error detection
- analyze_reasoning_path() efficiency scoring
- Async behavior

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest

from self_reflection import SelfReflection


# ===== INITIALIZATION =====

def test_self_reflection_initialization():
    """
    SCENARIO: Create SelfReflection instance
    EXPECTED: Initializes successfully
    """
    reflection = SelfReflection()

    assert reflection is not None


# ===== REFLECT AND REFINE TESTS =====

@pytest.mark.asyncio
async def test_reflect_and_refine_no_error():
    """
    SCENARIO: Reflect on response with no errors
    EXPECTED: Returns refined response with "No significant issues" note
    """
    reflection = SelfReflection()

    response = {"output": "Normal response"}
    context = {}

    refined = await reflection.reflect_and_refine(response, context)

    assert refined["output"] == "Normal response"
    assert "No significant issues" in refined["reflection_notes"]


@pytest.mark.asyncio
async def test_reflect_and_refine_with_error():
    """
    SCENARIO: Reflect on response containing "error"
    EXPECTED: Returns corrected response with error detected note
    """
    reflection = SelfReflection()

    response = {"output": "An error occurred"}
    context = {}

    refined = await reflection.reflect_and_refine(response, context)

    assert "error was detected" in refined["output"]
    assert "Identified potential error" in refined["reflection_notes"]


@pytest.mark.asyncio
async def test_reflect_and_refine_empty_output():
    """
    SCENARIO: Response with empty output
    EXPECTED: Handles gracefully
    """
    reflection = SelfReflection()

    response = {"output": ""}
    context = {}

    refined = await reflection.reflect_and_refine(response, context)

    assert "reflection_notes" in refined
    assert "No significant issues" in refined["reflection_notes"]


@pytest.mark.asyncio
async def test_reflect_and_refine_case_insensitive():
    """
    SCENARIO: Response with "ERROR" in uppercase
    EXPECTED: Detects error (case-insensitive)
    """
    reflection = SelfReflection()

    response = {"output": "An ERROR was found"}
    context = {}

    refined = await reflection.reflect_and_refine(response, context)

    assert "error was detected" in refined["output"]


@pytest.mark.asyncio
async def test_reflect_and_refine_returns_dict():
    """
    SCENARIO: Call reflect_and_refine()
    EXPECTED: Returns dict with output and reflection_notes
    """
    reflection = SelfReflection()

    response = {"output": "Test"}
    context = {}

    refined = await reflection.reflect_and_refine(response, context)

    assert isinstance(refined, dict)
    assert "output" in refined
    assert "reflection_notes" in refined


# ===== ANALYZE REASONING PATH TESTS =====

@pytest.mark.asyncio
async def test_analyze_reasoning_path_short():
    """
    SCENARIO: Analyze reasoning path with 3 steps
    EXPECTED: Efficiency score 0.9 (logical and efficient)
    """
    reflection = SelfReflection()

    reasoning_path = ["step1", "step2", "step3"]

    analysis = await reflection.analyze_reasoning_path(reasoning_path)

    assert analysis["efficiency_score"] == 0.9
    assert "logical and efficient" in analysis["analysis"]


@pytest.mark.asyncio
async def test_analyze_reasoning_path_long():
    """
    SCENARIO: Analyze reasoning path with > 5 steps
    EXPECTED: Efficiency score 0.7 (consider optimizing)
    """
    reflection = SelfReflection()

    reasoning_path = ["step1", "step2", "step3", "step4", "step5", "step6"]

    analysis = await reflection.analyze_reasoning_path(reasoning_path)

    assert analysis["efficiency_score"] == 0.7
    assert "consider optimizing" in analysis["analysis"]


@pytest.mark.asyncio
async def test_analyze_reasoning_path_exactly_five():
    """
    SCENARIO: Analyze reasoning path with exactly 5 steps
    EXPECTED: Efficiency score 0.9 (not considered "long")
    """
    reflection = SelfReflection()

    reasoning_path = ["step1", "step2", "step3", "step4", "step5"]

    analysis = await reflection.analyze_reasoning_path(reasoning_path)

    assert analysis["efficiency_score"] == 0.9


@pytest.mark.asyncio
async def test_analyze_reasoning_path_empty():
    """
    SCENARIO: Analyze empty reasoning path
    EXPECTED: Returns efficient score (len 0 is not > 5)
    """
    reflection = SelfReflection()

    reasoning_path = []

    analysis = await reflection.analyze_reasoning_path(reasoning_path)

    assert analysis["efficiency_score"] == 0.9


@pytest.mark.asyncio
async def test_analyze_reasoning_path_returns_dict():
    """
    SCENARIO: Call analyze_reasoning_path()
    EXPECTED: Returns dict with analysis and efficiency_score
    """
    reflection = SelfReflection()

    reasoning_path = ["step1", "step2"]

    analysis = await reflection.analyze_reasoning_path(reasoning_path)

    assert isinstance(analysis, dict)
    assert "analysis" in analysis
    assert "efficiency_score" in analysis


# ===== INTEGRATION TEST =====

@pytest.mark.asyncio
async def test_self_reflection_full_cycle():
    """
    SCENARIO: Full lifecycle (reflect + analyze)
    EXPECTED: Both methods work together
    """
    reflection = SelfReflection()

    # Reflect on response
    response = {"output": "Test response"}
    context = {}
    refined = await reflection.reflect_and_refine(response, context)

    assert refined is not None

    # Analyze reasoning
    reasoning_path = ["step1", "step2"]
    analysis = await reflection.analyze_reasoning_path(reasoning_path)

    assert analysis is not None
    assert analysis["efficiency_score"] > 0.0
