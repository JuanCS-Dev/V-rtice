/**
 * Mutation Persistence Examples
 *
 * DOUTRINA VÉRTICE - GAP #9 (P1)
 * Complete examples of offline-first mutation persistence
 *
 * Following Boris Cherny's principle: "Examples are executable documentation"
 */

import React, { useState } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createQueryClient, queryKeys, mutationKeys } from '../queryClient';
import { createIDBPersister, persistOptions } from '../queryPersister';
import {
  useOnlineStatus,
  useMutationQueue,
  useOfflineQueue,
  useAutoRetryOnReconnect,
} from '../offlineQueue';

// ============================================================================
// Example 1: Basic Persistence Setup
// ============================================================================

/**
 * App root with persistence enabled
 *
 * This is the recommended setup for production apps
 */
export function AppWithPersistence() {
  const queryClient = createQueryClient();
  const persister = createIDBPersister();

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

  return (
    <div>
      <NetworkStatusBanner />
      <OfflineQueueIndicator />
      <YourComponents />
    </div>
  );
}

// ============================================================================
// Example 2: Network Status Indicator
// ============================================================================

/**
 * Show online/offline status to user
 */
function NetworkStatusBanner() {
  const isOnline = useOnlineStatus();

  if (isOnline) return null;

  return (
    <div
      style={{
        background: '#f59e0b',
        color: 'white',
        padding: '0.75rem',
        textAlign: 'center',
      }}
    >
      ⚠️ You are offline. Changes will be saved and synced when you reconnect.
    </div>
  );
}

// ============================================================================
// Example 3: Offline Queue Indicator
// ============================================================================

/**
 * Show pending mutations count
 */
function OfflineQueueIndicator() {
  const { pendingCount, hasPending, retryAll, clearQueue } = useOfflineQueue();
  const isOnline = useOnlineStatus();

  if (!hasPending) return null;

  return (
    <div
      style={{
        background: '#3b82f6',
        color: 'white',
        padding: '1rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <span>
        📦 {pendingCount} action{pendingCount > 1 ? 's' : ''} queued
        {!isOnline && ' - will sync when online'}
      </span>

      <div style={{ display: 'flex', gap: '0.5rem' }}>
        {isOnline && (
          <button
            onClick={retryAll}
            style={{
              background: 'white',
              color: '#3b82f6',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              cursor: 'pointer',
            }}
          >
            Retry All
          </button>
        )}

        <button
          onClick={clearQueue}
          style={{
            background: 'transparent',
            color: 'white',
            border: '1px solid white',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            cursor: 'pointer',
          }}
        >
          Clear Queue
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// Example 4: Mutation with Offline Support
// ============================================================================

interface ScanRequest {
  target: string;
  scanType: 'quick' | 'full' | 'custom';
}

/**
 * Mutation that works offline
 *
 * The mutation will be queued when offline and automatically
 * retried when connection is restored
 */
function StartScanButton() {
  const queryClient = useQueryClient();
  const isOnline = useOnlineStatus();

  const startScanMutation = useMutation({
    mutationKey: mutationKeys.scan.start,
    mutationFn: async (data: ScanRequest) => {
      const response = await fetch('http://localhost:8000/api/v1/scan/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to start scan');
      }

      return response.json();
    },

    // Optimistic update
    onMutate: async (newScan) => {
      console.log('Starting scan (optimistic):', newScan);

      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: queryKeys.scan.all });

      // Snapshot previous value
      const previousScans = queryClient.getQueryData(queryKeys.scan.lists());

      // Optimistically update
      queryClient.setQueryData(queryKeys.scan.lists(), (old: any) => {
        return {
          ...old,
          scans: [
            ...(old?.scans || []),
            {
              id: 'temp-' + Date.now(),
              ...newScan,
              status: 'pending',
              created_at: new Date().toISOString(),
            },
          ],
        };
      });

      return { previousScans };
    },

    // Rollback on error
    onError: (_error, _variables, context) => {
      if (context?.previousScans) {
        queryClient.setQueryData(queryKeys.scan.lists(), context.previousScans);
      }
    },

    // Refetch on success
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.scan.all });
    },
  });

  const handleStartScan = () => {
    startScanMutation.mutate({
      target: '192.168.1.1',
      scanType: 'quick',
    });
  };

  return (
    <div>
      <button
        onClick={handleStartScan}
        disabled={startScanMutation.isPending}
        style={{
          background: isOnline ? '#10b981' : '#6b7280',
          color: 'white',
          padding: '0.75rem 1.5rem',
          border: 'none',
          borderRadius: '0.375rem',
          cursor: startScanMutation.isPending ? 'not-allowed' : 'pointer',
        }}
      >
        {startScanMutation.isPending ? 'Starting...' : 'Start Scan'}
      </button>

      {!isOnline && (
        <p style={{ color: '#6b7280', marginTop: '0.5rem', fontSize: '0.875rem' }}>
          Scan will start automatically when you reconnect
        </p>
      )}

      {startScanMutation.isError && (
        <p style={{ color: '#ef4444', marginTop: '0.5rem' }}>
          Error: {(startScanMutation.error as Error).message}
        </p>
      )}
    </div>
  );
}

// ============================================================================
// Example 5: Detailed Mutation Queue View
// ============================================================================

/**
 * Admin panel showing all pending mutations
 */
function MutationQueuePanel() {
  const pendingMutations = useMutationQueue();
  const isOnline = useOnlineStatus();

  if (pendingMutations.length === 0) {
    return (
      <div style={{ padding: '1rem', color: '#6b7280' }}>
        No pending mutations
      </div>
    );
  }

  return (
    <div style={{ padding: '1rem' }}>
      <h3 style={{ marginBottom: '1rem' }}>
        Pending Mutations ({pendingMutations.length})
      </h3>

      {pendingMutations.map((mutation, index) => (
        <div
          key={index}
          style={{
            border: '1px solid #e5e7eb',
            borderRadius: '0.375rem',
            padding: '1rem',
            marginBottom: '0.5rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>
              <strong>{mutation.mutationKey.join(' / ')}</strong>
            </span>
            <span
              style={{
                background:
                  mutation.status === 'error' ? '#fecaca' : '#dbeafe',
                color: mutation.status === 'error' ? '#991b1b' : '#1e40af',
                padding: '0.25rem 0.5rem',
                borderRadius: '0.25rem',
                fontSize: '0.75rem',
              }}
            >
              {mutation.status}
            </span>
          </div>

          {mutation.error && (
            <p style={{ color: '#ef4444', marginTop: '0.5rem', fontSize: '0.875rem' }}>
              {mutation.error.message}
            </p>
          )}

          <p style={{ color: '#6b7280', fontSize: '0.875rem', marginTop: '0.5rem' }}>
            Queued at: {new Date(mutation.timestamp).toLocaleString()}
          </p>
        </div>
      ))}

      {!isOnline && (
        <p
          style={{
            background: '#fef3c7',
            color: '#92400e',
            padding: '0.75rem',
            borderRadius: '0.375rem',
            marginTop: '1rem',
          }}
        >
          ℹ️ Mutations will automatically retry when connection is restored
        </p>
      )}
    </div>
  );
}

// ============================================================================
// Example 6: Manual Persistence Control
// ============================================================================

/**
 * Admin controls for managing persistence
 */
function PersistenceControls() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState('');

  const handleClearCache = async () => {
    queryClient.clear();
    setStatus('Cache cleared');
    setTimeout(() => setStatus(''), 2000);
  };

  const handleClearMutations = () => {
    queryClient.getMutationCache().clear();
    setStatus('Mutation queue cleared');
    setTimeout(() => setStatus(''), 2000);
  };

  return (
    <div style={{ padding: '1rem', border: '1px solid #e5e7eb', borderRadius: '0.375rem' }}>
      <h3 style={{ marginBottom: '1rem' }}>Persistence Controls</h3>

      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button
          onClick={handleClearCache}
          style={{
            background: '#f3f4f6',
            border: '1px solid #d1d5db',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            cursor: 'pointer',
          }}
        >
          Clear Query Cache
        </button>

        <button
          onClick={handleClearMutations}
          style={{
            background: '#f3f4f6',
            border: '1px solid #d1d5db',
            padding: '0.5rem 1rem',
            borderRadius: '0.25rem',
            cursor: 'pointer',
          }}
        >
          Clear Mutation Queue
        </button>
      </div>

      {status && (
        <p style={{ color: '#10b981', marginTop: '1rem', fontSize: '0.875rem' }}>
          ✓ {status}
        </p>
      )}
    </div>
  );
}

// ============================================================================
// Example 7: Complete Demo Component
// ============================================================================

/**
 * Complete demo showing all persistence features
 */
export function PersistenceDemo() {
  return (
    <AppWithPersistence />
  );
}

/**
 * Internal components for demo
 */
function YourComponents() {
  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '2rem' }}>Offline-First Mutation Persistence</h1>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ marginBottom: '1rem' }}>1. Try a Mutation</h2>
        <StartScanButton />
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ marginBottom: '1rem' }}>2. Mutation Queue</h2>
        <MutationQueuePanel />
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ marginBottom: '1rem' }}>3. Admin Controls</h2>
        <PersistenceControls />
      </section>

      <section
        style={{
          background: '#f3f4f6',
          padding: '1rem',
          borderRadius: '0.375rem',
          marginTop: '2rem',
        }}
      >
        <h3 style={{ marginBottom: '0.5rem' }}>Test Offline Behavior:</h3>
        <ol style={{ marginLeft: '1.5rem' }}>
          <li>Open DevTools → Network tab</li>
          <li>Click "Offline" checkbox</li>
          <li>Click "Start Scan" button</li>
          <li>Notice mutation is queued</li>
          <li>Uncheck "Offline"</li>
          <li>Watch mutation automatically retry and succeed</li>
        </ol>
      </section>
    </div>
  );
}
