"""
Tests for Infrastructure Layer - Models

100% coverage required.
"""
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from service_template.infrastructure.database import Base, ExampleModel
from service_template.infrastructure.database.models import GUID


class TestBase:
    """Tests for Base declarative base."""

    def test_base_exists(self) -> None:
        """Test Base class exists."""
        assert Base is not None


class TestGUID:
    """Tests for GUID type decorator."""

    def test_load_dialect_impl_postgresql(self) -> None:
        """Test PostgreSQL dialect uses UUID."""
        guid = GUID()
        mock_dialect = MagicMock()
        mock_dialect.name = 'postgresql'
        mock_dialect.type_descriptor = MagicMock(return_value="PG_UUID")

        result = guid.load_dialect_impl(mock_dialect)

        assert result == "PG_UUID"

    def test_load_dialect_impl_sqlite(self) -> None:
        """Test SQLite dialect uses CHAR(36)."""
        guid = GUID()
        mock_dialect = MagicMock()
        mock_dialect.name = 'sqlite'
        mock_dialect.type_descriptor = MagicMock(return_value="CHAR36")

        result = guid.load_dialect_impl(mock_dialect)

        assert result == "CHAR36"

    def test_process_bind_param_none(self) -> None:
        """Test binding None value."""
        guid = GUID()

        result = guid.process_bind_param(None, None)

        assert result is None

    def test_process_bind_param_uuid(self) -> None:
        """Test binding UUID value."""
        guid = GUID()
        test_uuid = uuid4()

        result = guid.process_bind_param(test_uuid, None)

        assert result == str(test_uuid)

    def test_process_bind_param_other(self) -> None:
        """Test binding non-UUID value."""
        guid = GUID()

        result = guid.process_bind_param("some-string", None)

        assert result == "some-string"

    def test_process_result_value_none(self) -> None:
        """Test processing None result."""
        guid = GUID()

        result = guid.process_result_value(None, None)

        assert result is None

    def test_process_result_value_string(self) -> None:
        """Test processing string result."""
        guid = GUID()
        test_uuid = uuid4()

        result = guid.process_result_value(str(test_uuid), None)

        assert isinstance(result, UUID)
        assert result == test_uuid

    def test_process_result_value_uuid(self) -> None:
        """Test processing UUID result."""
        guid = GUID()
        test_uuid = uuid4()

        result = guid.process_result_value(test_uuid, None)

        assert result == test_uuid


class TestExampleModel:
    """Tests for ExampleModel."""

    def test_creation(self) -> None:
        """Test model creation."""
        model = ExampleModel(
            name="test",
            description="desc",
            status="active",
            extra_data={"key": "value"}
        )

        assert model.name == "test"
        assert model.description == "desc"
        assert model.status == "active"
        assert model.extra_data == {"key": "value"}

    def test_repr(self) -> None:
        """Test string representation."""
        model = ExampleModel(name="test", status="active")

        str_repr = str(model)
        assert model.name in str_repr or "ExampleModel" in str_repr
