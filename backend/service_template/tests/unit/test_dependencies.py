"""
Tests for Presentation Layer - Dependencies

100% coverage required.
"""
from unittest.mock import MagicMock

from service_template.infrastructure.config import Settings
from service_template.presentation.dependencies import get_database


class TestGetDatabase:
    """Tests for get_database dependency."""

    def test_returns_database_instance(self) -> None:
        """Test get_database returns Database instance."""
        settings = Settings()
        
        db = get_database(settings)
        
        assert db is not None

    def test_singleton_pattern(self) -> None:
        """Test get_database returns same instance."""
        settings = Settings()
        
        db1 = get_database(settings)
        db2 = get_database(settings)
        
        assert db1 is db2
