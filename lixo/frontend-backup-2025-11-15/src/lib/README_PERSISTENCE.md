# Mutation Persistence & Offline Queue

## 🎯 Purpose

Offline-first architecture with mutation persistence using IndexedDB. User actions survive page reloads and network failures.

**DOUTRINA VÉRTICE - GAP #9 (P1)**
**Following Boris Cherny: "State should survive failures"**

## 🚀 Features

✅ **Persist Mutations** - Queued mutations survive page reload
✅ **Offline Queue** - Actions queued when offline, auto-retry when online
✅ **Optimistic Updates** - Instant UI feedback, rollback on error
✅ **Auto-Retry** - Exponential backoff for failed mutations
✅ **Online/Offline Detection** - Real-time network status monitoring
✅ **IndexedDB Storage** - Browser-native persistent storage

## 📦 Setup

### 1. Install Dependencies

```bash
npm install @tanstack/react-query-persist-client idb-keyval
```

### 2. Wrap App with Persistence Provider

```tsx
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { createQueryClient } from "@/lib/queryClient";
import { createIDBPersister, persistOptions } from "@/lib/queryPersister";
import { useAutoRetryOnReconnect } from "@/lib/offlineQueue";

const queryClient = createQueryClient();
const persister = createIDBPersister();

function App() {
  return (
    <PersistQueryClientProvider
      client={queryClient}
      persistOptions={{ persister, ...persistOptions }}
    >
      <AppContent />
    </PersistQueryClientProvider>
  );
}

function AppContent() {
  // Enable auto-retry when connection restored
  useAutoRetryOnReconnect();

  return <YourApp />;
}
```

## 🔄 How It Works

### Architecture

```
┌──────────────┐
│  User Action │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ useMutation()        │
│ - mutationKey set    │
│ - networkMode:       │
│   'offlineFirst'     │
└──────┬───────────────┘
       │
       ▼
    Online?
       │
  ┌────┴────┐
  │         │
YES        NO
  │         │
  │         ▼
  │    ┌────────────────┐
  │    │ Queue Mutation │
  │    │ (IndexedDB)    │
  │    └────────────────┘
  │         │
  │         ▼
  │    Wait for online
  │         │
  ▼         ▼
┌────────────────────┐
│ Execute Mutation   │
└──────┬─────────────┘
       │
       ▼
   Success?
       │
  ┌────┴────┐
  │         │
YES        NO
  │         │
  │         ▼
  │    ┌─────────────┐
  │    │ Retry logic │
  │    │ (exp backoff)│
  │    └─────────────┘
  │         │
  ▼         ▼
┌────────────────────┐
│ Update Cache       │
│ (persist to IDB)   │
└────────────────────┘
```

### Persistence Flow

1. **Mutation Triggered** - User performs action (e.g., start scan)
2. **Queue Check** - Is user online?
   - **Online**: Execute immediately
   - **Offline**: Queue in IndexedDB
3. **State Persistence** - React Query state saved to IndexedDB
4. **Page Reload** - State restored from IndexedDB
5. **Online Detection** - `useAutoRetryOnReconnect()` detects connection
6. **Auto-Retry** - All queued mutations automatically retried

## 📚 Usage Examples

### Basic Mutation with Persistence

```tsx
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { mutationKeys, queryKeys } from "@/lib/queryClient";

function StartScanButton() {
  const queryClient = useQueryClient();

  const startScan = useMutation({
    // IMPORTANT: Set mutationKey for persistence
    mutationKey: mutationKeys.scan.start,

    mutationFn: async (data: ScanRequest) => {
      const response = await fetch("/api/v1/scan/start", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return response.json();
    },

    // Optimistic update
    onMutate: async (newScan) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.scan.all });

      const previousScans = queryClient.getQueryData(queryKeys.scan.lists());

      queryClient.setQueryData(queryKeys.scan.lists(), (old: any) => ({
        ...old,
        scans: [...(old?.scans || []), newScan],
      }));

      return { previousScans };
    },

    // Rollback on error
    onError: (_err, _vars, context) => {
      if (context?.previousScans) {
        queryClient.setQueryData(queryKeys.scan.lists(), context.previousScans);
      }
    },

    // Refetch on success
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.scan.all });
    },
  });

  return (
    <button onClick={() => startScan.mutate({ target: "192.168.1.1" })}>
      Start Scan
    </button>
  );
}
```

### Network Status Indicator

```tsx
import { useOnlineStatus } from "@/lib/offlineQueue";

function NetworkStatus() {
  const isOnline = useOnlineStatus();

  return (
    <div>
      {isOnline ? (
        <span style={{ color: "green" }}>✓ Online</span>
      ) : (
        <span style={{ color: "orange" }}>
          ⚠️ Offline - Changes will be queued
        </span>
      )}
    </div>
  );
}
```

### Offline Queue Display

```tsx
import { useMutationQueue } from "@/lib/offlineQueue";

function OfflineQueueBadge() {
  const pendingMutations = useMutationQueue();

  if (pendingMutations.length === 0) return null;

  return (
    <div style={{ background: "blue", color: "white", padding: "0.5rem" }}>
      📦 {pendingMutations.length} action(s) queued
    </div>
  );
}
```

### Queue Management

```tsx
import { useOfflineQueue } from "@/lib/offlineQueue";

function QueueControls() {
  const { pendingCount, retryAll, clearQueue, isOnline } = useOfflineQueue();

  return (
    <div>
      <p>{pendingCount} mutations pending</p>
      <button onClick={retryAll} disabled={!isOnline}>
        Retry All
      </button>
      <button onClick={clearQueue}>Clear Queue</button>
    </div>
  );
}
```

## 🔧 Configuration

### QueryClient Settings

```typescript
// src/lib/queryClient.ts

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      mutations: {
        // CRITICAL: Enable offline queue
        networkMode: "offlineFirst",

        // Retry failed mutations
        retry: shouldRetry,
        retryDelay: getRetryDelay,

        // Callbacks
        onError: (error) => console.error("Mutation failed:", error),
        onSuccess: () => console.info("Mutation succeeded"),
      },
    },
  });
}
```

### Retry Logic

```typescript
function shouldRetry(failureCount: number, error: any): boolean {
  // Max 3 retries
  if (failureCount >= 3) return false;

  // Don't retry client errors (4xx)
  if (error?.response?.status >= 400 && error?.response?.status < 500) {
    return false;
  }

  // Don't retry auth/validation errors
  const errorCode = error?.error_code;
  if (errorCode?.startsWith("AUTH_") || errorCode?.startsWith("VAL_")) {
    return false;
  }

  // Retry 5xx, network errors, timeouts
  return true;
}

function getRetryDelay(attemptIndex: number): number {
  // Exponential backoff: 1s, 2s, 4s (capped at 30s)
  return Math.min(1000 * Math.pow(2, attemptIndex), 30000);
}
```

### Persistence Settings

```typescript
// src/lib/queryPersister.ts

export const persistOptions = {
  maxAge: 1000 * 60 * 60 * 24 * 7, // 7 days
  buster: "", // Change to invalidate all cached data
};
```

## 🧪 Testing Offline Behavior

### Manual Testing

1. **Open DevTools** → Network tab
2. **Check "Offline"** checkbox
3. **Perform mutation** (e.g., click "Start Scan")
4. **Observe**:
   - Mutation queued (shown in UI)
   - Page still responsive
   - No error thrown
5. **Uncheck "Offline"**
6. **Watch**:
   - Mutation auto-retries
   - UI updates on success
   - Queue clears

### Programmatic Testing

```typescript
import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useMutation } from "@tanstack/react-query";
import { mutationKeys } from "@/lib/queryClient";

describe("Mutation Persistence", () => {
  it("should queue mutation when offline", async () => {
    // Simulate offline
    vi.spyOn(navigator, "onLine", "get").mockReturnValue(false);

    const { result } = renderHook(() =>
      useMutation({
        mutationKey: mutationKeys.scan.start,
        mutationFn: async () => {
          throw new Error("Network error");
        },
        networkMode: "offlineFirst",
      }),
    );

    result.current.mutate({ target: "192.168.1.1" });

    await waitFor(() => {
      expect(result.current.isPending).toBe(true);
    });

    // Mutation is queued, not failed
    expect(result.current.isError).toBe(false);
  });

  it("should retry when connection restored", async () => {
    // Test auto-retry on reconnect
    // (Implementation depends on test setup)
  });
});
```

## 🎯 Best Practices

### 1. Always Set `mutationKey`

```tsx
// ❌ BAD - Mutation won't be persisted
useMutation({
  mutationFn: startScan,
});

// ✅ GOOD - Mutation persisted
useMutation({
  mutationKey: mutationKeys.scan.start,
  mutationFn: startScan,
});
```

### 2. Use Optimistic Updates

```tsx
useMutation({
  mutationKey: mutationKeys.scan.start,
  mutationFn: startScan,

  // Optimistic update
  onMutate: async (newScan) => {
    // Cancel outgoing queries
    await queryClient.cancelQueries({ queryKey: queryKeys.scan.all });

    // Snapshot
    const previous = queryClient.getQueryData(queryKeys.scan.lists());

    // Update optimistically
    queryClient.setQueryData(queryKeys.scan.lists(), (old) => [
      ...old,
      newScan,
    ]);

    return { previous };
  },

  // Rollback on error
  onError: (_err, _vars, context) => {
    queryClient.setQueryData(queryKeys.scan.lists(), context.previous);
  },
});
```

### 3. Show Queue Status

```tsx
function App() {
  const { hasPending } = useOfflineQueue();
  const isOnline = useOnlineStatus();

  return (
    <>
      {!isOnline && <OfflineBanner />}
      {hasPending && <QueueIndicator />}
      <YourApp />
    </>
  );
}
```

### 4. Handle Errors Gracefully

```tsx
useMutation({
  mutationKey: mutationKeys.scan.start,
  mutationFn: startScan,

  onError: (error, variables, context) => {
    // Log for debugging
    console.error("[Mutation Error]", {
      error,
      variables,
      requestId: error.request_id,
    });

    // Show user-friendly message
    toast.error(handleApiError(error));

    // Rollback optimistic update
    if (context?.previousData) {
      queryClient.setQueryData(queryKey, context.previousData);
    }
  },
});
```

### 5. Clear Cache on Logout

```typescript
import { clearPersistedQueries } from "@/lib/queryPersister";

async function handleLogout() {
  // Clear persisted state
  await clearPersistedQueries();

  // Clear in-memory cache
  queryClient.clear();

  // Redirect to login
  window.location.href = "/login";
}
```

## 🔍 Debugging

### View Persisted Data

```javascript
// Open DevTools → Console
indexedDB.databases().then(console.log);

// Inspect keyval-store → VERTICE_REACT_QUERY_OFFLINE_CACHE
```

### Check Mutation State

```tsx
import { useMutationState } from "@tanstack/react-query";

function DebugPanel() {
  const mutations = useMutationState();

  return <pre>{JSON.stringify(mutations, null, 2)}</pre>;
}
```

### Monitor Network Events

```typescript
window.addEventListener("online", () => {
  console.log("🟢 Connection restored");
});

window.addEventListener("offline", () => {
  console.log("🔴 Connection lost");
});
```

## 🚨 Common Issues

### Issue: Mutations Not Persisting

**Cause**: Missing `mutationKey`

**Fix**:

```tsx
// ❌ Won't persist
useMutation({ mutationFn: doSomething });

// ✅ Will persist
useMutation({
  mutationKey: ["myMutation"],
  mutationFn: doSomething,
});
```

### Issue: Duplicate Mutations After Reload

**Cause**: Mutation succeeded but UI didn't update before reload

**Fix**: Use `onSuccess` to invalidate queries

```tsx
useMutation({
  mutationKey: mutationKeys.scan.start,
  mutationFn: startScan,
  onSuccess: () => {
    // Ensure UI reflects server state
    queryClient.invalidateQueries({ queryKey: queryKeys.scan.all });
  },
});
```

### Issue: Mutations Not Retrying

**Cause**: `networkMode` not set to `'offlineFirst'`

**Fix**: Set in QueryClient config (already done in `queryClient.ts`)

## 📖 API Reference

### `createIDBPersister()`

Creates IndexedDB persister for React Query.

**Returns**: `Persister`

### `createQueryClient()`

Creates configured QueryClient with offline support.

**Returns**: `QueryClient`

### `useOnlineStatus()`

Hook for online/offline detection.

**Returns**: `boolean` - Current online status

### `useMutationQueue()`

Hook for accessing queued mutations.

**Returns**: `PendingMutation[]` - Array of pending mutations

### `useOfflineQueue()`

Hook for managing mutation queue.

**Returns**: `{ pendingCount, hasPending, isOnline, clearQueue, retryAll }`

### `useAutoRetryOnReconnect()`

Hook for automatic retry when connection restored.

**Side Effects**: Resumes paused mutations on reconnect

## 🔗 Related

- [TanStack Query Docs](https://tanstack.com/query/latest)
- [Persistence & Offline](https://tanstack.com/query/latest/docs/react/plugins/persistQueryClient)
- [idb-keyval](https://github.com/jakearchibald/idb-keyval)
- [GAP #6: Error Handling](../utils/errorHandler.ts)

---

**DOUTRINA VÉRTICE - GAP #9 (P1)**
**Following Boris Cherny: "State should survive failures"**
**Soli Deo Gloria** 🙏
