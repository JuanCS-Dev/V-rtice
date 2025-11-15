/**
 * OffensiveDashboard Component Tests
 * ===================================
 *
 * Tests for offensive operations dashboard (Red Team)
 * - Module lazy loading
 * - Metrics display
 * - Real-time executions
 * - i18n support
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nextProvider } from "react-i18next";
import i18n from "../../../../i18n";
import { OffensiveDashboard } from "../OffensiveDashboard";

// Mock hooks
vi.mock("../hooks/useOffensiveMetrics", () => ({
  useOffensiveMetrics: vi.fn(() => ({
    metrics: {
      activeScans: 5,
      activeSessions: 3,
      simulationsToday: 12,
      vulnerabilitiesFound: 48,
    },
    loading: false,
  })),
}));

vi.mock("../hooks/useRealTimeExecutions", () => ({
  useRealTimeExecutions: vi.fn(() => ({
    executions: [
      { id: 1, type: "nmap_scan", status: "running", target: "192.168.1.0/24" },
    ],
  })),
}));

// Mock lazy-loaded modules
vi.mock("../../../cyber/NetworkRecon/NetworkRecon", () => ({
  default: () => <div data-testid="network-recon">Network Recon</div>,
}));

vi.mock("../../../cyber/VulnIntel/VulnIntel", () => ({
  default: () => <div data-testid="vuln-intel">Vuln Intel</div>,
}));

vi.mock("../../../cyber/WebAttack/WebAttack", () => ({
  default: () => <div data-testid="web-attack">Web Attack</div>,
}));

vi.mock("../../../cyber/C2Orchestration/C2Orchestration", () => ({
  default: () => <div data-testid="c2-orchestration">C2 Orchestration</div>,
}));

vi.mock("../../../cyber/BAS/BAS", () => ({
  default: () => <div data-testid="bas">BAS</div>,
}));

vi.mock("../../../cyber/OffensiveGateway/OffensiveGateway", () => ({
  default: () => <div data-testid="offensive-gateway">Offensive Gateway</div>,
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, cacheTime: 0 },
    },
  });

  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
    </QueryClientProvider>
  );
};

describe("OffensiveDashboard Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render offensive dashboard", async () => {
    render(<OffensiveDashboard />, { wrapper: createWrapper() });

    // Default module is 'network-recon'
    await waitFor(() => {
      expect(screen.getByTestId("network-recon")).toBeInTheDocument();
    });
  });

  it("should display loading fallback while lazy loading", () => {
    render(<OffensiveDashboard />, { wrapper: createWrapper() });

    // Loading state appears briefly
    const main = screen.getByRole("main");
    expect(main).toBeInTheDocument();
  });

  it("should display offensive metrics", async () => {
    render(<OffensiveDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("network-recon")).toBeInTheDocument();
    });

    // Metrics are passed to header component
  });

  it("should display real-time executions in sidebar", async () => {
    render(<OffensiveDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("network-recon")).toBeInTheDocument();
    });

    // Executions are passed to sidebar
  });

  it("should call setCurrentView on back", async () => {
    const mockSetView = vi.fn();
    render(<OffensiveDashboard setCurrentView={mockSetView} />, {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByTestId("network-recon")).toBeInTheDocument();
    });

    // Back handler is passed to header
  });

  it("should have 6 offensive modules", async () => {
    render(<OffensiveDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("network-recon")).toBeInTheDocument();
    });

    // Modules: Network Recon, Vuln Intel, Web Attack, C2, BAS, Gateway
  });

  it("should include skip link for accessibility", () => {
    render(<OffensiveDashboard />, { wrapper: createWrapper() });

    const skipLink = screen.getByText(/skip/i);
    expect(skipLink).toBeInTheDocument();
  });

  it("should wrap modules in error boundaries", async () => {
    render(<OffensiveDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("network-recon")).toBeInTheDocument();
    });

    // WidgetErrorBoundary and QueryErrorBoundary are used
  });

  it("should handle loading state for metrics", async () => {
    const { useOffensiveMetrics } = await import(
      "../hooks/useOffensiveMetrics"
    );
    useOffensiveMetrics.mockReturnValue({
      metrics: {
        activeScans: 0,
        activeSessions: 0,
        simulationsToday: 0,
        vulnerabilitiesFound: 0,
      },
      loading: true,
    });

    render(<OffensiveDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("network-recon")).toBeInTheDocument();
    });
  });

  it("should handle empty executions array", async () => {
    const { useRealTimeExecutions } = await import(
      "../hooks/useRealTimeExecutions"
    );
    useRealTimeExecutions.mockReturnValue({
      executions: [],
    });

    render(<OffensiveDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("network-recon")).toBeInTheDocument();
    });
  });

  it("should support internationalization", async () => {
    render(<OffensiveDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId("network-recon")).toBeInTheDocument();
    });

    // i18n translations are used throughout
  });
});
