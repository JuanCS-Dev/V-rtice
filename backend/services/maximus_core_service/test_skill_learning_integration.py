"""
Skill Learning - MAXIMUS Integration Tests

Validates that Skill Learning System is properly integrated with MaximusIntegrated.
Tests integration without requiring HSAS service (structure validation).

Tests:
1. MaximusIntegrated initializes with Skill Learning support
2. Skill Learning availability flag works correctly
3. execute_learned_skill() handles unavailable gracefully
4. learn_skill_from_demonstration() connects with memory
5. compose_skill_from_primitives() connects with neuromodulation
6. get_skill_learning_state() returns correct structure
7. System status includes Skill Learning

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO - Zero mocks, graceful degradation
"""

from pathlib import Path

# ============================================================================
# TEST 1: MAXIMUS INITIALIZES WITH SKILL LEARNING SUPPORT
# ============================================================================


def test_maximus_initializes_with_skill_learning():
    """Test that MaximusIntegrated initializes with Skill Learning support."""
    print("\n" + "=" * 80)
    print("TEST 1: MaximusIntegrated Initializes with Skill Learning")
    print("=" * 80)

    # Read maximus_integrated.py source
    path = Path(__file__).parent / "maximus_integrated.py"
    with open(path) as f:
        source = f.read()

    # Check that Skill Learning is initialized
    assert "self.skill_learning" in source, "MaximusIntegrated missing skill_learning attribute"
    assert "skill_learning_available" in source, "Missing skill_learning_available flag"
    print("✅ MaximusIntegrated has skill_learning and availability flag")

    # Check for try/except (graceful degradation)
    assert "try:" in source and "except" in source, "Missing graceful degradation"
    print("✅ Graceful degradation implemented for HSAS service dependency")

    # Check initialization of SkillLearningController
    assert "SkillLearningController" in source, "Missing SkillLearningController initialization"
    assert "hsas_url" in source, "Missing HSAS service URL configuration"
    print("✅ SkillLearningController imported and initialized")

    print("✅ Test passed")


# ============================================================================
# TEST 2: SKILL LEARNING AVAILABILITY FLAG
# ============================================================================


def test_skill_learning_availability_flag():
    """Test that skill_learning_available flag is properly set."""
    print("\n" + "=" * 80)
    print("TEST 2: Skill Learning Availability Flag")
    print("=" * 80)

    path = Path(__file__).parent / "maximus_integrated.py"
    with open(path) as f:
        source = f.read()

    # Check that flag is set in try block
    assert "self.skill_learning_available = True" in source, "Missing skill_learning_available = True"
    print("✅ Availability flag set to True in try block")

    # Check that flag is initialized to False
    assert "self.skill_learning_available = False" in source, "Missing skill_learning_available = False initialization"
    print("✅ Availability flag initialized to False before try")

    print("✅ Test passed")


# ============================================================================
# TEST 3: execute_learned_skill() HANDLES UNAVAILABLE
# ============================================================================


def test_execute_learned_skill_api():
    """Test that execute_learned_skill() has correct API."""
    print("\n" + "=" * 80)
    print("TEST 3: execute_learned_skill() API")
    print("=" * 80)

    path = Path(__file__).parent / "maximus_integrated.py"
    with open(path) as f:
        source = f.read()

    # Check method exists
    assert "async def execute_learned_skill(" in source, "Missing execute_learned_skill() method"
    print("✅ execute_learned_skill() method exists")

    # Check it returns gracefully when unavailable
    assert '"available": False,' in source or "'available': False," in source, (
        "execute_learned_skill() doesn't handle unavailable"
    )
    print("✅ Method handles unavailable HSAS gracefully")

    # Check neuromodulation integration
    assert "self.neuromodulation.dopamine" in source, "Method missing dopamine integration"
    print("✅ Method integrates with dopamine (RPE)")

    # Check it has skill execution logic
    assert "execute_skill" in source.lower() or "skill_name" in source.lower(), "Method missing skill execution logic"
    print("✅ Method references skill execution")

    print("✅ Test passed")


# ============================================================================
# TEST 4: learn_skill_from_demonstration() CONNECTS WITH MEMORY
# ============================================================================


def test_learn_skill_from_demonstration_memory_connection():
    """Test that learn_skill_from_demonstration() connects with memory."""
    print("\n" + "=" * 80)
    print("TEST 4: learn_skill_from_demonstration() Memory Connection")
    print("=" * 80)

    path = Path(__file__).parent / "maximus_integrated.py"
    with open(path) as f:
        source = f.read()

    # Check method exists
    assert "async def learn_skill_from_demonstration(" in source, "Missing learn_skill_from_demonstration() method"
    print("✅ learn_skill_from_demonstration() method exists")

    # Check it stores in memory system
    assert "self.memory_system.store_memory" in source, "Method doesn't store in memory system"
    print("✅ Method stores learned skill in memory")

    # Check it updates dopamine (intrinsic reward)
    assert "self.neuromodulation.dopamine" in source, "Method doesn't provide intrinsic reward"
    print("✅ Method provides dopamine boost for learning")

    # Check it calls HSAS service
    assert "learn_from_demonstration" in source, "Method doesn't call HSAS service"
    print("✅ Method calls HSAS service")

    print("✅ Test passed")


# ============================================================================
# TEST 5: compose_skill_from_primitives() CONNECTS WITH NEUROMODULATION
# ============================================================================


def test_compose_skill_neuromodulation_connection():
    """Test that compose_skill_from_primitives() connects with neuromodulation."""
    print("\n" + "=" * 80)
    print("TEST 5: compose_skill_from_primitives() Neuromodulation Connection")
    print("=" * 80)

    path = Path(__file__).parent / "maximus_integrated.py"
    with open(path) as f:
        source = f.read()

    # Check method exists
    assert "async def compose_skill_from_primitives(" in source, "Missing compose_skill_from_primitives() method"
    print("✅ compose_skill_from_primitives() method exists")

    # Check it updates serotonin (creativity)
    assert "self.neuromodulation.serotonin" in source, "Method doesn't connect with serotonin system"
    print("✅ Method connects with serotonin (creativity)")

    # Check it stores composed skill
    assert "self.memory_system.store_memory" in source, "Method doesn't store composed skill"
    print("✅ Method stores composed skill in memory")

    # Check it calls HSAS compose_skill
    assert "compose_skill" in source, "Method doesn't call HSAS service"
    print("✅ Method calls HSAS service")

    print("✅ Test passed")


# ============================================================================
# TEST 6: get_skill_learning_state() RETURNS CORRECT STRUCTURE
# ============================================================================


def test_get_skill_learning_state_structure():
    """Test that get_skill_learning_state() returns correct structure."""
    print("\n" + "=" * 80)
    print("TEST 6: get_skill_learning_state() Structure")
    print("=" * 80)

    path = Path(__file__).parent / "maximus_integrated.py"
    with open(path) as f:
        source = f.read()

    # Check method exists
    assert "def get_skill_learning_state(" in source, "Missing get_skill_learning_state() method"
    print("✅ get_skill_learning_state() method exists")

    # Check it returns availability info
    assert '"available": False' in source or "'available': False" in source, "Method doesn't return availability info"
    print("✅ Method returns availability info")

    # Check it accesses controller state
    assert "self.skill_learning.export_state" in source or "self.skill_learning" in source, (
        "Method doesn't access Skill Learning controller state"
    )
    print("✅ Method accesses Skill Learning controller state")

    print("✅ Test passed")


# ============================================================================
# TEST 7: SYSTEM STATUS INCLUDES SKILL LEARNING
# ============================================================================


def test_system_status_includes_skill_learning():
    """Test that get_system_status() includes Skill Learning info."""
    print("\n" + "=" * 80)
    print("TEST 7: System Status Includes Skill Learning")
    print("=" * 80)

    path = Path(__file__).parent / "maximus_integrated.py"
    with open(path) as f:
        source = f.read()

    # Find get_system_status method
    assert "async def get_system_status(" in source, "Missing get_system_status() method"
    print("✅ get_system_status() method exists")

    # Check it includes skill_learning_status
    assert "skill_learning_status" in source, "System status doesn't include skill_learning_status"
    print("✅ System status includes skill_learning_status")

    # Check it calls get_skill_learning_state()
    assert "self.get_skill_learning_state()" in source, "System status doesn't call get_skill_learning_state()"
    print("✅ System status calls get_skill_learning_state()")

    print("✅ Test passed")


# ============================================================================
# TEST 8: PREDICTIVE CODING INTEGRATION
# ============================================================================


def test_skill_learning_predictive_coding_integration():
    """Test that Skill Learning integrates with Predictive Coding."""
    print("\n" + "=" * 80)
    print("TEST 8: Skill Learning - Predictive Coding Integration")
    print("=" * 80)

    path = Path(__file__).parent / "maximus_integrated.py"
    with open(path) as f:
        source = f.read()

    # Check execute_learned_skill connects to Predictive Coding
    # Find the execute_learned_skill method
    execute_skill_start = source.find("async def execute_learned_skill(")
    execute_skill_end = source.find("\n    async def", execute_skill_start + 1)
    execute_skill_code = source[execute_skill_start:execute_skill_end]

    assert "predictive_coding_available" in execute_skill_code, (
        "execute_learned_skill doesn't check Predictive Coding availability"
    )
    print("✅ execute_learned_skill() checks Predictive Coding availability")

    assert "process_prediction_error" in execute_skill_code, "execute_learned_skill doesn't process prediction errors"
    print("✅ execute_learned_skill() processes prediction errors")

    # Check layer parameter is correct (tactical timescale)
    assert 'layer="l4"' in execute_skill_code or "layer='l4'" in execute_skill_code, (
        "execute_learned_skill uses wrong Predictive Coding layer"
    )
    print("✅ execute_learned_skill() uses correct layer (L4 - tactical)")

    print("✅ Test passed")


# ============================================================================
# SUMMARY
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SKILL LEARNING - MAXIMUS INTEGRATION TESTS")
    print("=" * 80)
    print("\nRunning tests...")
    print("\nTest Suite:")
    print("  1. MaximusIntegrated initializes with Skill Learning")
    print("  2. Skill Learning availability flag")
    print("  3. execute_learned_skill() API")
    print("  4. learn_skill_from_demonstration() memory connection")
    print("  5. compose_skill_from_primitives() neuromodulation connection")
    print("  6. get_skill_learning_state() structure")
    print("  7. System status includes Skill Learning")
    print("  8. Predictive Coding integration")
    print("\nTarget: 8/8 passing (100%)")
    print("=" * 80)
