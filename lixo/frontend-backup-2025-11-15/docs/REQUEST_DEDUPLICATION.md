# Request Deduplication

## 🎯 Purpose

Prevent duplicate API requests from being sent when multiple components request the same data simultaneously.

**DOUTRINA VÉRTICE - GAP #10 (P2)**
**Status: ✅ ALREADY IMPLEMENTED via React Query**

## ✅ Built-in Solution

React Query **automatically deduplicates requests** without any additional configuration required.

### How It Works

When multiple components mount and request the same query simultaneously:

```tsx
// Component A
function ComponentA() {
  const { data } = useQuery({
    queryKey: ["scan", "123"],
    queryFn: () => fetchScan("123"),
  });
}

// Component B (mounts at same time)
function ComponentB() {
  const { data } = useQuery({
    queryKey: ["scan", "123"], // Same key!
    queryFn: () => fetchScan("123"),
  });
}

// Result: Only ONE network request is made! ✅
```

**What happens:**

1. Component A mounts → Triggers query with key `['scan', '123']`
2. Component B mounts (same render cycle) → Also requests `['scan', '123']`
3. React Query detects identical `queryKey`
4. **Only one network request** is made
5. Both components receive the same data

## 🔍 Verification

You can verify this in browser DevTools:

```typescript
// Open React Query DevTools
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

function App() {
  return (
    <>
      <YourApp />
      <ReactQueryDevtools initialIsOpen={false} />
    </>
  );
}
```

**Test scenario:**

1. Open DevTools → Network tab
2. Mount multiple components requesting same data
3. Observe: Only **1 network request** despite multiple `useQuery` calls
4. Check React Query DevTools → See query state shared across components

## 📚 Examples

### Example 1: Multiple Components, Same Data

```tsx
function ScanDetails({ scanId }: { scanId: string }) {
  const { data: scan } = useQuery({
    queryKey: queryKeys.scan.detail(scanId),
    queryFn: () => fetchScan(scanId),
  });

  return <div>{scan?.status}</div>;
}

function ScanProgress({ scanId }: { scanId: string }) {
  const { data: scan } = useQuery({
    queryKey: queryKeys.scan.detail(scanId), // Same key!
    queryFn: () => fetchScan(scanId),
  });

  return <ProgressBar progress={scan?.progress} />;
}

function Page() {
  return (
    <>
      <ScanDetails scanId="123" /> {/* Request 1 */}
      <ScanProgress scanId="123" /> {/* Deduped! */}
    </>
  );
}

// Network tab: 1 request for /api/v1/scans/123 ✅
```

### Example 2: Rapid Successive Calls

```tsx
function SearchComponent() {
  const [query, setQuery] = useState("");

  const { data } = useQuery({
    queryKey: ["search", query],
    queryFn: () => fetchSearch(query),
    enabled: query.length > 0,
  });

  // User types fast: "test" → "test1" → "test" (back to "test")
  // React Query reuses cached result from first "test" query
  // No duplicate network request!

  return <input value={query} onChange={(e) => setQuery(e.target.value)} />;
}
```

### Example 3: Parallel Requests (Different Keys)

```tsx
function Dashboard() {
  // These run in parallel (different keys)
  const { data: scans } = useQuery({
    queryKey: queryKeys.scan.lists(),
    queryFn: fetchScans,
  });

  const { data: vulnerabilities } = useQuery({
    queryKey: queryKeys.vulnerability.lists(),
    queryFn: fetchVulnerabilities,
  });

  const { data: metrics } = useQuery({
    queryKey: queryKeys.metrics.dashboard(),
    queryFn: fetchMetrics,
  });

  // Result: 3 network requests (different queryKeys)
  // No deduplication (as expected)
}
```

## 🎯 Query Key Best Practices

For effective deduplication, use consistent query keys:

### ✅ Good: Centralized Query Keys

```typescript
// lib/queryClient.ts
export const queryKeys = {
  scan: {
    all: ["scans"] as const,
    detail: (id: string) => ["scans", "detail", id] as const,
  },
} as const;

// Component A
useQuery({
  queryKey: queryKeys.scan.detail("123"), // ['scans', 'detail', '123']
  queryFn: () => fetchScan("123"),
});

// Component B
useQuery({
  queryKey: queryKeys.scan.detail("123"), // Same key → deduped!
  queryFn: () => fetchScan("123"),
});
```

### ❌ Bad: Inconsistent Keys

```typescript
// Component A
useQuery({
  queryKey: ["scan", "123"], // Different key structure!
  queryFn: () => fetchScan("123"),
});

// Component B
useQuery({
  queryKey: ["scans", "detail", "123"], // Different → NOT deduped
  queryFn: () => fetchScan("123"),
});

// Result: 2 network requests (should be 1)
```

## 🔧 Advanced: Manual Deduplication Control

In rare cases, you may want to disable deduplication:

```typescript
// Force separate request (ignore cache)
const { data } = useQuery({
  queryKey: queryKeys.scan.detail(scanId),
  queryFn: fetchScan,
  staleTime: 0, // Always considered stale
  gcTime: 0, // Don't cache
});
```

## 📊 Performance Benefits

### Before React Query

```typescript
// Manual fetch (no deduplication)
useEffect(() => {
  fetch("/api/v1/scans/123"); // Component A
}, []);

useEffect(() => {
  fetch("/api/v1/scans/123"); // Component B → Duplicate!
}, []);

// Result: 2 requests ❌
```

### After React Query

```typescript
// Automatic deduplication
useQuery({ queryKey: ["scan", "123"], queryFn: fetchScan }); // A
useQuery({ queryKey: ["scan", "123"], queryFn: fetchScan }); // B

// Result: 1 request ✅
// Reduced network traffic by 50%!
```

## 🎯 Benefits

| Feature                     | Status                            |
| --------------------------- | --------------------------------- |
| **Automatic Deduplication** | ✅ Zero configuration             |
| **Shared State**            | ✅ All components get same data   |
| **Reduced Network**         | ✅ 50-90% fewer requests          |
| **Improved Performance**    | ✅ Faster page loads              |
| **Lower Server Load**       | ✅ Fewer backend requests         |
| **Battery Savings**         | ✅ Fewer mobile radio activations |

## 🚨 Common Mistakes

### 1. Different Query Keys for Same Data

```typescript
// ❌ BAD
const componentA = useQuery({ queryKey: ['scan', id], ... });
const componentB = useQuery({ queryKey: ['scans', id], ... });

// ✅ GOOD
const componentA = useQuery({ queryKey: queryKeys.scan.detail(id), ... });
const componentB = useQuery({ queryKey: queryKeys.scan.detail(id), ... });
```

### 2. Bypassing Cache Unnecessarily

```typescript
// ❌ BAD - Forces new request every time
const { data } = useQuery({
  queryKey: ["scan", id],
  queryFn: fetchScan,
  staleTime: 0, // Don't do this without reason!
});

// ✅ GOOD - Use default staleTime (5 minutes in our config)
const { data } = useQuery({
  queryKey: queryKeys.scan.detail(id),
  queryFn: fetchScan,
});
```

### 3. Unique Keys Per Component

```typescript
// ❌ BAD - Each component gets unique key
const componentId = useId(); // React 18 useId()
const { data } = useQuery({
  queryKey: ["scan", id, componentId], // Unique per component!
  queryFn: fetchScan,
});

// ✅ GOOD - Shared key
const { data } = useQuery({
  queryKey: queryKeys.scan.detail(id),
  queryFn: fetchScan,
});
```

## 🔍 Debugging

### Check for Duplicate Requests

```typescript
// Add request interceptor
typedApiClient.use({
  onRequest({ request }) {
    console.log("[API Request]", request.method, request.url);
    return request;
  },
});

// Watch console:
// Should see: "GET /api/v1/scans/123" only once
// If you see it twice → check queryKey consistency
```

### React Query DevTools

```tsx
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

<ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-right" />;

// DevTools shows:
// - Active queries
// - Query keys
// - Number of observers (components using the query)
// - Network status
```

## 📈 Monitoring

Track deduplication effectiveness:

```typescript
// Log query stats
const queryClient = useQueryClient();

useEffect(() => {
  const cache = queryClient.getQueryCache();

  console.log("Active Queries:", cache.getAll().length);
  console.log(
    "Query Keys:",
    cache.getAll().map((q) => q.queryKey),
  );
}, [queryClient]);
```

## 🎓 Summary

**GAP #10 (Request Deduplication):**

- ✅ **Status**: Already implemented via React Query
- ✅ **Configuration**: Zero config required
- ✅ **Benefit**: 50-90% reduction in duplicate requests
- ✅ **Maintenance**: Use centralized `queryKeys` factory
- ✅ **Monitoring**: React Query DevTools + Network tab

**No additional code needed.** Just follow query key best practices.

---

**DOUTRINA VÉRTICE - GAP #10 (P2)**
**Following Boris Cherny: "Don't reinvent built-in features"**
**Soli Deo Gloria** 🙏
