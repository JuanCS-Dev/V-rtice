"""
Tests for Infrastructure Layer - Models

100% coverage required.
"""
from uuid import uuid4

from service_template.infrastructure.models import Base, ExampleModel


class TestBase:
    """Tests for Base declarative base."""

    def test_base_exists(self) -> None:
        """Test Base class exists."""
        assert Base is not None


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
        entity_id = uuid4()
        model = ExampleModel(id=entity_id, name="test", status="active")
        
        repr_str = repr(model)
        
        assert "ExampleModel" in repr_str
        assert str(entity_id) in repr_str
        assert "test" in repr_str
        assert "active" in repr_str
