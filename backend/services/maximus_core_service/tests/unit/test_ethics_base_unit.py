"""
Ethics Base Module - Comprehensive Unit Test Suite
Coverage Target: 85%+

Tests the CRITICAL ethics base classes:
- EthicalFrameworkResult validation
- ActionContext validation (all fields)
- EthicalFramework abstract class methods
- EthicalCache (caching, TTL, eviction)

Author: Claude Code + JuanCS-Dev (Artisanal, DOUTRINA VÉRTICE)
Date: 2025-10-21
"""

import pytest
import time
from ethics.base import (
    ActionContext,
    EthicalFramework,
    EthicalFrameworkResult,
    EthicalVerdict,
    EthicalCache,
    VetoException,
)


# ===== FIXTURES =====

@pytest.fixture
def valid_action_context():
    """Valid ActionContext for testing."""
    return ActionContext(
        action_description="Perform security scan with proper authorization and user consent",
        action_type="security_scan",
        system_component="test_scanner",
        urgency="medium"
    )


@pytest.fixture
def ethical_cache():
    """Fresh EthicalCache instance."""
    return EthicalCache(max_size=100, ttl_seconds=60)


@pytest.fixture
def sample_result():
    """Sample EthicalFrameworkResult for caching tests."""
    return EthicalFrameworkResult(
        framework_name="test_framework",
        approved=True,
        confidence=0.95,
        veto=False,
        explanation="Test reasoning",
        reasoning_steps=["Step 1", "Step 2"],
        verdict=EthicalVerdict.APPROVED,
        latency_ms=10,
        metadata={}
    )


# Mock implementation for testing abstract EthicalFramework
class MockEthicalFramework(EthicalFramework):
    """Mock implementation of EthicalFramework for testing."""

    def __init__(self, name: str = "MockFramework", config: dict = None):
        super().__init__(config or {"version": "2.0.0"})
        if name != "MockFramework":
            self.name = name.lower()

    async def evaluate(self, action_context: ActionContext) -> EthicalFrameworkResult:
        """Mock evaluation."""
        return EthicalFrameworkResult(
            framework_name=self.name,
            approved=True,
            confidence=0.9,
            veto=False,
            explanation="Mock evaluation",
            reasoning_steps=["Mock step"],
            verdict=EthicalVerdict.APPROVED,
            latency_ms=5,
            metadata={}
        )

    def get_framework_principles(self) -> list[str]:
        """Mock principles."""
        return ["Principle 1", "Principle 2"]


# ===== ETHICALFRAMEWORKRESULT VALIDATION TESTS =====

class TestEthicalFrameworkResultValidation:
    """Tests for EthicalFrameworkResult validation."""

    @pytest.mark.unit
    def test_result_valid_confidence(self):
        """
        SCENARIO: Create EthicalFrameworkResult with valid confidence
        EXPECTED: No validation error
        """
        # Act
        result = EthicalFrameworkResult(
            framework_name="test",
            approved=True,
            confidence=0.85,
            veto=False,
            explanation="Valid confidence",
            reasoning_steps=["Step 1"],
            verdict=EthicalVerdict.APPROVED,
            latency_ms=10,
            metadata={}
        )

        # Assert
        assert result.confidence == 0.85

    @pytest.mark.unit
    def test_result_invalid_confidence_too_high(self):
        """
        SCENARIO: Create EthicalFrameworkResult with confidence > 1.0
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            EthicalFrameworkResult(
                framework_name="test",
                approved=True,
                confidence=1.5,
                veto=False,
                explanation="Invalid confidence",
                reasoning_steps=["Step 1"],
                verdict=EthicalVerdict.APPROVED,
                latency_ms=10,
                metadata={}
            )

        assert "confidence must be between 0.0 and 1.0" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_result_invalid_confidence_negative(self):
        """
        SCENARIO: Create EthicalFrameworkResult with negative confidence
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            EthicalFrameworkResult(
                framework_name="test",
                approved=False,
                confidence=-0.1,
                veto=False,
                explanation="Invalid confidence",
                reasoning_steps=["Step 1"],
                verdict=EthicalVerdict.REJECTED,
                latency_ms=10,
                metadata={}
            )

        assert "confidence must be between 0.0 and 1.0" in str(exc_info.value).lower()


# ===== ACTIONCONTEXT VALIDATION TESTS =====

class TestActionContextValidation:
    """Tests for ActionContext validation (comprehensive)."""

    @pytest.mark.unit
    def test_action_context_valid(self, valid_action_context):
        """
        SCENARIO: Create ActionContext with all valid fields
        EXPECTED: No validation error
        """
        # Assert
        assert valid_action_context.action_type == "security_scan"
        assert valid_action_context.urgency == "medium"

    @pytest.mark.unit
    def test_action_type_empty(self):
        """
        SCENARIO: ActionContext with empty action_type
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="Valid description here",
                action_type="",
                system_component="test",
                urgency="low"
            )

        assert "action_type is required and cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_action_type_too_long(self):
        """
        SCENARIO: ActionContext with action_type > 100 characters
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="Valid description here",
                action_type="a" * 101,
                system_component="test",
                urgency="low"
            )

        assert "action_type must be less than 100 characters" in str(exc_info.value)

    @pytest.mark.unit
    def test_action_description_empty(self):
        """
        SCENARIO: ActionContext with empty action_description
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="",
                action_type="test",
                system_component="test",
                urgency="low"
            )

        assert "action_description is required and cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_action_description_too_short(self):
        """
        SCENARIO: ActionContext with action_description < 10 characters
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="Short",
                action_type="test",
                system_component="test",
                urgency="low"
            )

        assert "action_description must be at least 10 characters" in str(exc_info.value)

    @pytest.mark.unit
    def test_action_description_too_long(self):
        """
        SCENARIO: ActionContext with action_description > 1000 characters
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="a" * 1001,
                action_type="test",
                system_component="test",
                urgency="low"
            )

        assert "action_description must be less than 1000 characters" in str(exc_info.value)

    @pytest.mark.unit
    def test_system_component_empty(self):
        """
        SCENARIO: ActionContext with empty system_component
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="Valid description here",
                action_type="test",
                system_component="",
                urgency="low"
            )

        assert "system_component is required and cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_system_component_too_long(self):
        """
        SCENARIO: ActionContext with system_component > 100 characters
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="Valid description here",
                action_type="test",
                system_component="c" * 101,
                urgency="low"
            )

        assert "system_component must be less than 100 characters" in str(exc_info.value)

    @pytest.mark.unit
    def test_urgency_invalid(self):
        """
        SCENARIO: ActionContext with invalid urgency value
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="Valid description here",
                action_type="test",
                system_component="test",
                urgency="super_urgent"
            )

        assert "urgency must be one of" in str(exc_info.value)

    @pytest.mark.unit
    def test_threat_data_severity_invalid(self):
        """
        SCENARIO: ActionContext with threat_data.severity > 1.0
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="Valid description here",
                action_type="test",
                system_component="test",
                urgency="high",
                threat_data={"severity": 1.5}
            )

        assert "threat_data.severity must be a number between 0.0 and 1.0" in str(exc_info.value)

    @pytest.mark.unit
    def test_threat_data_confidence_invalid(self):
        """
        SCENARIO: ActionContext with threat_data.confidence < 0.0
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="Valid description here",
                action_type="test",
                system_component="test",
                urgency="high",
                threat_data={"confidence": -0.2}
            )

        assert "threat_data.confidence must be a number between 0.0 and 1.0" in str(exc_info.value)

    @pytest.mark.unit
    def test_impact_assessment_disruption_invalid(self):
        """
        SCENARIO: ActionContext with impact_assessment.disruption_level > 1.0
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ActionContext(
                action_description="Valid description here",
                action_type="test",
                system_component="test",
                urgency="high",
                impact_assessment={"disruption_level": 2.0}
            )

        assert "impact_assessment.disruption_level must be a number between 0.0 and 1.0" in str(exc_info.value)

    @pytest.mark.unit
    def test_action_context_with_valid_threat_data(self):
        """
        SCENARIO: ActionContext with valid threat_data
        EXPECTED: No validation error
        """
        # Act
        context = ActionContext(
            action_description="Valid description here",
            action_type="test",
            system_component="test",
            urgency="high",
            threat_data={"severity": 0.8, "confidence": 0.9}
        )

        # Assert
        assert context.threat_data["severity"] == 0.8
        assert context.threat_data["confidence"] == 0.9

    @pytest.mark.unit
    def test_action_context_with_valid_impact_assessment(self):
        """
        SCENARIO: ActionContext with valid impact_assessment
        EXPECTED: No validation error
        """
        # Act
        context = ActionContext(
            action_description="Valid description here",
            action_type="test",
            system_component="test",
            urgency="critical",
            impact_assessment={"disruption_level": 0.7}
        )

        # Assert
        assert context.impact_assessment["disruption_level"] == 0.7


# ===== ETHICALFRAMEWORK TESTS =====

class TestEthicalFramework:
    """Tests for EthicalFramework abstract class methods."""

    @pytest.mark.unit
    def test_get_name(self):
        """
        SCENARIO: Call get_name on framework
        EXPECTED: Returns framework name (lowercased)
        """
        # Arrange
        framework = MockEthicalFramework(name="TestFramework")

        # Act
        name = framework.get_name()

        # Assert
        assert name == "testframework"  # EthicalFramework lowercases names

    @pytest.mark.unit
    def test_get_version_custom(self):
        """
        SCENARIO: Call get_version with custom version in config
        EXPECTED: Returns custom version
        """
        # Arrange
        framework = MockEthicalFramework(config={"version": "3.1.4"})

        # Act
        version = framework.get_version()

        # Assert
        assert version == "3.1.4"

    @pytest.mark.unit
    def test_get_version_default(self):
        """
        SCENARIO: Call get_version without version in config
        EXPECTED: Returns default version "1.0.0"
        """
        # Arrange
        # Need to pass None to avoid MockEthicalFramework's default config
        framework = MockEthicalFramework(config=None)
        framework.config = {}  # Set empty config after init

        # Act
        version = framework.get_version()

        # Assert
        assert version == "1.0.0"


# ===== ETHICALCACHE TESTS =====

class TestEthicalCache:
    """Tests for EthicalCache caching functionality."""

    @pytest.mark.unit
    def test_cache_initialization(self, ethical_cache):
        """
        SCENARIO: Initialize EthicalCache
        EXPECTED: Empty cache with correct settings
        """
        # Assert
        assert ethical_cache.max_size == 100
        assert ethical_cache.ttl_seconds == 60
        assert len(ethical_cache._cache) == 0

    @pytest.mark.unit
    def test_cache_set_and_get(self, ethical_cache, sample_result):
        """
        SCENARIO: Set and get a cached result
        EXPECTED: Returns same result
        """
        # Arrange
        key = "test_key"

        # Act
        ethical_cache.set(key, sample_result)
        retrieved = ethical_cache.get(key)

        # Assert
        assert retrieved is not None
        assert retrieved.verdict == EthicalVerdict.APPROVED
        assert retrieved.confidence == 0.95
        assert retrieved.framework_name == "test_framework"

    @pytest.mark.unit
    def test_cache_get_nonexistent(self, ethical_cache):
        """
        SCENARIO: Get a key that doesn't exist
        EXPECTED: Returns None
        """
        # Act
        result = ethical_cache.get("nonexistent_key")

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_cache_ttl_expiration(self, ethical_cache, sample_result):
        """
        SCENARIO: Get a cached result after TTL expiration
        EXPECTED: Returns None (expired)
        """
        # Arrange
        cache = EthicalCache(max_size=100, ttl_seconds=1)
        key = "test_key"

        # Act
        cache.set(key, sample_result)
        time.sleep(1.1)  # Wait for TTL to expire
        result = cache.get(key)

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_cache_eviction_at_max_size(self, sample_result):
        """
        SCENARIO: Add items beyond max_size
        EXPECTED: Oldest item evicted
        """
        # Arrange
        cache = EthicalCache(max_size=3, ttl_seconds=60)

        # Act
        cache.set("key1", sample_result)
        time.sleep(0.01)  # Ensure different timestamps
        cache.set("key2", sample_result)
        time.sleep(0.01)
        cache.set("key3", sample_result)
        time.sleep(0.01)
        cache.set("key4", sample_result)  # Should evict key1

        # Assert
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None

    @pytest.mark.unit
    def test_generate_key(self, ethical_cache, valid_action_context):
        """
        SCENARIO: Generate cache key from ActionContext
        EXPECTED: Returns consistent hash string
        """
        # Act
        key1 = ethical_cache.generate_key(valid_action_context, "framework1")
        key2 = ethical_cache.generate_key(valid_action_context, "framework1")

        # Assert
        assert key1 == key2  # Same input = same key
        assert len(key1) == 64  # SHA-256 hex digest length

    @pytest.mark.unit
    def test_generate_key_different_for_different_inputs(self, ethical_cache):
        """
        SCENARIO: Generate keys for different action contexts
        EXPECTED: Different hash strings
        """
        # Arrange
        context1 = ActionContext(
            action_description="Action 1 with specific details",
            action_type="type1",
            system_component="comp1",
            urgency="low"
        )
        context2 = ActionContext(
            action_description="Action 2 with different details",
            action_type="type2",
            system_component="comp2",
            urgency="high"
        )

        # Act
        key1 = ethical_cache.generate_key(context1, "framework1")
        key2 = ethical_cache.generate_key(context2, "framework1")

        # Assert
        assert key1 != key2


# ===== VETOEXCEPTION TESTS =====

class TestVetoException:
    """Tests for VetoException."""

    @pytest.mark.unit
    def test_veto_exception_creation(self):
        """
        SCENARIO: Create VetoException with framework_name and reason
        EXPECTED: Exception with proper attributes
        """
        # Arrange
        framework_name = "KantianImperativeChecker"
        reason = "Categorical imperative violated: NEVER harm humans"

        # Act
        exception = VetoException(framework_name, reason)

        # Assert
        assert exception.framework_name == framework_name
        assert exception.reason == reason
        assert isinstance(exception, Exception)
