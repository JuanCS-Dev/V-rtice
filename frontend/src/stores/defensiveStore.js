/**
 * Defensive Operations Store
 *
 * Zustand store for defensive dashboard state management
 * Eliminates props drilling and centralizes state
 *
 * Features:
 * - Centralized metrics state
 * - Alerts management
 * - Active module tracking
 * - Loading states
 * - Error handling
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export const useDefensiveStore = create(
  devtools(
    persist(
      (set, get) => ({
        // State
        metrics: {
          threats: 0,
          suspiciousIPs: 0,
          domains: 0,
          monitored: 0,
          behavioralAnomalies: 0,
          encryptedThreats: 0
        },
        alerts: [],
        activeModule: 'threat-map',
        loading: {
          metrics: true,
          alerts: false,
          behavioral: false,
          traffic: false
        },
        error: null,
        lastUpdate: null,
        
        // NEW: Defensive tools data
        behavioralResults: [],
        trafficResults: [],

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

        // Actions - Alerts
        addAlert: (alert) => set((state) => ({
          alerts: [
            {
              ...alert,
              id: alert.id || `alert-${Date.now()}-${Math.random()}`,
              timestamp: alert.timestamp || new Date().toISOString()
            },
            ...state.alerts
          ].slice(0, 50) // Keep last 50 alerts
        })),

        clearAlerts: () => set({ alerts: [] }),

        removeAlert: (alertId) => set((state) => ({
          alerts: state.alerts.filter(a => a.id !== alertId)
        })),

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

        // NEW: Actions - Behavioral Analyzer
        addBehavioralResult: (result) => set((state) => ({
          behavioralResults: [result, ...state.behavioralResults].slice(0, 50),
          metrics: {
            ...state.metrics,
            behavioralAnomalies: result.is_anomalous 
              ? state.metrics.behavioralAnomalies + 1 
              : state.metrics.behavioralAnomalies
          }
        })),

        clearBehavioralResults: () => set({ behavioralResults: [] }),

        // NEW: Actions - Traffic Analyzer
        addTrafficResult: (result) => set((state) => ({
          trafficResults: [result, ...state.trafficResults].slice(0, 50),
          metrics: {
            ...state.metrics,
            encryptedThreats: result.is_threat 
              ? state.metrics.encryptedThreats + 1 
              : state.metrics.encryptedThreats
          }
        })),

        clearTrafficResults: () => set({ trafficResults: [] }),

        // Actions - Reset
        reset: () => set({
          metrics: {
            threats: 0,
            suspiciousIPs: 0,
            domains: 0,
            monitored: 0,
            behavioralAnomalies: 0,
            encryptedThreats: 0
          },
          alerts: [],
          activeModule: 'threat-map',
          loading: {
            metrics: true,
            alerts: false,
            behavioral: false,
            traffic: false
          },
          error: null,
          lastUpdate: null,
          behavioralResults: [],
          trafficResults: []
        })
      }),
      {
        name: 'defensive-store',
        partialize: (state) => ({
          // Only persist these fields
          activeModule: state.activeModule,
          alerts: state.alerts.slice(0, 10) // Only persist last 10 alerts
        })
      }
    ),
    { name: 'DefensiveStore' }
  )
);

// Selectors (for optimized re-renders)
export const selectMetrics = (state) => state.metrics;
export const selectAlerts = (state) => state.alerts;
export const selectActiveModule = (state) => state.activeModule;
export const selectLoading = (state) => state.loading;
export const selectError = (state) => state.error;
export const selectLastUpdate = (state) => state.lastUpdate;
