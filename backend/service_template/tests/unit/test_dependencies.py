"""
Tests for Presentation Layer - Dependencies

100% coverage required.
"""
from unittest.mock import MagicMock, patch

from service_template.infrastructure.config import Settings
from service_template.infrastructure.database import Database
from service_template.presentation.dependencies import get_database


class TestGetDatabase:
    """Tests for get_database dependency."""

    def test_returns_database_instance(self) -> None:
        """Test get_database returns Database instance."""
        # Reset global state
        import service_template.presentation.dependencies as deps
        deps._database_instance = None

        settings = Settings()

        db = get_database(settings)

        assert isinstance(db, Database)

    def test_singleton_pattern(self) -> None:
        """Test get_database returns same instance."""
        # Reset global state
        import service_template.presentation.dependencies as deps
        deps._database_instance = None

        settings = Settings()

        db1 = get_database(settings)
        db2 = get_database(settings)

        assert db1 is db2

    def test_creates_new_instance_when_none(self) -> None:
        """Test creates Database when _database_instance is None."""
        # Reset global state
        import service_template.presentation.dependencies as deps
        deps._database_instance = None

        settings = Settings()

        with patch("service_template.presentation.dependencies.Database") as mock_db:
            mock_instance = MagicMock(spec=Database)
            mock_db.return_value = mock_instance

            result = get_database(settings)

            assert result == mock_instance
            mock_db.assert_called_once_with(settings.database_url)

