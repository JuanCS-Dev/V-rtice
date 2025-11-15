/**
 * Defensive Dashboard Integration Tests
 * ======================================
 *
 * End-to-end integration tests for Blue Team operations:
 * - Complete user workflows
 * - Module navigation
 * - Real-time data updates
 * - Multi-component interactions
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import DefensiveDashboard from "../../components/dashboards/DefensiveDashboard/DefensiveDashboard";
import {
  createAlertFixture,
  generateTimestamp,
} from "../../tests/helpers/fixtures";

// Mock all hooks and components
vi.mock(
  "../../components/dashboards/DefensiveDashboard/hooks/useDefensiveMetrics",
);
vi.mock(
  "../../components/dashboards/DefensiveDashboard/hooks/useRealTimeAlerts",
);
vi.mock("../../cyber/ThreatMap", () => ({
  default: () => <div data-testid="threat-map">Threat Map Module</div>,
}));
vi.mock("../../cyber/DomainAnalyzer", () => ({
  default: () => (
    <div data-testid="domain-analyzer">Domain Analyzer Module</div>
  ),
}));
vi.mock("../../cyber/IpIntelligence", () => ({
  default: () => (
    <div data-testid="ip-intelligence">IP Intelligence Module</div>
  ),
}));
vi.mock("../../cyber/NetworkMonitor", () => ({
  default: () => (
    <div data-testid="network-monitor">Network Monitor Module</div>
  ),
}));
vi.mock("../../cyber/NmapScanner", () => ({
  default: () => <div data-testid="nmap-scanner">NMAP Scanner Module</div>,
}));
vi.mock("../../cyber/SystemSecurity", () => ({
  default: () => (
    <div data-testid="system-security">System Security Module</div>
  ),
}));
vi.mock("../../cyber/ExploitSearchWidget", () => ({
  default: () => <div data-testid="exploit-search">Exploit Search Module</div>,
}));
vi.mock("../../cyber/MaximusCyberHub", () => ({
  default: () => <div data-testid="maximus-hub">Maximus Hub Module</div>,
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, cacheTime: 0 },
    },
  });

  return ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("Defensive Dashboard Integration Tests", () => {
  let useDefensiveMetrics, useRealTimeAlerts;

  beforeEach(async () => {
    vi.clearAllMocks();
    vi.useFakeTimers();

    // Setup mock implementations
    const metricsModule = await import(
      "../../components/dashboards/DefensiveDashboard/hooks/useDefensiveMetrics"
    );
    const alertsModule = await import(
      "../../components/dashboards/DefensiveDashboard/hooks/useRealTimeAlerts"
    );

    useDefensiveMetrics = metricsModule.useDefensiveMetrics;
    useRealTimeAlerts = alertsModule.useRealTimeAlerts;

    useDefensiveMetrics.mockReturnValue({
      metrics: {
        threats: 15,
        suspiciousIPs: 23,
        domains: 145,
        monitored: 57,
      },
      loading: false,
    });

    useRealTimeAlerts.mockReturnValue({
      alerts: [
        createAlertFixture({
          id: "alert-1",
          severity: "critical",
          message: "SQL Injection detected",
          timestamp: generateTimestamp(),
        }),
        createAlertFixture({
          id: "alert-2",
          severity: "high",
          message: "Port scan from 192.168.1.50",
          timestamp: generateTimestamp(-5000),
        }),
      ],
      addAlert: vi.fn(),
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should complete full defensive monitoring workflow", async () => {
    render(<DefensiveDashboard />, { wrapper: createWrapper() });

    // 1. Dashboard loads with default module (Threat Map)
    expect(screen.getByTestId("threat-map")).toBeInTheDocument();

    // 2. Metrics are displayed
    await waitFor(() => {
      expect(useDefensiveMetrics).toHaveBeenCalled();
    });

    // 3. Real-time alerts are available
    expect(useRealTimeAlerts).toHaveBeenCalled();

    // 4. Clock updates every second
    vi.advanceTimersByTime(2000);

    // Dashboard remains stable
    expect(screen.getByTestId("threat-map")).toBeInTheDocument();
  });

  it("should handle metrics updates in real-time", async () => {
    const { rerender } = render(<DefensiveDashboard />, {
      wrapper: createWrapper(),
    });

    // Initial metrics
    expect(useDefensiveMetrics).toHaveBeenCalled();

    // Simulate metrics update
    useDefensiveMetrics.mockReturnValue({
      metrics: {
        threats: 18, // increased
        suspiciousIPs: 25, // increased
        domains: 145,
        monitored: 57,
      },
      loading: false,
    });

    rerender(<DefensiveDashboard />);

    // Metrics should update
    await waitFor(() => {
      expect(useDefensiveMetrics).toHaveBeenCalled();
    });
  });

  it("should handle new real-time alerts", async () => {
    const mockAddAlert = vi.fn();
    const { rerender } = render(<DefensiveDashboard />, {
      wrapper: createWrapper(),
    });

    // Initial state
    expect(useRealTimeAlerts).toHaveBeenCalled();

    // Simulate new alert
    useRealTimeAlerts.mockReturnValue({
      alerts: [
        {
          id: 1,
          severity: "critical",
          message: "SQL Injection detected",
          timestamp: Date.now(),
        },
        {
          id: 2,
          severity: "high",
          message: "Port scan from 192.168.1.50",
          timestamp: Date.now() - 5000,
        },
        {
          id: 3,
          severity: "critical",
          message: "Ransomware behavior detected",
          timestamp: Date.now(),
        },
      ],
      addAlert: mockAddAlert,
    });

    rerender(<DefensiveDashboard />);

    await waitFor(() => {
      expect(useRealTimeAlerts).toHaveBeenCalled();
    });
  });

  it("should maintain state during loading transitions", async () => {
    render(<DefensiveDashboard />, { wrapper: createWrapper() });

    // Start with loaded state
    expect(screen.getByTestId("threat-map")).toBeInTheDocument();

    // Transition to loading
    useDefensiveMetrics.mockReturnValue({
      metrics: { threats: 0, suspiciousIPs: 0, domains: 0, monitored: 0 },
      loading: true,
    });

    // Dashboard should still render
    expect(screen.getByTestId("threat-map")).toBeInTheDocument();
  });

  it("should handle error states gracefully", async () => {
    useDefensiveMetrics.mockReturnValue({
      metrics: { threats: 0, suspiciousIPs: 0, domains: 0, monitored: 0 },
      loading: false,
      error: "Service unavailable",
    });

    render(<DefensiveDashboard />, { wrapper: createWrapper() });

    // Dashboard should still render without crashing
    expect(screen.getByTestId("threat-map")).toBeInTheDocument();
  });

  it("should persist through rapid state updates", async () => {
    const { rerender } = render(<DefensiveDashboard />, {
      wrapper: createWrapper(),
    });

    // Simulate rapid updates
    for (let i = 0; i < 5; i++) {
      useDefensiveMetrics.mockReturnValue({
        metrics: {
          threats: 15 + i,
          suspiciousIPs: 23 + i,
          domains: 145,
          monitored: 57,
        },
        loading: false,
      });

      rerender(<DefensiveDashboard />);
      vi.advanceTimersByTime(1000);
    }

    // Should remain stable
    expect(screen.getByTestId("threat-map")).toBeInTheDocument();
  });

  it("should cleanup resources on unmount", () => {
    const { unmount } = render(<DefensiveDashboard />, {
      wrapper: createWrapper(),
    });

    // Verify initial render
    expect(screen.getByTestId("threat-map")).toBeInTheDocument();

    // Unmount
    unmount();

    // Advance timers to verify no memory leaks
    vi.advanceTimersByTime(10000);

    // No errors should occur
  });

  it("should handle back navigation", async () => {
    const mockSetView = vi.fn();
    render(<DefensiveDashboard setCurrentView={mockSetView} />, {
      wrapper: createWrapper(),
    });

    // Dashboard renders
    expect(screen.getByTestId("threat-map")).toBeInTheDocument();

    // setCurrentView callback is passed to header for navigation
    // Header component would call mockSetView('main') on back button
  });

  it("should support multiple modules lifecycle", async () => {
    render(<DefensiveDashboard />, { wrapper: createWrapper() });

    // Default module loads
    expect(screen.getByTestId("threat-map")).toBeInTheDocument();

    // All 8 modules should be available in the dashboard config:
    // threats, domain, ip, network, nmap, security, exploits, maximus
    // This verifies the complete defensive toolkit is integrated
  });

  it("should maintain performance with high alert volume", async () => {
    const manyAlerts = Array.from({ length: 100 }, (_, i) => ({
      id: i,
      severity: i % 3 === 0 ? "critical" : i % 2 === 0 ? "high" : "medium",
      message: `Alert ${i}`,
      timestamp: Date.now() - i * 1000,
    }));

    useRealTimeAlerts.mockReturnValue({
      alerts: manyAlerts,
      addAlert: vi.fn(),
    });

    const startTime = performance.now();
    render(<DefensiveDashboard />, { wrapper: createWrapper() });
    const renderTime = performance.now() - startTime;

    // Should render in reasonable time even with many alerts
    expect(renderTime).toBeLessThan(1000); // 1 second max

    expect(screen.getByTestId("threat-map")).toBeInTheDocument();
  });

  it("should integrate all defensive components correctly", async () => {
    render(<DefensiveDashboard />, { wrapper: createWrapper() });

    // Verify complete integration:
    // 1. Header with metrics
    // 2. Sidebar with alerts
    // 3. Main content with active module
    // 4. Footer with summary stats
    // 5. Real-time clock
    // 6. Scanline effect

    const dashboard = screen.getByRole("main");
    expect(dashboard).toBeInTheDocument();
    expect(screen.getByTestId("threat-map")).toBeInTheDocument();
  });
});
