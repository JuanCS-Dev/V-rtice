"""
Test PFC + Persistence Integration

Validates that PFC can automatically persist decisions to database.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, MagicMock

from consciousness.prefrontal_cortex import PrefrontalCortex


class TestPFCPersistenceIntegration:
    """Tests for PFC with persistence enabled."""

    def test_pfc_without_repository(self):
        """Test PFC works without repository (default behavior)."""
        pfc = PrefrontalCortex(enable_mip=False)

        assert pfc.repository is None
        assert pfc.stats["persisted_decisions"] == 0

    def test_pfc_with_repository_saves_decisions(self):
        """Test PFC saves decisions when repository provided."""
        # Create mock repository
        mock_repo = Mock()
        mock_repo.save_decision = Mock(return_value=uuid4())

        pfc = PrefrontalCortex(enable_mip=False, repository=mock_repo)
        user_id = uuid4()

        # Make a decision
        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals={"error_count": 0, "task_success": True},
            action_description="Normal operation"
        )

        # Verify save was called
        mock_repo.save_decision.assert_called_once_with(decision)
        assert pfc.stats["persisted_decisions"] == 1
        assert pfc.stats["total_decisions"] == 1

    def test_pfc_continues_on_persistence_error(self):
        """Test PFC continues even if persistence fails."""
        # Create mock repository that fails
        mock_repo = Mock()
        mock_repo.save_decision = Mock(side_effect=Exception("Database error"))

        pfc = PrefrontalCortex(enable_mip=False, repository=mock_repo)
        user_id = uuid4()

        # Make a decision - should succeed despite persistence error
        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals={"error_count": 0, "task_success": True},
            action_description="Normal operation"
        )

        # Decision succeeded but wasn't persisted
        assert decision is not None
        assert pfc.stats["total_decisions"] == 1
        assert pfc.stats["persisted_decisions"] == 0  # Persistence failed

    def test_pfc_with_repository_multiple_decisions(self):
        """Test multiple decisions are all persisted."""
        mock_repo = Mock()
        mock_repo.save_decision = Mock(return_value=uuid4())

        pfc = PrefrontalCortex(enable_mip=False, repository=mock_repo)
        user_id = uuid4()

        # Make 3 decisions
        for i in range(3):
            pfc.orchestrate_decision(
                user_id=user_id,
                behavioral_signals={"error_count": i, "task_success": True},
                action_description=f"Operation {i}"
            )

        # All 3 should be persisted
        assert mock_repo.save_decision.call_count == 3
        assert pfc.stats["persisted_decisions"] == 3
        assert pfc.stats["total_decisions"] == 3

    def test_pfc_persistence_statistics(self):
        """Test persistence statistics are tracked correctly."""
        mock_repo = Mock()
        mock_repo.save_decision = Mock(return_value=uuid4())

        pfc = PrefrontalCortex(enable_mip=False, repository=mock_repo)
        user_id = uuid4()

        # Make some decisions
        for _ in range(5):
            pfc.orchestrate_decision(
                user_id=user_id,
                behavioral_signals={"error_count": 0},
                action_description="Test"
            )

        stats = pfc.get_statistics()
        assert stats["persisted_decisions"] == 5
        assert stats["total_decisions"] == 5
