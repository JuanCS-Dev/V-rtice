"""
Suggestion Generator - Targeted Coverage Tests

Objetivo: Cobrir suggestion_generator.py (27 lines, 0% → 100%)

Testa SuggestionGenerator: generate_suggestions, get_status, priority logic

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from suggestion_generator import SuggestionGenerator
from datetime import datetime


# ===== INITIALIZATION TESTS =====

def test_suggestion_generator_initialization():
    """
    SCENARIO: SuggestionGenerator created
    EXPECTED: Default attributes set
    """
    generator = SuggestionGenerator()

    assert generator.generated_suggestions == []
    assert generator.last_generation_time is None
    assert generator.current_status == "ready_to_suggest"


# ===== GENERATE_SUGGESTIONS - THREAT DETECTION =====

@pytest.mark.asyncio
async def test_generate_suggestions_threat_detection_high_confidence():
    """
    SCENARIO: generate_suggestions() with threat_detection, confidence > 0.7
    EXPECTED: Returns security_alert and investigation suggestions
    """
    generator = SuggestionGenerator()
    analysis = {
        "prediction_type": "threat_detection",
        "predicted_event": "SQL injection attempt",
        "confidence": 0.85
    }

    suggestions = await generator.generate_suggestions(analysis)

    assert len(suggestions) == 2
    assert suggestions[0]["type"] == "security_alert"
    assert suggestions[0]["priority"] == "critical"
    assert "SQL injection attempt" in suggestions[0]["description"]
    assert suggestions[1]["type"] == "investigation"
    assert suggestions[1]["priority"] == "high"


@pytest.mark.asyncio
async def test_generate_suggestions_threat_detection_low_confidence():
    """
    SCENARIO: generate_suggestions() with threat_detection, confidence ≤ 0.7
    EXPECTED: Returns monitor_closely suggestion (fallback)
    """
    generator = SuggestionGenerator()
    analysis = {
        "prediction_type": "threat_detection",
        "predicted_event": "potential attack",
        "confidence": 0.6
    }

    suggestions = await generator.generate_suggestions(analysis)

    assert len(suggestions) == 1
    assert suggestions[0]["type"] == "monitor_closely"
    assert suggestions[0]["priority"] == "low"


# ===== GENERATE_SUGGESTIONS - RESOURCE OPTIMIZATION =====

@pytest.mark.asyncio
async def test_generate_suggestions_resource_optimization_high_confidence():
    """
    SCENARIO: generate_suggestions() with resource_optimization, confidence > 0.6
    EXPECTED: Returns scale_up and optimize_database suggestions
    """
    generator = SuggestionGenerator()
    analysis = {
        "prediction_type": "resource_optimization",
        "predicted_event": "high load expected",
        "confidence": 0.75
    }

    suggestions = await generator.generate_suggestions(analysis)

    assert len(suggestions) == 2
    assert suggestions[0]["type"] == "scale_up"
    assert suggestions[0]["priority"] == "medium"
    assert "20%" in suggestions[0]["description"]
    assert suggestions[1]["type"] == "optimize_database"
    assert suggestions[1]["priority"] == "low"


@pytest.mark.asyncio
async def test_generate_suggestions_resource_optimization_low_confidence():
    """
    SCENARIO: generate_suggestions() with resource_optimization, confidence ≤ 0.6
    EXPECTED: Returns monitor_closely suggestion (fallback)
    """
    generator = SuggestionGenerator()
    analysis = {
        "prediction_type": "resource_optimization",
        "predicted_event": "possible load increase",
        "confidence": 0.5
    }

    suggestions = await generator.generate_suggestions(analysis)

    assert len(suggestions) == 1
    assert suggestions[0]["type"] == "monitor_closely"


# ===== GENERATE_SUGGESTIONS - UNKNOWN/OTHER TYPES =====

@pytest.mark.asyncio
async def test_generate_suggestions_unknown_type():
    """
    SCENARIO: generate_suggestions() with unknown prediction_type
    EXPECTED: Returns monitor_closely suggestion (fallback)
    """
    generator = SuggestionGenerator()
    analysis = {
        "prediction_type": "unknown_type",
        "predicted_event": "something",
        "confidence": 0.9
    }

    suggestions = await generator.generate_suggestions(analysis)

    assert len(suggestions) == 1
    assert suggestions[0]["type"] == "monitor_closely"
    assert suggestions[0]["priority"] == "low"


@pytest.mark.asyncio
async def test_generate_suggestions_missing_prediction_type():
    """
    SCENARIO: generate_suggestions() with missing prediction_type
    EXPECTED: Returns monitor_closely suggestion (fallback)
    """
    generator = SuggestionGenerator()
    analysis = {
        "predicted_event": "event",
        "confidence": 0.8
    }

    suggestions = await generator.generate_suggestions(analysis)

    assert len(suggestions) == 1
    assert suggestions[0]["type"] == "monitor_closely"


# ===== GENERATE_SUGGESTIONS - CONTEXT PARAMETER =====

@pytest.mark.asyncio
async def test_generate_suggestions_with_context():
    """
    SCENARIO: generate_suggestions() called with context parameter
    EXPECTED: Suggestions generated (context currently not used)
    """
    generator = SuggestionGenerator()
    analysis = {
        "prediction_type": "threat_detection",
        "predicted_event": "attack",
        "confidence": 0.8
    }
    context = {"source": "firewall_logs", "timestamp": "2025-10-23T10:00:00Z"}

    suggestions = await generator.generate_suggestions(analysis, context)

    assert len(suggestions) == 2  # threat_detection with high confidence


@pytest.mark.asyncio
async def test_generate_suggestions_with_none_context():
    """
    SCENARIO: generate_suggestions() with context=None
    EXPECTED: Works correctly (default behavior)
    """
    generator = SuggestionGenerator()
    analysis = {
        "prediction_type": "resource_optimization",
        "predicted_event": "load",
        "confidence": 0.7
    }

    suggestions = await generator.generate_suggestions(analysis, None)

    assert len(suggestions) == 2


# ===== GENERATE_SUGGESTIONS - HISTORY TRACKING =====

@pytest.mark.asyncio
async def test_generate_suggestions_updates_history():
    """
    SCENARIO: generate_suggestions() called
    EXPECTED: Suggestions added to generated_suggestions history
    """
    generator = SuggestionGenerator()
    analysis = {
        "prediction_type": "threat_detection",
        "predicted_event": "attack",
        "confidence": 0.8
    }

    await generator.generate_suggestions(analysis)

    assert len(generator.generated_suggestions) == 2  # threat_detection returns 2


@pytest.mark.asyncio
async def test_generate_suggestions_updates_last_generation_time():
    """
    SCENARIO: generate_suggestions() called
    EXPECTED: last_generation_time updated to datetime
    """
    generator = SuggestionGenerator()
    analysis = {
        "prediction_type": "resource_optimization",
        "predicted_event": "load",
        "confidence": 0.7
    }

    await generator.generate_suggestions(analysis)

    assert generator.last_generation_time is not None
    assert isinstance(generator.last_generation_time, datetime)


@pytest.mark.asyncio
async def test_generate_suggestions_multiple_calls_accumulate():
    """
    SCENARIO: generate_suggestions() called multiple times
    EXPECTED: All suggestions accumulated in history
    """
    generator = SuggestionGenerator()

    await generator.generate_suggestions({
        "prediction_type": "threat_detection",
        "predicted_event": "attack1",
        "confidence": 0.8
    })
    await generator.generate_suggestions({
        "prediction_type": "resource_optimization",
        "predicted_event": "load",
        "confidence": 0.7
    })

    assert len(generator.generated_suggestions) == 4  # 2 + 2


# ===== GENERATE_SUGGESTIONS - MISSING FIELDS =====

@pytest.mark.asyncio
async def test_generate_suggestions_missing_confidence():
    """
    SCENARIO: generate_suggestions() with missing confidence
    EXPECTED: Uses default 0.5, returns fallback suggestion
    """
    generator = SuggestionGenerator()
    analysis = {
        "prediction_type": "threat_detection",
        "predicted_event": "attack"
        # No confidence field
    }

    suggestions = await generator.generate_suggestions(analysis)

    # confidence defaults to 0.5, which is ≤ 0.7 for threat_detection
    assert len(suggestions) == 1
    assert suggestions[0]["type"] == "monitor_closely"


@pytest.mark.asyncio
async def test_generate_suggestions_empty_analysis():
    """
    SCENARIO: generate_suggestions() with empty analysis dict
    EXPECTED: Returns fallback suggestion
    """
    generator = SuggestionGenerator()

    suggestions = await generator.generate_suggestions({})

    assert len(suggestions) == 1
    assert suggestions[0]["type"] == "monitor_closely"


# ===== GET_STATUS METHOD TESTS =====

@pytest.mark.asyncio
async def test_get_status_initial_state():
    """
    SCENARIO: get_status() on new generator
    EXPECTED: status=ready_to_suggest, 0 suggestions, last_generation=N/A
    """
    generator = SuggestionGenerator()

    status = await generator.get_status()

    assert status["status"] == "ready_to_suggest"
    assert status["total_suggestions_generated"] == 0
    assert status["last_generation"] == "N/A"


@pytest.mark.asyncio
async def test_get_status_after_generation():
    """
    SCENARIO: get_status() after generating suggestions
    EXPECTED: total_suggestions_generated > 0, last_generation has timestamp
    """
    generator = SuggestionGenerator()
    await generator.generate_suggestions({
        "prediction_type": "threat_detection",
        "predicted_event": "attack",
        "confidence": 0.8
    })

    status = await generator.get_status()

    assert status["total_suggestions_generated"] == 2
    assert status["last_generation"] != "N/A"
    assert isinstance(status["last_generation"], str)


@pytest.mark.asyncio
async def test_get_status_multiple_generations():
    """
    SCENARIO: get_status() after multiple generations
    EXPECTED: total_suggestions_generated matches total count
    """
    generator = SuggestionGenerator()

    await generator.generate_suggestions({
        "prediction_type": "threat_detection",
        "predicted_event": "attack1",
        "confidence": 0.8
    })
    await generator.generate_suggestions({
        "prediction_type": "resource_optimization",
        "predicted_event": "load",
        "confidence": 0.7
    })
    await generator.generate_suggestions({
        "prediction_type": "unknown",
        "predicted_event": "event",
        "confidence": 0.9
    })

    status = await generator.get_status()

    assert status["total_suggestions_generated"] == 5  # 2 + 2 + 1


@pytest.mark.asyncio
async def test_get_status_returns_dict():
    """
    SCENARIO: get_status() called
    EXPECTED: Returns dictionary with expected keys
    """
    generator = SuggestionGenerator()

    status = await generator.get_status()

    assert isinstance(status, dict)
    assert "status" in status
    assert "total_suggestions_generated" in status
    assert "last_generation" in status


# ===== INTEGRATION TESTS =====

@pytest.mark.asyncio
async def test_complete_workflow():
    """
    SCENARIO: Complete workflow with multiple prediction types
    EXPECTED: All operations work together correctly
    """
    generator = SuggestionGenerator()

    # Initial status
    status = await generator.get_status()
    assert status["total_suggestions_generated"] == 0

    # Generate threat detection suggestions
    suggestions1 = await generator.generate_suggestions({
        "prediction_type": "threat_detection",
        "predicted_event": "DDoS attack",
        "confidence": 0.9
    })
    assert len(suggestions1) == 2
    assert suggestions1[0]["priority"] == "critical"

    # Generate resource optimization suggestions
    suggestions2 = await generator.generate_suggestions({
        "prediction_type": "resource_optimization",
        "predicted_event": "peak load expected",
        "confidence": 0.8
    })
    assert len(suggestions2) == 2
    assert suggestions2[0]["priority"] == "medium"

    # Check final status
    status = await generator.get_status()
    assert status["total_suggestions_generated"] == 4
    assert status["last_generation"] != "N/A"


@pytest.mark.asyncio
async def test_priority_escalation_logic():
    """
    SCENARIO: Test priority logic across different scenarios
    EXPECTED: Priorities assigned correctly based on type and confidence
    """
    generator = SuggestionGenerator()

    # Critical priority (threat + high confidence)
    s1 = await generator.generate_suggestions({
        "prediction_type": "threat_detection",
        "predicted_event": "attack",
        "confidence": 0.95
    })
    assert s1[0]["priority"] == "critical"

    # Medium priority (resource optimization + medium confidence)
    s2 = await generator.generate_suggestions({
        "prediction_type": "resource_optimization",
        "predicted_event": "load",
        "confidence": 0.7
    })
    assert s2[0]["priority"] == "medium"

    # Low priority (fallback)
    s3 = await generator.generate_suggestions({
        "prediction_type": "unknown",
        "predicted_event": "event",
        "confidence": 0.9
    })
    assert s3[0]["priority"] == "low"
