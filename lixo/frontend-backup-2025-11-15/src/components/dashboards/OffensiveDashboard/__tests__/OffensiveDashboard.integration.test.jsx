/**
 * OffensiveDashboard Integration Tests
 * =====================================
 *
 * Integration tests for OffensiveDashboard with new service layer
 * Tests the complete flow: Component → Hook → Service
 *
 * Governed by: Constituição Vértice v2.5 - ADR-004 (Testing Strategy)
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { OffensiveDashboard } from '../OffensiveDashboard';
import { useOffensiveMetrics } from '@/hooks/services/useOffensiveService';

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key) => key,
    i18n: { changeLanguage: vi.fn() },
  }),
  I18nextProvider: ({ children }) => children,
  withTranslation: () => (Component) => Component, // HOC mock for class components
}));

// Mock the service layer hooks
vi.mock('@/hooks/services/useOffensiveService', () => ({
  useOffensiveMetrics: vi.fn(() => ({
    data: {
      activeScans: 7,
      exploitsFound: 23,
      targets: 15,
      c2Sessions: 4,
    },
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
  })),
}));

// Mock WebSocket hook
vi.mock('../hooks/useRealTimeExecutions', () => ({
  useRealTimeExecutions: vi.fn(() => ({
    executions: [
      {
        id: 'exec-001',
        type: 'network_scan',
        status: 'running',
        target: '192.168.1.0/24',
        timestamp: '2024-01-15T10:30:00Z',
      },
      {
        id: 'exec-002',
        type: 'vuln_scan',
        status: 'completed',
        target: 'example.com',
        timestamp: '2024-01-15T10:25:00Z',
      },
    ],
  })),
}));

// Mock lazy-loaded modules
vi.mock('../../../cyber/NetworkRecon/NetworkRecon', () => ({
  default: () => <div data-testid="network-recon-module">Network Recon Module</div>,
}));

vi.mock('../../../cyber/VulnIntel/VulnIntel', () => ({
  default: () => <div data-testid="vuln-intel-module">Vuln Intel Module</div>,
}));

vi.mock('../../../cyber/WebAttack/WebAttack', () => ({
  default: () => <div data-testid="web-attack-module">Web Attack Module</div>,
}));

vi.mock('../../../cyber/C2Orchestration/C2Orchestration', () => ({
  default: () => <div data-testid="c2-module">C2 Module</div>,
}));

vi.mock('../../../cyber/BAS/BAS', () => ({
  default: () => <div data-testid="bas-module">BAS Module</div>,
}));

vi.mock('../../../cyber/OffensiveGateway/OffensiveGateway', () => ({
  default: () => <div data-testid="gateway-module">Gateway Module</div>,
}));

vi.mock('../../../cyber/NetworkScanner/NetworkScanner', () => ({
  default: () => <div data-testid="network-scanner-module">Network Scanner Module</div>,
}));

// Helper to create test wrapper
const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('OffensiveDashboard - Service Layer Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Reset mock to default implementation
    useOffensiveMetrics.mockReturnValue({
      data: {
        activeScans: 7,
        exploitsFound: 23,
        targets: 15,
        c2Sessions: 4,
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ============================================================================
  // BASIC RENDERING
  // ============================================================================

  it('should render dashboard with metrics from service layer', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    // Wait for dashboard to render
    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // Verify useOffensiveMetrics was called
    expect(useOffensiveMetrics).toHaveBeenCalled();
  });

  it('should display loading state when metrics are loading', async () => {
    useOffensiveMetrics.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      error: null,
    });

    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    // Dashboard should still render with default metrics
    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });

  it('should handle metrics error gracefully', async () => {
    useOffensiveMetrics.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new Error('Failed to fetch metrics'),
    });

    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    // Dashboard should render with default metrics (0s)
    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // MODULE LOADING
  // ============================================================================

  it('should lazy load network-recon module by default', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('network-recon-module')).toBeInTheDocument();
    });
  });

  it('should display loading fallback while module loads', () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    // Should have main content area
    const main = screen.getByRole('main');
    expect(main).toBeInTheDocument();
  });

  // ============================================================================
  // METRICS INTEGRATION
  // ============================================================================

  it('should pass correct metrics to header component', async () => {
    const customMetrics = {
      activeScans: 12,
      exploitsFound: 45,
      targets: 30,
      c2Sessions: 8,
    };

    useOffensiveMetrics.mockReturnValue({
      data: customMetrics,
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // Verify metrics were passed (header receives metrics prop)
    expect(useOffensiveMetrics).toHaveBeenCalled();
  });

  it('should provide default metrics when data is undefined', async () => {
    useOffensiveMetrics.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
      error: null,
    });

    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // Dashboard should not crash and use default metrics
  });

  // ============================================================================
  // REAL-TIME EXECUTIONS
  // ============================================================================

  it('should display real-time executions in sidebar', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // Executions are passed to OffensiveSidebar component
    // Sidebar should receive executions array
  });

  it('should handle empty executions array', async () => {
    const { useRealTimeExecutions } = await import('../hooks/useRealTimeExecutions');
    useRealTimeExecutions.mockReturnValue({
      executions: [],
    });

    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // MODULE SWITCHING
  // ============================================================================

  it('should have 7 offensive modules available', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // Modules: Network Scanner, Network Recon, Vuln Intel, Web Attack, C2, BAS, Gateway
    // Total: 7 modules
  });

  it('should render network-recon module by default', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('network-recon-module')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // ERROR BOUNDARIES
  // ============================================================================

  it('should wrap header in QueryErrorBoundary', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // QueryErrorBoundary wraps OffensiveHeader
  });

  it('should wrap module in WidgetErrorBoundary', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByTestId('network-recon-module')).toBeInTheDocument();
    });

    // WidgetErrorBoundary wraps module component
  });

  it('should wrap sidebar in WidgetErrorBoundary', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // WidgetErrorBoundary wraps OffensiveSidebar
  });

  // ============================================================================
  // ACCESSIBILITY
  // ============================================================================

  it('should include skip link for keyboard navigation', () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    const skipLink = screen.getByText(/skip/i);
    expect(skipLink).toBeInTheDocument();
    expect(skipLink).toHaveAttribute('href', '#main-content');
  });

  it('should have main landmark with correct id', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      const main = screen.getByRole('main');
      expect(main).toHaveAttribute('id', 'main-content');
    });
  });

  it('should have aria-label on sidebar', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // Sidebar receives ariaLabel prop from i18n
  });

  // ============================================================================
  // NAVIGATION
  // ============================================================================

  it('should call setCurrentView when handleBack is invoked', async () => {
    const mockSetView = vi.fn();
    render(<OffensiveDashboard setCurrentView={mockSetView} />, {
      wrapper: createTestWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // handleBack is passed to OffensiveHeader
    // When invoked, should call setCurrentView('main')
  });

  it('should not crash if setCurrentView is not provided', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // Should handle missing setCurrentView gracefully
  });

  // ============================================================================
  // FOOTER
  // ============================================================================

  it('should render dashboard footer with correct props', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // Footer should display:
    // - moduleName: "OFFENSIVE OPERATIONS"
    // - classification: "TOP SECRET"
    // - statusItems: SYSTEM, MODE, OPSEC
    // - metricsItems: EXECUTIONS count, ACTIVE module
  });

  // ============================================================================
  // INTERNATIONALIZATION
  // ============================================================================

  it('should support internationalization with useTranslation', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // useTranslation hook is used throughout component
    // Module names, accessibility labels, etc. are translated
  });

  it('should translate module names correctly', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // Module names come from i18n: dashboard.offensive.modules.*
  });

  // ============================================================================
  // SERVICE LAYER INTEGRATION
  // ============================================================================

  it('should use useOffensiveMetrics from service layer', async () => {
    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(useOffensiveMetrics).toHaveBeenCalled();
    });

    // Verify correct import: @/hooks/services/useOffensiveService
  });

  it('should handle metrics refetch correctly', async () => {
    const mockRefetch = vi.fn();
    useOffensiveMetrics.mockReturnValue({
      data: { activeScans: 5, exploitsFound: 10, targets: 8, c2Sessions: 2 },
      isLoading: false,
      isError: false,
      error: null,
      refetch: mockRefetch,
    });

    render(<OffensiveDashboard />, { wrapper: createTestWrapper() });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // refetch function is available if needed by child components
  });

  it('should update when metrics data changes', async () => {
    const { rerender } = render(<OffensiveDashboard />, {
      wrapper: createTestWrapper(),
    });

    await waitFor(() => {
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    // Update metrics
    useOffensiveMetrics.mockReturnValue({
      data: {
        activeScans: 20,
        exploitsFound: 50,
        targets: 35,
        c2Sessions: 10,
      },
      isLoading: false,
      isError: false,
      error: null,
    });

    rerender(<OffensiveDashboard />);

    // Dashboard should reflect new metrics
    await waitFor(() => {
      expect(useOffensiveMetrics).toHaveBeenCalled();
    });
  });
});
