"""Complete models tests for 100% coverage."""
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from service_template.infrastructure.database.models import GUID, ExampleModel


class TestGUIDTypeDecorator:
    """Test GUID type decorator for complete coverage."""

    def test_process_bind_param_with_uuid(self) -> None:
        """Test binding UUID parameter."""
        guid = GUID()
        test_uuid = uuid4()

        result = guid.process_bind_param(test_uuid, dialect=None)

        assert result == str(test_uuid)

    def test_process_bind_param_with_none(self) -> None:
        """Test binding None parameter."""
        guid = GUID()

        result = guid.process_bind_param(None, dialect=None)

        assert result is None

    def test_process_bind_param_with_string(self) -> None:
        """Test binding string parameter."""
        guid = GUID()
        test_str = "test-string"

        result = guid.process_bind_param(test_str, dialect=None)

        assert result == test_str

    def test_process_result_value_with_string(self) -> None:
        """Test processing string result."""
        guid = GUID()
        test_uuid_str = str(uuid4())

        result = guid.process_result_value(test_uuid_str, dialect=None)

        assert isinstance(result, UUID)
        assert str(result) == test_uuid_str

    def test_process_result_value_with_none(self) -> None:
        """Test processing None result."""
        guid = GUID()

        result = guid.process_result_value(None, dialect=None)

        assert result is None

    def test_process_result_value_with_uuid(self) -> None:
        """Test processing UUID result."""
        guid = GUID()
        test_uuid = uuid4()

        result = guid.process_result_value(test_uuid, dialect=None)

        assert result == test_uuid

    def test_load_dialect_impl_postgresql(self) -> None:
        """Test loading PostgreSQL dialect implementation."""
        guid = GUID()
        mock_dialect = MagicMock()
        mock_dialect.name = 'postgresql'

        result = guid.load_dialect_impl(mock_dialect)

        assert result is not None

    def test_load_dialect_impl_sqlite(self) -> None:
        """Test loading SQLite dialect implementation."""
        guid = GUID()
        mock_dialect = MagicMock()
        mock_dialect.name = 'sqlite'

        result = guid.load_dialect_impl(mock_dialect)

        assert result is not None


class TestExampleModelConstraints:
    """Test ExampleModel table constraints."""

    def test_unique_constraint_exists(self) -> None:
        """Test that unique constraint on name exists."""
        constraints = ExampleModel.__table_args__

        assert len(constraints) > 0
        assert any('name' in str(c) for c in constraints)
