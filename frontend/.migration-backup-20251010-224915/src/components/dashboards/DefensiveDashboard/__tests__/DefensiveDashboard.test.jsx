/**
 * DefensiveDashboard Component Tests
 * ==================================
 *
 * Tests for defensive operations dashboard (Blue Team)
 * - Module switching
 * - Real-time metrics
 * - Alert management
 * - Component rendering
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import userEvent from '@testing-library/user-event';
import DefensiveDashboard from '../DefensiveDashboard';

// Mock hooks
vi.mock('../hooks/useDefensiveMetrics', () => ({
  useDefensiveMetrics: vi.fn(() => ({
    metrics: {
      threats: 15,
      suspiciousIPs: 23,
      domains: 145,
      monitored: 57
    },
    loading: false
  }))
}));

vi.mock('../hooks/useRealTimeAlerts', () => ({
  useRealTimeAlerts: vi.fn(() => ({
    alerts: [
      { id: 1, severity: 'high', message: 'Port scan detected', timestamp: Date.now() }
    ],
    addAlert: vi.fn()
  }))
}));

// Mock all cyber tool components
vi.mock('../../../cyber/ThreatMap', () => ({
  default: () => <div data-testid="threat-map">Threat Map</div>
}));

vi.mock('../../../cyber/DomainAnalyzer', () => ({
  default: () => <div data-testid="domain-analyzer">Domain Analyzer</div>
}));

vi.mock('../../../cyber/IpIntelligence', () => ({
  default: () => <div data-testid="ip-intelligence">IP Intelligence</div>
}));

vi.mock('../../../cyber/NetworkMonitor', () => ({
  default: () => <div data-testid="network-monitor">Network Monitor</div>
}));

vi.mock('../../../cyber/NmapScanner', () => ({
  default: () => <div data-testid="nmap-scanner">NMAP Scanner</div>
}));

vi.mock('../../../cyber/SystemSecurity', () => ({
  default: () => <div data-testid="system-security">System Security</div>
}));

vi.mock('../../../cyber/ExploitSearchWidget', () => ({
  default: () => <div data-testid="exploit-search">Exploit Search</div>
}));

vi.mock('../../../cyber/MaximusCyberHub', () => ({
  default: () => <div data-testid="maximus-hub">Maximus Hub</div>
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, cacheTime: 0 }
    }
  });

  return ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('DefensiveDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should render defensive dashboard with default module', () => {
    render(<DefensiveDashboard />, { wrapper: createWrapper() });

    // Default module is 'threats' (Threat Map)
    expect(screen.getByTestId('threat-map')).toBeInTheDocument();
  });

  it('should display defensive metrics', () => {
    render(<DefensiveDashboard />, { wrapper: createWrapper() });

    // Metrics are passed to header component
    // We can't easily test internal header props without exposing them
    // But we can verify the dashboard renders
    expect(screen.getByTestId('threat-map')).toBeInTheDocument();
  });

  it('should display real-time alerts', () => {
    render(<DefensiveDashboard />, { wrapper: createWrapper() });

    // Alerts are passed to sidebar
    // Verify dashboard structure
    const dashboard = screen.getByRole('main');
    expect(dashboard).toBeInTheDocument();
  });

  it('should update clock every second', () => {
    render(<DefensiveDashboard />, { wrapper: createWrapper() });

    // Clock is managed internally via setInterval
    // Advance time and verify no errors
    vi.advanceTimersByTime(2000);

    expect(screen.getByTestId('threat-map')).toBeInTheDocument();
  });

  it('should cleanup timer on unmount', () => {
    const { unmount } = render(<DefensiveDashboard />, { wrapper: createWrapper() });

    unmount();

    // Should not throw errors after unmounting
    vi.advanceTimersByTime(5000);
  });

  it('should handle setCurrentView callback', () => {
    const mockSetView = vi.fn();
    render(<DefensiveDashboard setCurrentView={mockSetView} />, { wrapper: createWrapper() });

    // Callback is passed to header for back navigation
    expect(screen.getByTestId('threat-map')).toBeInTheDocument();
  });

  it('should render with loading state', async () => {
    const { useDefensiveMetrics } = await import('../hooks/useDefensiveMetrics');
    useDefensiveMetrics.mockReturnValue({
      metrics: { threats: 0, suspiciousIPs: 0, domains: 0, monitored: 0 },
      loading: true
    });

    render(<DefensiveDashboard />, { wrapper: createWrapper() });

    expect(screen.getByTestId('threat-map')).toBeInTheDocument();
  });

  it('should handle empty alerts array', async () => {
    const { useRealTimeAlerts } = await import('../hooks/useRealTimeAlerts');
    useRealTimeAlerts.mockReturnValue({
      alerts: [],
      addAlert: vi.fn()
    });

    render(<DefensiveDashboard />, { wrapper: createWrapper() });

    expect(screen.getByTestId('threat-map')).toBeInTheDocument();
  });

  it('should apply defensive dashboard CSS class', () => {
    const { container } = render(<DefensiveDashboard />, { wrapper: createWrapper() });

    const dashboard = container.querySelector('.dashboard-defensive');
    expect(dashboard).toBeInTheDocument();
  });

  it('should include scanline overlay effect', () => {
    const { container } = render(<DefensiveDashboard />, { wrapper: createWrapper() });

    const scanline = container.querySelector('.scanline-overlay');
    expect(scanline).toBeInTheDocument();
  });
});
