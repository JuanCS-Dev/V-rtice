/**
 * Offensive Operations Store
 *
 * Zustand store for offensive dashboard state management
 * Centralizes red team operations state
 *
 * Features:
 * - Attack metrics tracking
 * - Execution history
 * - Active module management
 * - Real-time updates
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export const useOffensiveStore = create(
  devtools(
    persist(
      (set, get) => ({
        // State
        metrics: {
          activeScans: 0,
          exploitsFound: 0,
          targets: 0,
          c2Sessions: 0,
          networkScans: 0,
          payloadsGenerated: 0
        },
        executions: [],
        activeModule: 'network-scanner',
        loading: {
          metrics: true,
          executions: false,
          scanner: false
        },
        error: null,
        lastUpdate: null,
        
        // NEW: Offensive tools data
        scanResults: [],
        payloads: [],

        // Actions - Metrics
        setMetrics: (metrics) => set({
          metrics,
          lastUpdate: new Date().toISOString(),
          loading: { ...get().loading, metrics: false }
        }),

        updateMetric: (key, value) => set((state) => ({
          metrics: {
            ...state.metrics,
            [key]: value
          },
          lastUpdate: new Date().toISOString()
        })),

        incrementMetric: (key, amount = 1) => set((state) => ({
          metrics: {
            ...state.metrics,
            [key]: (state.metrics[key] || 0) + amount
          },
          lastUpdate: new Date().toISOString()
        })),

        // Actions - Executions
        addExecution: (execution) => set((state) => ({
          executions: [
            {
              ...execution,
              id: execution.id || `exec-${Date.now()}-${Math.random()}`,
              timestamp: execution.timestamp || new Date().toISOString(),
              status: execution.status || 'running'
            },
            ...state.executions
          ].slice(0, 100) // Keep last 100 executions
        })),

        updateExecution: (executionId, updates) => set((state) => ({
          executions: state.executions.map(exec =>
            exec.id === executionId
              ? { ...exec, ...updates, updated: new Date().toISOString() }
              : exec
          )
        })),

        removeExecution: (executionId) => set((state) => ({
          executions: state.executions.filter(e => e.id !== executionId)
        })),

        clearExecutions: () => set({ executions: [] }),

        // Actions - Module
        setActiveModule: (moduleId) => set({ activeModule: moduleId }),

        // Actions - Loading
        setLoading: (key, value) => set((state) => ({
          loading: {
            ...state.loading,
            [key]: value
          }
        })),

        // Actions - Error
        setError: (error) => set({ error }),
        clearError: () => set({ error: null }),

        // NEW: Actions - Network Scanner
        addScanResult: (result) => set((state) => ({
          scanResults: [result, ...state.scanResults].slice(0, 50),
          metrics: {
            ...state.metrics,
            networkScans: state.metrics.networkScans + 1,
            activeScans: result.success ? state.metrics.activeScans + 1 : state.metrics.activeScans
          }
        })),

        clearScanResults: () => set({ scanResults: [] }),

        // NEW: Actions - Payload Generator
        addPayload: (payload) => set((state) => ({
          payloads: [payload, ...state.payloads].slice(0, 20),
          metrics: {
            ...state.metrics,
            payloadsGenerated: state.metrics.payloadsGenerated + 1
          }
        })),

        clearPayloads: () => set({ payloads: [] }),

        // Actions - Reset
        reset: () => set({
          metrics: {
            activeScans: 0,
            exploitsFound: 0,
            targets: 0,
            c2Sessions: 0,
            networkScans: 0,
            payloadsGenerated: 0
          },
          executions: [],
          activeModule: 'network-scanner',
          loading: {
            metrics: true,
            executions: false,
            scanner: false
          },
          error: null,
          lastUpdate: null,
          scanResults: [],
          payloads: []
        })
      }),
      {
        name: 'offensive-store',
        partialize: (state) => ({
          activeModule: state.activeModule,
          executions: state.executions.slice(0, 20) // Persist last 20 executions
        })
      }
    ),
    { name: 'OffensiveStore' }
  )
);

// Selectors
export const selectMetrics = (state) => state.metrics;
export const selectExecutions = (state) => state.executions;
export const selectActiveModule = (state) => state.activeModule;
export const selectLoading = (state) => state.loading;
export const selectError = (state) => state.error;
export const selectActiveExecutions = (state) =>
  state.executions.filter(e => e.status === 'running');
export const selectCompletedExecutions = (state) =>
  state.executions.filter(e => e.status === 'completed');
