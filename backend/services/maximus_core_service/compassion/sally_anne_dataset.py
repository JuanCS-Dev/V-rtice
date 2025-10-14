"""
Sally-Anne False Belief Test Dataset
=====================================

10 scenarios for Theory of Mind (ToM) validation.
Classic test for false belief tracking - can the system model
another agent's incorrect belief about reality?

Based on: Baron-Cohen et al. (1985) "Does the autistic child have a theory of mind?"

Authors: Claude Code (Executor Tático)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Padrão Pagani
"""

from typing import List, Dict, Any


# ===========================================================================
# SALLY-ANNE DATASET (10 Scenarios)
# ===========================================================================

SALLY_ANNE_SCENARIOS: List[Dict[str, Any]] = [
    # Scenario 1: Classic Sally-Anne (basket → box)
    {
        "id": "classic_basket_box",
        "description": "Classic Sally-Anne test with basket and box",
        "setup": {
            "sally_belief": "marble_in_basket",
            "anne_action": "moved_marble_to_box",
            "reality": "marble_in_box",
        },
        "question": "Where will Sally look for the marble?",
        "correct_answer": "basket",  # Sally believes it's still in basket
        "rationale": "Sally was absent when Anne moved the marble. Sally's belief is outdated.",
    },

    # Scenario 2: Updated belief (Sally returns and sees)
    {
        "id": "sally_returns_and_sees",
        "description": "Sally returns and observes the new location",
        "setup": {
            "sally_initial_belief": "marble_in_basket",
            "anne_action": "moved_marble_to_box",
            "sally_observes": True,
            "reality": "marble_in_box",
        },
        "question": "Where will Sally look for the marble?",
        "correct_answer": "box",  # Sally updated her belief by observing
        "rationale": "Sally observed Anne moving the marble. Belief updated to match reality.",
    },

    # Scenario 3: Deception (Anne lies to Sally)
    {
        "id": "deception_false_info",
        "description": "Anne tells Sally incorrect location",
        "setup": {
            "reality": "marble_in_box",
            "anne_tells_sally": "marble_in_basket",
            "sally_belief": "marble_in_basket",  # Believes Anne's lie
        },
        "question": "Where will Sally look for the marble?",
        "correct_answer": "basket",  # Sally believes Anne's false information
        "rationale": "Sally trusts Anne's false information. Reality ≠ Sally's belief.",
    },

    # Scenario 4: Third-party observation (Tom watches)
    {
        "id": "third_party_tom",
        "description": "Tom observes Anne moving marble, Sally doesn't",
        "setup": {
            "sally_belief": "marble_in_basket",
            "anne_action": "moved_marble_to_box",
            "tom_observes": True,
            "reality": "marble_in_box",
        },
        "question": "Where does Tom think Sally will look?",
        "correct_answer": "basket",  # Tom knows Sally has false belief
        "rationale": "Tom has second-order ToM: Tom knows Sally doesn't know about the move.",
    },

    # Scenario 5: Multiple moves (basket → box → drawer)
    {
        "id": "multiple_moves",
        "description": "Marble moved twice while Sally is absent",
        "setup": {
            "sally_initial_belief": "marble_in_basket",
            "anne_action_1": "moved_marble_to_box",
            "anne_action_2": "moved_marble_to_drawer",
            "reality": "marble_in_drawer",
        },
        "question": "Where will Sally look for the marble?",
        "correct_answer": "basket",  # Sally's belief frozen at initial state
        "rationale": "Sally missed both moves. Belief remains at initial location.",
    },

    # Scenario 6: Partial observation (sees first move, misses second)
    {
        "id": "partial_observation",
        "description": "Sally sees first move but misses second",
        "setup": {
            "sally_initial_belief": "marble_in_basket",
            "sally_observes_move_1": True,  # basket → box
            "anne_action_1": "moved_marble_to_box",
            "sally_observes_move_2": False,  # Absent for box → drawer
            "anne_action_2": "moved_marble_to_drawer",
            "reality": "marble_in_drawer",
        },
        "question": "Where will Sally look for the marble?",
        "correct_answer": "box",  # Sally's belief updated after first move only
        "rationale": "Sally updated belief after first move, but missed second move.",
    },

    # Scenario 7: Inference (Sally infers from evidence)
    {
        "id": "inference_from_evidence",
        "description": "Sally finds empty basket and infers move",
        "setup": {
            "sally_initial_belief": "marble_in_basket",
            "anne_action": "moved_marble_to_box",
            "sally_checks_basket": True,
            "basket_is_empty": True,
        },
        "question": "Where will Sally look next?",
        "correct_answer": "box",  # Sally infers marble was moved
        "rationale": "Sally infers from empty basket that marble was relocated.",
    },

    # Scenario 8: Memory decay (long time passes)
    {
        "id": "memory_decay",
        "description": "Long time passes, Sally forgets original location",
        "setup": {
            "sally_initial_belief": "marble_in_basket",
            "time_passed": "30_days",
            "anne_action": "moved_marble_to_box",
            "reality": "marble_in_box",
        },
        "question": "Where will Sally look for the marble?",
        "correct_answer": "uncertain",  # Belief decayed due to time
        "rationale": "After 30 days, Sally's confidence in original belief is low (temporal decay).",
    },

    # Scenario 9: Conflicting evidence (sees empty box)
    {
        "id": "conflicting_evidence",
        "description": "Anne says box, but Sally sees box is empty",
        "setup": {
            "anne_tells_sally": "marble_in_box",
            "sally_checks_box": True,
            "box_is_empty": True,
            "reality": "marble_in_drawer",  # Anne was wrong
        },
        "question": "Where will Sally look next?",
        "correct_answer": "drawer",  # Sally searches other locations
        "rationale": "Sally detects contradiction (Anne's claim vs. observation). Searches elsewhere.",
    },

    # Scenario 10: Nested belief (Sally thinks Anne thinks...)
    {
        "id": "nested_second_order",
        "description": "Second-order: Sally thinks Anne believes marble is in basket",
        "setup": {
            "reality": "marble_in_box",  # Sally moved it
            "sally_action": "moved_marble_to_box",
            "anne_initial_belief": "marble_in_basket",
            "anne_absent": True,
        },
        "question": "Where does Sally think Anne will look?",
        "correct_answer": "basket",  # Sally models Anne's false belief
        "rationale": "Sally has second-order ToM: Sally knows Anne doesn't know Sally moved it.",
    },
]


# ===========================================================================
# EXPECTED ANSWERS KEY
# ===========================================================================

EXPECTED_ANSWERS = {
    scenario["id"]: scenario["correct_answer"]
    for scenario in SALLY_ANNE_SCENARIOS
}


# ===========================================================================
# DIFFICULTY LEVELS
# ===========================================================================

DIFFICULTY_LEVELS = {
    "basic": ["classic_basket_box", "sally_returns_and_sees"],
    "intermediate": [
        "deception_false_info",
        "third_party_tom",
        "multiple_moves",
        "partial_observation",
    ],
    "advanced": [
        "inference_from_evidence",
        "memory_decay",
        "conflicting_evidence",
        "nested_second_order",
    ],
}


# ===========================================================================
# HELPER FUNCTIONS
# ===========================================================================

def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """Get scenario by ID.

    Args:
        scenario_id: Scenario identifier

    Returns:
        Scenario dictionary

    Raises:
        KeyError: If scenario_id not found
    """
    for scenario in SALLY_ANNE_SCENARIOS:
        if scenario["id"] == scenario_id:
            return scenario

    raise KeyError(f"Scenario '{scenario_id}' not found")


def get_scenarios_by_difficulty(difficulty: str) -> List[Dict[str, Any]]:
    """Get all scenarios of a given difficulty level.

    Args:
        difficulty: One of "basic", "intermediate", "advanced"

    Returns:
        List of scenario dictionaries
    """
    if difficulty not in DIFFICULTY_LEVELS:
        raise ValueError(f"Invalid difficulty: {difficulty}")

    scenario_ids = DIFFICULTY_LEVELS[difficulty]
    return [get_scenario(sid) for sid in scenario_ids]


def get_all_scenarios() -> List[Dict[str, Any]]:
    """Get all 10 scenarios.

    Returns:
        List of all scenario dictionaries
    """
    return SALLY_ANNE_SCENARIOS.copy()
