"""
Cursor-Based Pagination Models

DOUTRINA VÉRTICE - GAP #15 (P2)
Cursor-based pagination for scalable, consistent results

Following Boris Cherny's principle: "Pagination should be predictable"
"""

import base64
import json
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

T = TypeVar('T')


# ============================================================================
# PAGINATION MODELS
# ============================================================================

class PageInfo(BaseModel):
    """
    Pagination metadata.

    Provides information about the current page and navigation options.
    """

    has_next_page: bool = Field(
        description="Whether there are more items after this page"
    )

    has_previous_page: bool = Field(
        description="Whether there are items before this page"
    )

    start_cursor: Optional[str] = Field(
        default=None,
        description="Cursor pointing to the first item in this page"
    )

    end_cursor: Optional[str] = Field(
        default=None,
        description="Cursor pointing to the last item in this page"
    )

    total_count: Optional[int] = Field(
        default=None,
        description="Total number of items (expensive to compute, optional)"
    )


class Edge(BaseModel, Generic[T]):
    """
    An edge in a cursor-based connection.

    Wraps an item with its cursor for navigation.
    """

    node: T = Field(
        description="The actual data item"
    )

    cursor: str = Field(
        description="Opaque cursor string for this item"
    )


class CursorPage(BaseModel, Generic[T]):
    """
    Cursor-based paginated response.

    Follows Relay Cursor Connection specification for consistency.

    Example:
        >>> page = CursorPage(
        ...     edges=[
        ...         Edge(node={"id": 1, "name": "Item 1"}, cursor="Y3Vyc29yOjE="),
        ...         Edge(node={"id": 2, "name": "Item 2"}, cursor="Y3Vyc29yOjI="),
        ...     ],
        ...     page_info=PageInfo(
        ...         has_next_page=True,
        ...         has_previous_page=False,
        ...         start_cursor="Y3Vyc29yOjE=",
        ...         end_cursor="Y3Vyc29yOjI="
        ...     )
        ... )
    """

    edges: List[Edge[T]] = Field(
        description="List of edges (items with cursors)"
    )

    page_info: PageInfo = Field(
        description="Pagination metadata"
    )

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class SimpleCursorPage(BaseModel, Generic[T]):
    """
    Simplified cursor-based pagination (without edges).

    Use this for simpler APIs that don't need full GraphQL-style connections.

    Example:
        >>> page = SimpleCursorPage(
        ...     items=[{"id": 1}, {"id": 2}],
        ...     next_cursor="Y3Vyc29yOjI=",
        ...     has_more=True
        ... )
    """

    items: List[T] = Field(
        description="List of items"
    )

    next_cursor: Optional[str] = Field(
        default=None,
        description="Cursor for fetching the next page (null if no more pages)"
    )

    previous_cursor: Optional[str] = Field(
        default=None,
        description="Cursor for fetching the previous page (null if first page)"
    )

    has_more: bool = Field(
        description="Whether there are more items after this page"
    )

    total_count: Optional[int] = Field(
        default=None,
        description="Total number of items (optional, expensive)"
    )


# ============================================================================
# CURSOR ENCODING/DECODING
# ============================================================================

def encode_cursor(data: Any) -> str:
    """
    Encode data into an opaque cursor string.

    Uses base64 encoding to make cursors opaque (clients shouldn't parse them).

    Args:
        data: Data to encode (typically ID or compound key)

    Returns:
        Base64-encoded cursor string

    Examples:
        >>> encode_cursor(123)
        'eyJpZCI6IDEyM30='

        >>> encode_cursor({"id": 123, "created_at": "2025-01-15T10:30:45Z"})
        'eyJpZCI6IDEyMywgImNyZWF0ZWRfYXQiOiAiMjAyNS0wMS0xNVQxMDozMDo0NVoifQ=='
    """
    # Convert data to JSON
    if isinstance(data, (int, str)):
        json_data = json.dumps({"id": data})
    else:
        json_data = json.dumps(data, default=str)

    # Encode to base64
    encoded = base64.b64encode(json_data.encode()).decode()

    return encoded


def decode_cursor(cursor: str) -> Any:
    """
    Decode cursor string back to data.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Decoded data

    Raises:
        ValueError: If cursor is invalid

    Examples:
        >>> decode_cursor('eyJpZCI6IDEyM30=')
        {'id': 123}

        >>> decode_cursor('invalid')
        ValueError: Invalid cursor
    """
    try:
        # Decode from base64
        decoded_bytes = base64.b64decode(cursor.encode())
        json_data = decoded_bytes.decode()

        # Parse JSON
        data = json.loads(json_data)

        # If simple ID wrapper, unwrap it
        if isinstance(data, dict) and len(data) == 1 and "id" in data:
            return data["id"]

        return data

    except Exception as e:
        raise ValueError(f"Invalid cursor: {cursor}") from e


# ============================================================================
# PAGINATION HELPERS
# ============================================================================

def create_cursor_page(
    items: List[T],
    limit: int,
    total_count: Optional[int] = None,
    cursor_field: str = "id",
) -> SimpleCursorPage[T]:
    """
    Create a SimpleCursorPage from a list of items.

    Automatically determines has_more by fetching limit+1 items
    and checking if there are more.

    Args:
        items: List of items (should be limit+1 to detect has_more)
        limit: Number of items per page
        total_count: Optional total count (expensive to compute)
        cursor_field: Field to use as cursor (default: "id")

    Returns:
        SimpleCursorPage with pagination metadata

    Example:
        >>> # Fetch limit + 1 to detect has_more
        >>> items = db.query(Scan).limit(limit + 1).all()
        >>> page = create_cursor_page(items, limit=10)
    """
    # Check if there are more items
    has_more = len(items) > limit

    # Trim to actual limit
    page_items = items[:limit] if has_more else items

    # Get cursors
    next_cursor = None
    previous_cursor = None

    if has_more and page_items:
        # Get last item's cursor field value
        last_item = page_items[-1]
        if isinstance(last_item, dict):
            cursor_value = last_item.get(cursor_field)
        else:
            cursor_value = getattr(last_item, cursor_field, None)

        if cursor_value is not None:
            next_cursor = encode_cursor(cursor_value)

    return SimpleCursorPage(
        items=page_items,
        next_cursor=next_cursor,
        previous_cursor=previous_cursor,
        has_more=has_more,
        total_count=total_count,
    )


def create_relay_page(
    items: List[T],
    limit: int,
    total_count: Optional[int] = None,
    cursor_field: str = "id",
    has_previous: bool = False,
) -> CursorPage[T]:
    """
    Create a Relay-style CursorPage from items.

    Args:
        items: List of items (should be limit+1 to detect has_next)
        limit: Number of items per page
        total_count: Optional total count
        cursor_field: Field to use as cursor
        has_previous: Whether there's a previous page

    Returns:
        CursorPage with edges and page_info

    Example:
        >>> items = db.query(Scan).limit(limit + 1).all()
        >>> page = create_relay_page(items, limit=10)
    """
    # Check if there are more items
    has_next = len(items) > limit

    # Trim to actual limit
    page_items = items[:limit] if has_next else items

    # Create edges
    edges = []
    for item in page_items:
        if isinstance(item, dict):
            cursor_value = item.get(cursor_field)
        else:
            cursor_value = getattr(item, cursor_field, None)

        cursor = encode_cursor(cursor_value) if cursor_value is not None else ""
        edges.append(Edge(node=item, cursor=cursor))

    # Create page info
    start_cursor = edges[0].cursor if edges else None
    end_cursor = edges[-1].cursor if edges else None

    page_info = PageInfo(
        has_next_page=has_next,
        has_previous_page=has_previous,
        start_cursor=start_cursor,
        end_cursor=end_cursor,
        total_count=total_count,
    )

    return CursorPage(
        edges=edges,
        page_info=page_info,
    )


# ============================================================================
# QUERY PARAMETER MODELS
# ============================================================================

class CursorPaginationParams(BaseModel):
    """
    Query parameters for cursor-based pagination.

    Example:
        @app.get("/api/v1/scans")
        async def list_scans(pagination: CursorPaginationParams = Depends()):
            ...
    """

    first: Optional[int] = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of items to fetch (forward pagination)"
    )

    after: Optional[str] = Field(
        default=None,
        description="Cursor to fetch items after"
    )

    last: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Number of items to fetch (backward pagination)"
    )

    before: Optional[str] = Field(
        default=None,
        description="Cursor to fetch items before"
    )


class SimplePaginationParams(BaseModel):
    """
    Simplified pagination parameters.

    Example:
        @app.get("/api/v1/scans")
        async def list_scans(pagination: SimplePaginationParams = Depends()):
            ...
    """

    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of items per page"
    )

    cursor: Optional[str] = Field(
        default=None,
        description="Cursor for next page"
    )
