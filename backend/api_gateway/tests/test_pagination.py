"""
Tests for Cursor-Based Pagination

DOUTRINA VÉRTICE - GAP #15 (P2)
Tests for cursor-based pagination models and utilities

Following Boris Cherny: "Tests or it didn't happen"
"""

import pytest
import base64
import json
from pydantic import BaseModel

from models.pagination import (
    PageInfo,
    Edge,
    CursorPage,
    SimpleCursorPage,
    encode_cursor,
    decode_cursor,
    create_cursor_page,
    create_relay_page,
    CursorPaginationParams,
    SimplePaginationParams,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

class TestItem(BaseModel):
    """Test item model."""
    id: int
    name: str


@pytest.fixture
def sample_items():
    """Create sample items for testing."""
    return [
        TestItem(id=1, name="Item 1"),
        TestItem(id=2, name="Item 2"),
        TestItem(id=3, name="Item 3"),
        TestItem(id=4, name="Item 4"),
        TestItem(id=5, name="Item 5"),
    ]


# ============================================================================
# TESTS: encode_cursor / decode_cursor
# ============================================================================

def test_encode_cursor_with_simple_id():
    """Should encode simple ID into base64 cursor."""
    cursor = encode_cursor(123)

    # Should be base64
    assert isinstance(cursor, str)
    # Should be decodable
    decoded = base64.b64decode(cursor.encode()).decode()
    data = json.loads(decoded)
    assert data == {"id": 123}


def test_encode_cursor_with_string_id():
    """Should encode string ID."""
    cursor = encode_cursor("scan-123")

    decoded_data = decode_cursor(cursor)
    assert decoded_data == "scan-123"


def test_encode_cursor_with_compound_key():
    """Should encode compound keys."""
    cursor = encode_cursor({
        "id": 123,
        "created_at": "2025-01-15T10:30:45Z"
    })

    decoded_data = decode_cursor(cursor)
    assert decoded_data == {
        "id": 123,
        "created_at": "2025-01-15T10:30:45Z"
    }


def test_decode_cursor_with_valid_cursor():
    """Should decode valid cursor."""
    cursor = encode_cursor(456)

    result = decode_cursor(cursor)

    assert result == 456


def test_decode_cursor_unwraps_simple_id():
    """Should unwrap {"id": N} to just N."""
    # Manually create cursor with {"id": 789}
    data = json.dumps({"id": 789})
    cursor = base64.b64encode(data.encode()).decode()

    result = decode_cursor(cursor)

    assert result == 789  # Unwrapped


def test_decode_cursor_keeps_compound_keys():
    """Should not unwrap compound keys."""
    cursor = encode_cursor({"id": 123, "name": "test"})

    result = decode_cursor(cursor)

    assert result == {"id": 123, "name": "test"}


def test_decode_cursor_with_invalid_cursor():
    """Should raise ValueError for invalid cursor."""
    with pytest.raises(ValueError, match="Invalid cursor"):
        decode_cursor("invalid-not-base64!")


def test_decode_cursor_with_invalid_json():
    """Should raise ValueError for invalid JSON in cursor."""
    # Valid base64 but invalid JSON
    invalid = base64.b64encode(b"not-json").decode()

    with pytest.raises(ValueError, match="Invalid cursor"):
        decode_cursor(invalid)


def test_cursor_roundtrip():
    """Encoding and decoding should be idempotent."""
    original = {"id": 999, "timestamp": "2025-01-15T10:30:45Z"}

    cursor = encode_cursor(original)
    decoded = decode_cursor(cursor)

    assert decoded == original


# ============================================================================
# TESTS: PageInfo
# ============================================================================

def test_page_info_creation():
    """Should create PageInfo with all fields."""
    page_info = PageInfo(
        has_next_page=True,
        has_previous_page=False,
        start_cursor="cursor1",
        end_cursor="cursor2",
        total_count=100
    )

    assert page_info.has_next_page is True
    assert page_info.has_previous_page is False
    assert page_info.start_cursor == "cursor1"
    assert page_info.end_cursor == "cursor2"
    assert page_info.total_count == 100


def test_page_info_optional_fields():
    """Optional fields should default to None."""
    page_info = PageInfo(
        has_next_page=False,
        has_previous_page=False
    )

    assert page_info.start_cursor is None
    assert page_info.end_cursor is None
    assert page_info.total_count is None


# ============================================================================
# TESTS: Edge
# ============================================================================

def test_edge_creation():
    """Should create Edge with node and cursor."""
    item = TestItem(id=1, name="Test")
    edge = Edge(node=item, cursor="abc123")

    assert edge.node == item
    assert edge.cursor == "abc123"


# ============================================================================
# TESTS: SimpleCursorPage
# ============================================================================

def test_simple_cursor_page_creation(sample_items):
    """Should create SimpleCursorPage."""
    page = SimpleCursorPage(
        items=sample_items[:3],
        next_cursor="cursor123",
        previous_cursor=None,
        has_more=True,
        total_count=10
    )

    assert len(page.items) == 3
    assert page.next_cursor == "cursor123"
    assert page.previous_cursor is None
    assert page.has_more is True
    assert page.total_count == 10


def test_simple_cursor_page_serialization(sample_items):
    """Should serialize to JSON correctly."""
    page = SimpleCursorPage(
        items=sample_items[:2],
        next_cursor="next",
        has_more=False
    )

    json_data = page.model_dump()

    assert "items" in json_data
    assert "next_cursor" in json_data
    assert "has_more" in json_data
    assert json_data["has_more"] is False


# ============================================================================
# TESTS: CursorPage
# ============================================================================

def test_cursor_page_creation(sample_items):
    """Should create Relay-style CursorPage."""
    edges = [
        Edge(node=sample_items[0], cursor="c1"),
        Edge(node=sample_items[1], cursor="c2"),
    ]

    page_info = PageInfo(
        has_next_page=True,
        has_previous_page=False,
        start_cursor="c1",
        end_cursor="c2"
    )

    page = CursorPage(edges=edges, page_info=page_info)

    assert len(page.edges) == 2
    assert page.edges[0].cursor == "c1"
    assert page.page_info.has_next_page is True


# ============================================================================
# TESTS: create_cursor_page
# ============================================================================

def test_create_cursor_page_with_more_items(sample_items):
    """Should detect has_more when items > limit."""
    # Simulate fetching limit+1 (5 items, limit 3)
    page = create_cursor_page(sample_items, limit=3)

    assert len(page.items) == 3  # Trimmed to limit
    assert page.has_more is True
    assert page.next_cursor is not None


def test_create_cursor_page_without_more_items(sample_items):
    """Should set has_more=False when items <= limit."""
    # Only 3 items, limit 5
    page = create_cursor_page(sample_items[:3], limit=5)

    assert len(page.items) == 3
    assert page.has_more is False
    assert page.next_cursor is None


def test_create_cursor_page_next_cursor(sample_items):
    """Next cursor should be based on last item."""
    page = create_cursor_page(sample_items, limit=3)

    # Last item in page is items[2] (id=3)
    assert page.next_cursor is not None

    # Decode and verify
    decoded = decode_cursor(page.next_cursor)
    assert decoded == 3  # Last item's ID


def test_create_cursor_page_with_dict_items():
    """Should work with dict items."""
    dict_items = [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"},
        {"id": 3, "name": "C"},
        {"id": 4, "name": "D"},
    ]

    page = create_cursor_page(dict_items, limit=2)

    assert len(page.items) == 2
    assert page.has_more is True

    decoded = decode_cursor(page.next_cursor)
    assert decoded == 2


def test_create_cursor_page_with_total_count(sample_items):
    """Should include total_count if provided."""
    page = create_cursor_page(sample_items, limit=3, total_count=100)

    assert page.total_count == 100


def test_create_cursor_page_with_custom_cursor_field():
    """Should use custom cursor field."""
    items = [
        {"uuid": "a1", "name": "Item 1"},
        {"uuid": "a2", "name": "Item 2"},
        {"uuid": "a3", "name": "Item 3"},
    ]

    page = create_cursor_page(items, limit=2, cursor_field="uuid")

    decoded = decode_cursor(page.next_cursor)
    assert decoded == "a2"


def test_create_cursor_page_empty_list():
    """Should handle empty list."""
    page = create_cursor_page([], limit=10)

    assert len(page.items) == 0
    assert page.has_more is False
    assert page.next_cursor is None


# ============================================================================
# TESTS: create_relay_page
# ============================================================================

def test_create_relay_page_with_more_items(sample_items):
    """Should create Relay page with has_next_page=True."""
    page = create_relay_page(sample_items, limit=3)

    assert len(page.edges) == 3
    assert page.page_info.has_next_page is True
    assert page.page_info.has_previous_page is False


def test_create_relay_page_without_more_items(sample_items):
    """Should create Relay page with has_next_page=False."""
    page = create_relay_page(sample_items[:3], limit=5)

    assert len(page.edges) == 3
    assert page.page_info.has_next_page is False


def test_create_relay_page_cursors(sample_items):
    """Should set start_cursor and end_cursor correctly."""
    page = create_relay_page(sample_items[:3], limit=5)

    assert page.page_info.start_cursor is not None
    assert page.page_info.end_cursor is not None

    # Start cursor should be first item's ID
    start_id = decode_cursor(page.page_info.start_cursor)
    assert start_id == 1

    # End cursor should be last item's ID
    end_id = decode_cursor(page.page_info.end_cursor)
    assert end_id == 3


def test_create_relay_page_with_has_previous(sample_items):
    """Should set has_previous_page if provided."""
    page = create_relay_page(sample_items[:2], limit=5, has_previous=True)

    assert page.page_info.has_previous_page is True


def test_create_relay_page_edges_structure(sample_items):
    """Edges should contain node and cursor."""
    page = create_relay_page(sample_items[:2], limit=5)

    assert len(page.edges) == 2
    assert page.edges[0].node == sample_items[0]
    assert page.edges[0].cursor is not None
    assert page.edges[1].node == sample_items[1]


def test_create_relay_page_empty_list():
    """Should handle empty list."""
    page = create_relay_page([], limit=10)

    assert len(page.edges) == 0
    assert page.page_info.has_next_page is False
    assert page.page_info.start_cursor is None
    assert page.page_info.end_cursor is None


# ============================================================================
# TESTS: Pagination Params
# ============================================================================

def test_cursor_pagination_params_defaults():
    """Should have default values."""
    params = CursorPaginationParams()

    assert params.first == 50
    assert params.after is None
    assert params.last is None
    assert params.before is None


def test_cursor_pagination_params_custom_values():
    """Should accept custom values."""
    params = CursorPaginationParams(
        first=10,
        after="cursor123"
    )

    assert params.first == 10
    assert params.after == "cursor123"


def test_cursor_pagination_params_validation():
    """Should validate limit bounds."""
    # Min validation
    with pytest.raises(ValueError):
        CursorPaginationParams(first=0)

    # Max validation
    with pytest.raises(ValueError):
        CursorPaginationParams(first=101)


def test_simple_pagination_params_defaults():
    """Should have default values."""
    params = SimplePaginationParams()

    assert params.limit == 50
    assert params.cursor is None


def test_simple_pagination_params_custom_values():
    """Should accept custom values."""
    params = SimplePaginationParams(
        limit=25,
        cursor="next_page"
    )

    assert params.limit == 25
    assert params.cursor == "next_page"


def test_simple_pagination_params_validation():
    """Should validate limit bounds."""
    # Min validation
    with pytest.raises(ValueError):
        SimplePaginationParams(limit=0)

    # Max validation
    with pytest.raises(ValueError):
        SimplePaginationParams(limit=101)


# ============================================================================
# TESTS: Integration Scenarios
# ============================================================================

def test_pagination_full_cycle(sample_items):
    """Test full pagination cycle: first page → next page."""
    # First page (limit 2)
    page1 = create_cursor_page(sample_items, limit=2)

    assert len(page1.items) == 2
    assert page1.items[0].id == 1
    assert page1.items[1].id == 2
    assert page1.has_more is True

    # Get cursor for next page
    next_cursor = page1.next_cursor

    # Simulate fetching next page
    # (In real code, would use cursor to filter DB query)
    # For test, manually slice
    remaining_items = sample_items[2:]  # Items 3, 4, 5
    page2 = create_cursor_page(remaining_items, limit=2)

    assert len(page2.items) == 2
    assert page2.items[0].id == 3
    assert page2.items[1].id == 4
    assert page2.has_more is True


def test_pagination_last_page(sample_items):
    """Last page should have has_more=False."""
    # Get last page (items 5)
    last_items = sample_items[4:]
    page = create_cursor_page(last_items, limit=10)

    assert len(page.items) == 1
    assert page.items[0].id == 5
    assert page.has_more is False
    assert page.next_cursor is None
