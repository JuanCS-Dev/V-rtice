# Cursor-Based Pagination

## 🎯 Purpose

Scalable, consistent pagination using cursors instead of offset-based pagination.

**DOUTRINA VÉRTICE - GAP #15 (P2)**
**Following Boris Cherny: "Pagination should be predictable"**

## ❌ Problems with Offset-Based Pagination

```python
# ❌ Offset-based (problematic)
@app.get("/scans")
async def list_scans(offset: int = 0, limit: int = 50):
    return db.query(Scan).offset(offset).limit(limit).all()
```

**Problems:**
1. **Performance**: `OFFSET 10000` scans and discards 10,000 rows
2. **Inconsistent Results**: If items are inserted/deleted during pagination, pages shift
3. **Can't Jump**: Hard to implement "load more" without tracking offset
4. **Database Load**: Large offsets are expensive

**Example of inconsistency:**
```
Page 1 (offset=0): Items 1, 2, 3, 4, 5
[New item inserted at position 1]
Page 2 (offset=5): Items 6, 7, 8, 9, 10  ← Skipped item!
```

## ✅ Cursor-Based Solution

```python
# ✅ Cursor-based (scalable)
@app.get("/scans")
async def list_scans(cursor: Optional[str] = None, limit: int = 50):
    query = db.query(Scan)

    if cursor:
        last_id = decode_cursor(cursor)
        query = query.filter(Scan.id > last_id)

    items = query.limit(limit + 1).all()
    return create_cursor_page(items, limit)
```

**Benefits:**
- **Fast**: Always uses index (WHERE id > X)
- **Consistent**: Same results even if data changes
- **Scalable**: Performance doesn't degrade with position
- **Predictable**: Clear navigation with cursors

## 📦 Usage

### Import Models

```python
from models.pagination import (
    SimpleCursorPage,         # Simple pagination response
    CursorPage,               # Relay-style response
    encode_cursor,            # Create cursor from ID
    decode_cursor,            # Parse cursor to ID
    create_cursor_page,       # Helper to build page
    create_relay_page,        # Helper for Relay format
    SimplePaginationParams,   # Query params
)
```

### Example 1: Simple Cursor Pagination

```python
from fastapi import FastAPI, Depends
from models.pagination import SimpleCursorPage, SimplePaginationParams, create_cursor_page, decode_cursor

app = FastAPI()

@app.get("/api/v1/scans", response_model=SimpleCursorPage[ScanModel])
async def list_scans(pagination: SimplePaginationParams = Depends()):
    """
    List scans with cursor-based pagination.

    Query params:
    - limit: Number of items (default: 50, max: 100)
    - cursor: Cursor for next page
    """
    query = db.query(Scan).order_by(Scan.id)

    # Apply cursor filter
    if pagination.cursor:
        last_id = decode_cursor(pagination.cursor)
        query = query.filter(Scan.id > last_id)

    # Fetch limit + 1 to detect if there are more items
    items = query.limit(pagination.limit + 1).all()

    # Create paginated response
    return create_cursor_page(items, limit=pagination.limit)
```

**Response:**
```json
{
  "items": [
    {"id": 1, "target": "example.com", "status": "completed"},
    {"id": 2, "target": "test.com", "status": "running"}
  ],
  "next_cursor": "eyJpZCI6IDJ9",
  "previous_cursor": null,
  "has_more": true,
  "total_count": null
}
```

**Client usage:**
```typescript
// First page
const page1 = await fetch('/api/v1/scans?limit=50');
const data1 = await page1.json();

// Next page
if (data1.has_more) {
  const page2 = await fetch(`/api/v1/scans?limit=50&cursor=${data1.next_cursor}`);
}
```

### Example 2: Relay-Style Pagination (GraphQL-like)

```python
from models.pagination import CursorPage, CursorPaginationParams, create_relay_page, decode_cursor

@app.get("/api/v1/vulnerabilities", response_model=CursorPage[VulnModel])
async def list_vulnerabilities(params: CursorPaginationParams = Depends()):
    """
    List vulnerabilities with Relay-style pagination.

    Query params:
    - first: Number of items to fetch forward (default: 50)
    - after: Cursor to fetch items after
    - last: Number of items to fetch backward
    - before: Cursor to fetch items before
    """
    query = db.query(Vulnerability).order_by(Vulnerability.id)

    # Forward pagination (after cursor)
    if params.after:
        last_id = decode_cursor(params.after)
        query = query.filter(Vulnerability.id > last_id)

    # Backward pagination (before cursor)
    if params.before:
        first_id = decode_cursor(params.before)
        query = query.filter(Vulnerability.id < first_id).order_by(Vulnerability.id.desc())

    limit = params.first or params.last or 50
    items = query.limit(limit + 1).all()

    # Reverse if backward pagination
    if params.before:
        items = items[::-1]

    has_previous = params.after is not None

    return create_relay_page(items, limit=limit, has_previous=has_previous)
```

**Response:**
```json
{
  "edges": [
    {
      "node": {"id": 1, "severity": "high", "cve": "CVE-2024-1234"},
      "cursor": "Y3Vyc29yOjE="
    },
    {
      "node": {"id": 2, "severity": "medium", "cve": "CVE-2024-5678"},
      "cursor": "Y3Vyc29yOjI="
    }
  ],
  "page_info": {
    "has_next_page": true,
    "has_previous_page": false,
    "start_cursor": "Y3Vyc29yOjE=",
    "end_cursor": "Y3Vyc29yOjI=",
    "total_count": null
  }
}
```

### Example 3: Compound Cursor (Multi-Field Sorting)

```python
from models.pagination import encode_cursor, decode_cursor

@app.get("/api/v1/events")
async def list_events(cursor: Optional[str] = None, limit: int = 50):
    """
    List events sorted by created_at DESC, then id DESC.

    Uses compound cursor: {"created_at": "...", "id": ...}
    """
    query = db.query(Event).order_by(Event.created_at.desc(), Event.id.desc())

    if cursor:
        cursor_data = decode_cursor(cursor)
        last_created = cursor_data["created_at"]
        last_id = cursor_data["id"]

        # Filter: (created_at < last_created) OR (created_at = last_created AND id < last_id)
        query = query.filter(
            or_(
                Event.created_at < last_created,
                and_(
                    Event.created_at == last_created,
                    Event.id < last_id
                )
            )
        )

    items = query.limit(limit + 1).all()
    has_more = len(items) > limit
    page_items = items[:limit]

    # Create next cursor from last item
    next_cursor = None
    if has_more and page_items:
        last_item = page_items[-1]
        next_cursor = encode_cursor({
            "created_at": last_item.created_at.isoformat(),
            "id": last_item.id
        })

    return {
        "items": page_items,
        "next_cursor": next_cursor,
        "has_more": has_more
    }
```

### Example 4: With Total Count (Expensive)

```python
@app.get("/api/v1/scans")
async def list_scans_with_count(
    cursor: Optional[str] = None,
    limit: int = 50,
    include_total: bool = False
):
    """
    List scans with optional total count.

    ⚠️ include_total=true is expensive (COUNT query)
    """
    query = db.query(Scan).order_by(Scan.id)

    # Get total count if requested
    total_count = None
    if include_total:
        total_count = query.count()  # Expensive!

    # Apply cursor
    if cursor:
        last_id = decode_cursor(cursor)
        query = query.filter(Scan.id > last_id)

    items = query.limit(limit + 1).all()

    return create_cursor_page(
        items,
        limit=limit,
        total_count=total_count
    )
```

## 🎯 Best Practices

### 1. Always Order By Unique Field

```python
# ❌ BAD - Non-unique ordering
query.order_by(Scan.status)  # Multiple scans can have same status

# ✅ GOOD - Unique ordering (or add tiebreaker)
query.order_by(Scan.created_at.desc(), Scan.id.desc())
```

### 2. Always Fetch limit + 1

```python
# ❌ BAD - Can't detect if there are more items
items = query.limit(limit).all()

# ✅ GOOD - Fetch one extra to detect has_more
items = query.limit(limit + 1).all()
has_more = len(items) > limit
page_items = items[:limit]
```

### 3. Use Indexed Fields for Cursor

```python
# ❌ BAD - Cursor on unindexed field
query.filter(Scan.target > cursor_value)  # Slow!

# ✅ GOOD - Cursor on indexed field (e.g., primary key)
query.filter(Scan.id > cursor_id)  # Fast!
```

### 4. Don't Include Total Count by Default

```python
# ❌ BAD - Always include total_count
total = query.count()  # Expensive COUNT(*) query

# ✅ GOOD - Make total_count optional
total = query.count() if include_total else None
```

### 5. Opaque Cursors

```python
# ❌ BAD - Expose internal IDs directly
return {"next_cursor": str(last_id)}  # Client can manipulate!

# ✅ GOOD - Use opaque base64-encoded cursors
return {"next_cursor": encode_cursor(last_id)}  # Clients can't parse
```

## 📊 Performance Comparison

### Offset-Based (Slow)

```sql
-- Page 1 (fast)
SELECT * FROM scans ORDER BY id LIMIT 50 OFFSET 0;
-- Scans: 50 rows

-- Page 100 (slow!)
SELECT * FROM scans ORDER BY id LIMIT 50 OFFSET 4950;
-- Scans: 4950 rows, returns 50 rows
```

### Cursor-Based (Fast)

```sql
-- Page 1 (fast)
SELECT * FROM scans ORDER BY id LIMIT 50;
-- Scans: 50 rows

-- Page 100 (still fast!)
SELECT * FROM scans WHERE id > 4950 ORDER BY id LIMIT 50;
-- Scans: 50 rows (uses index!)
```

**Benchmark (1M rows):**
| Method | Page 1 | Page 100 | Page 10000 |
|--------|--------|----------|------------|
| Offset | 5ms | 50ms | 2000ms |
| Cursor | 5ms | 5ms | 5ms |

## 🔍 Frontend Integration

### React Query + Infinite Scroll

```typescript
import { useInfiniteQuery } from '@tanstack/react-query';

function useScans() {
  return useInfiniteQuery({
    queryKey: ['scans'],
    queryFn: async ({ pageParam }) => {
      const url = pageParam
        ? `/api/v1/scans?cursor=${pageParam}`
        : '/api/v1/scans';

      const response = await fetch(url);
      return response.json();
    },
    getNextPageParam: (lastPage) => {
      // Return next cursor if has_more
      return lastPage.has_more ? lastPage.next_cursor : undefined;
    },
  });
}

function ScanList() {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useScans();

  return (
    <div>
      {data?.pages.map((page) => (
        page.items.map((scan) => <ScanCard key={scan.id} scan={scan} />)
      ))}

      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

### Load More Button

```typescript
async function loadMore() {
  if (!currentPage.has_more) return;

  const nextPage = await fetch(
    `/api/v1/scans?cursor=${currentPage.next_cursor}`
  );
  const data = await nextPage.json();

  // Append to existing items
  setItems([...items, ...data.items]);
  setCurrentPage(data);
}
```

## 🧪 Testing

### Run Tests

```bash
cd backend/api_gateway
pytest tests/test_pagination.py -v
```

### Test Coverage

```bash
pytest tests/test_pagination.py --cov=models.pagination --cov-report=html
```

### Integration Test Example

```python
def test_pagination_integration(client, db_session):
    """Test full pagination flow."""
    # Create test data
    for i in range(25):
        scan = Scan(target=f"example{i}.com")
        db_session.add(scan)
    db_session.commit()

    # Page 1
    response = client.get("/api/v1/scans?limit=10")
    assert response.status_code == 200

    page1 = response.json()
    assert len(page1["items"]) == 10
    assert page1["has_more"] is True

    # Page 2
    response = client.get(f"/api/v1/scans?limit=10&cursor={page1['next_cursor']}")
    page2 = response.json()
    assert len(page2["items"]) == 10

    # Page 3 (last page)
    response = client.get(f"/api/v1/scans?limit=10&cursor={page2['next_cursor']}")
    page3 = response.json()
    assert len(page3["items"]) == 5
    assert page3["has_more"] is False
```

## 🚨 Common Mistakes

### 1. Forgetting to Order By Unique Field

```python
# ❌ Will have duplicate/missing items
query.order_by(Scan.status)

# ✅ Add unique tiebreaker
query.order_by(Scan.status, Scan.id)
```

### 2. Not Handling Empty Cursors

```python
# ❌ Will crash on invalid cursor
last_id = decode_cursor(cursor)  # ValueError if cursor invalid

# ✅ Handle errors
try:
    last_id = decode_cursor(cursor)
except ValueError:
    raise HTTPException(400, "Invalid cursor")
```

### 3. Exposing Raw IDs as Cursors

```python
# ❌ Clients can manipulate
return {"next_cursor": str(last_id)}

# ✅ Use opaque encoding
return {"next_cursor": encode_cursor(last_id)}
```

### 4. Inconsistent Ordering

```python
# ❌ Different ordering in different requests
query.order_by(Scan.created_at)  # Sometimes ASC, sometimes DESC

# ✅ Consistent ordering
query.order_by(Scan.created_at.desc(), Scan.id.desc())
```

## 📖 API Reference

### `encode_cursor(data: Any) -> str`

Encode data into opaque base64 cursor.

**Returns**: Base64-encoded cursor string

### `decode_cursor(cursor: str) -> Any`

Decode cursor back to data.

**Raises**: `ValueError` if cursor is invalid

### `create_cursor_page(items, limit, total_count=None, cursor_field='id')`

Create `SimpleCursorPage` from items.

**Parameters**:
- `items`: List of items (should be limit+1)
- `limit`: Number of items per page
- `total_count`: Optional total count
- `cursor_field`: Field to use as cursor

**Returns**: `SimpleCursorPage[T]`

### `create_relay_page(items, limit, total_count=None, cursor_field='id', has_previous=False)`

Create Relay-style `CursorPage` from items.

**Returns**: `CursorPage[T]`

## 🔗 Related

- [Relay Cursor Connections Spec](https://relay.dev/graphql/connections.htm)
- [GraphQL Pagination Best Practices](https://graphql.org/learn/pagination/)
- [Why Cursor Pagination](https://www.sitepoint.com/paginating-real-time-data-cursor-based-pagination/)

---

**DOUTRINA VÉRTICE - GAP #15 (P2)**
**Following Boris Cherny: "Pagination should be predictable"**
**Soli Deo Gloria** 🙏
