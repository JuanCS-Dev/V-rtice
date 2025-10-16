"""
Tests for Application Layer - DTOs

100% coverage required.
"""
import pytest
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import ValidationError

from service_template.application.dtos import (
    CreateEntityDTO,
    EntityDTO,
    PaginatedEntitiesDTO,
    UpdateEntityDTO,
)
from service_template.domain.entities import ExampleEntity


class TestCreateEntityDTO:
    """Tests for CreateEntityDTO."""

    def test_valid_minimal(self) -> None:
        """Test valid DTO with minimal fields."""
        dto = CreateEntityDTO(name="test")
        assert dto.name == "test"
        assert dto.description is None

    def test_valid_full(self) -> None:
        """Test valid DTO with all fields."""
        dto = CreateEntityDTO(name="test", description="desc")
        assert dto.name == "test"
        assert dto.description == "desc"

    def test_name_too_short(self) -> None:
        """Test name validation - too short."""
        with pytest.raises(ValidationError):
            CreateEntityDTO(name="")

    def test_name_too_long(self) -> None:
        """Test name validation - too long."""
        with pytest.raises(ValidationError):
            CreateEntityDTO(name="x" * 256)

    def test_description_too_long(self) -> None:
        """Test description validation - too long."""
        with pytest.raises(ValidationError):
            CreateEntityDTO(name="test", description="x" * 1001)


class TestUpdateEntityDTO:
    """Tests for UpdateEntityDTO."""

    def test_valid_name_only(self) -> None:
        """Test valid DTO with name only."""
        dto = UpdateEntityDTO(name="test")
        assert dto.name == "test"
        assert dto.description is None

    def test_valid_description_only(self) -> None:
        """Test valid DTO with description only."""
        dto = UpdateEntityDTO(description="desc")
        assert dto.name is None
        assert dto.description == "desc"

    def test_valid_both(self) -> None:
        """Test valid DTO with both fields."""
        dto = UpdateEntityDTO(name="test", description="desc")
        assert dto.name == "test"
        assert dto.description == "desc"

    def test_valid_neither(self) -> None:
        """Test valid DTO with no fields (all optional)."""
        dto = UpdateEntityDTO()
        assert dto.name is None
        assert dto.description is None

    def test_name_too_short(self) -> None:
        """Test name validation - too short."""
        with pytest.raises(ValidationError):
            UpdateEntityDTO(name="")

    def test_name_too_long(self) -> None:
        """Test name validation - too long."""
        with pytest.raises(ValidationError):
            UpdateEntityDTO(name="x" * 256)

    def test_description_too_long(self) -> None:
        """Test description validation - too long."""
        with pytest.raises(ValidationError):
            UpdateEntityDTO(description="x" * 1001)


class TestEntityDTO:
    """Tests for EntityDTO."""

    def test_from_entity(self) -> None:
        """Test creating DTO from entity."""
        entity = ExampleEntity(
            name="test",
            description="desc",
            status="active",
            extra_data={"key": "value"}
        )
        
        dto = EntityDTO.model_validate(entity)
        
        assert dto.id == entity.id
        assert dto.name == "test"
        assert dto.description == "desc"
        assert dto.status == "active"
        assert dto.extra_data == {"key": "value"}
        assert isinstance(dto.created_at, datetime)
        assert isinstance(dto.updated_at, datetime)

    def test_from_entity_no_description(self) -> None:
        """Test creating DTO from entity without description."""
        entity = ExampleEntity(name="test")
        
        dto = EntityDTO.model_validate(entity)
        
        assert dto.name == "test"
        assert dto.description is None


class TestPaginatedEntitiesDTO:
    """Tests for PaginatedEntitiesDTO."""

    def test_creation(self) -> None:
        """Test creating paginated response."""
        entities = [
            ExampleEntity(name="test1"),
            ExampleEntity(name="test2"),
        ]
        entity_dtos = [EntityDTO.model_validate(e) for e in entities]
        
        dto = PaginatedEntitiesDTO(
            items=entity_dtos,
            total=50,
            limit=10,
            offset=20
        )
        
        assert len(dto.items) == 2
        assert dto.total == 50
        assert dto.limit == 10
        assert dto.offset == 20

    def test_empty_items(self) -> None:
        """Test paginated response with no items."""
        dto = PaginatedEntitiesDTO(
            items=[],
            total=0,
            limit=100,
            offset=0
        )
        
        assert dto.items == []
        assert dto.total == 0
