/**
 * DistributedTopologyWidget Component Tests
 * ==========================================
 *
 * Tests for FASE 10 Distributed Organism Widget
 * - Edge agents status
 * - Global metrics
 * - Network topology
 * - Auto-refresh functionality
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DistributedTopologyWidget } from '../DistributedTopologyWidget';
import * as maximusAI from '../../../../api/maximusAI';

// Mock API functions
vi.mock('../../../../api/maximusAI', () => ({
  getEdgeStatus: vi.fn(),
  getGlobalMetrics: vi.fn(),
  getTopology: vi.fn()
}));

describe('DistributedTopologyWidget Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should render widget with header', () => {
    maximusAI.getTopology.mockResolvedValue({ agents: [], regions: [] });
    render(<DistributedTopologyWidget />);

    expect(screen.getByText('🌐 Distributed Organism')).toBeInTheDocument();
    expect(screen.getByText('FASE 10')).toBeInTheDocument();
  });

  it('should have topology and metrics view buttons', () => {
    maximusAI.getTopology.mockResolvedValue({ agents: [], regions: [] });
    render(<DistributedTopologyWidget />);

    expect(screen.getByText('📊 Topology')).toBeInTheDocument();
    expect(screen.getByText('📈 Global Metrics')).toBeInTheDocument();
  });

  it('should have auto-refresh toggle enabled by default', () => {
    maximusAI.getTopology.mockResolvedValue({ agents: [], regions: [] });
    render(<DistributedTopologyWidget />);

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeChecked();
  });

  it('should fetch topology on mount', async () => {
    const mockTopology = {
      agent_count: 5,
      healthy_count: 4,
      regions: ['us-east', 'eu-west'],
      agents: []
    };
    maximusAI.getTopology.mockResolvedValue(mockTopology);

    render(<DistributedTopologyWidget />);

    await waitFor(() => {
      expect(maximusAI.getTopology).toHaveBeenCalled();
    });
  });

  it('should switch to metrics view', async () => {
    const user = userEvent.setup({ delay: null });
    maximusAI.getTopology.mockResolvedValue({ agents: [], regions: [] });
    maximusAI.getGlobalMetrics.mockResolvedValue({
      events_per_second: 1500,
      avg_compression_ratio: 0.65,
      p95_latency_ms: 42,
      total_events: 1000000,
      total_bytes: 5242880
    });

    render(<DistributedTopologyWidget />);

    const metricsBtn = screen.getByText('📈 Global Metrics');
    await user.click(metricsBtn);

    await waitFor(() => {
      expect(maximusAI.getGlobalMetrics).toHaveBeenCalledWith(60);
    });
  });

  it('should display topology summary', async () => {
    const mockTopology = {
      agent_count: 8,
      healthy_count: 7,
      regions: ['us-east', 'eu-west', 'ap-south'],
      agents: []
    };
    maximusAI.getTopology.mockResolvedValue(mockTopology);

    render(<DistributedTopologyWidget />);

    await waitFor(() => {
      expect(screen.getByText('8')).toBeInTheDocument(); // agent_count
      expect(screen.getByText('7')).toBeInTheDocument(); // healthy_count
      expect(screen.getByText('3')).toBeInTheDocument(); // regions length
    });
  });

  it('should display agent cards', async () => {
    const mockTopology = {
      agent_count: 2,
      healthy_count: 2,
      regions: ['us-east'],
      agents: [
        {
          id: 'edge-001',
          health: 'healthy',
          location: 'us-east-1a',
          buffer_utilization: 45,
          events_per_second: 250
        },
        {
          id: 'edge-002',
          health: 'degraded',
          location: 'eu-west-1b',
          buffer_utilization: 78,
          events_per_second: 180
        }
      ]
    };
    maximusAI.getTopology.mockResolvedValue(mockTopology);

    render(<DistributedTopologyWidget />);

    await waitFor(() => {
      expect(screen.getByText('edge-001')).toBeInTheDocument();
      expect(screen.getByText('edge-002')).toBeInTheDocument();
      expect(screen.getByText('us-east-1a')).toBeInTheDocument();
      expect(screen.getByText('eu-west-1b')).toBeInTheDocument();
    });
  });

  it('should display global metrics', async () => {
    const user = userEvent.setup({ delay: null });
    maximusAI.getTopology.mockResolvedValue({ agents: [], regions: [] });
    maximusAI.getGlobalMetrics.mockResolvedValue({
      events_per_second: 2500,
      avg_compression_ratio: 0.72,
      p95_latency_ms: 38,
      total_events: 5000000,
      total_bytes: 104857600 // 100 MB
    });

    render(<DistributedTopologyWidget />);

    await user.click(screen.getByText('📈 Global Metrics'));

    await waitFor(() => {
      expect(screen.getByText('2500')).toBeInTheDocument(); // events_per_second
      expect(screen.getByText('72.0%')).toBeInTheDocument(); // compression
      expect(screen.getByText('38')).toBeInTheDocument(); // latency
      expect(screen.getByText('100.00')).toBeInTheDocument(); // MB
    });
  });

  it('should show loading state while fetching', async () => {
    maximusAI.getTopology.mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve({ agents: [], regions: [] }), 1000))
    );

    render(<DistributedTopologyWidget />);

    expect(screen.getByText('Loading topology...')).toBeInTheDocument();
  });

  it('should auto-refresh topology every 10 seconds', async () => {
    maximusAI.getTopology.mockResolvedValue({ agents: [], regions: [] });

    render(<DistributedTopologyWidget />);

    await waitFor(() => {
      expect(maximusAI.getTopology).toHaveBeenCalledTimes(1);
    });

    // Advance timer by 10 seconds
    vi.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(maximusAI.getTopology).toHaveBeenCalledTimes(2);
    });
  });

  it('should disable auto-refresh when toggled off', async () => {
    const user = userEvent.setup({ delay: null });
    maximusAI.getTopology.mockResolvedValue({ agents: [], regions: [] });

    render(<DistributedTopologyWidget />);

    await waitFor(() => {
      expect(maximusAI.getTopology).toHaveBeenCalledTimes(1);
    });

    // Disable auto-refresh
    const checkbox = screen.getByRole('checkbox');
    await user.click(checkbox);

    vi.advanceTimersByTime(20000);

    // Should not fetch again
    expect(maximusAI.getTopology).toHaveBeenCalledTimes(1);
  });

  it('should re-enable auto-refresh when toggled back on', async () => {
    const user = userEvent.setup({ delay: null });
    maximusAI.getTopology.mockResolvedValue({ agents: [], regions: [] });

    render(<DistributedTopologyWidget />);

    await waitFor(() => {
      expect(maximusAI.getTopology).toHaveBeenCalledTimes(1);
    });

    // Disable
    const checkbox = screen.getByRole('checkbox');
    await user.click(checkbox);

    // Re-enable
    await user.click(checkbox);

    vi.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(maximusAI.getTopology).toHaveBeenCalled();
    });
  });

  it('should apply correct health color for healthy agents', async () => {
    const mockTopology = {
      agent_count: 1,
      healthy_count: 1,
      regions: ['us-east'],
      agents: [
        { id: 'edge-001', health: 'healthy', location: 'us-east-1a', buffer_utilization: 30, events_per_second: 100 }
      ]
    };
    maximusAI.getTopology.mockResolvedValue(mockTopology);

    const { container } = render(<DistributedTopologyWidget />);

    await waitFor(() => {
      const indicator = container.querySelector('.health-indicator');
      expect(indicator).toHaveStyle({ backgroundColor: '#38ef7d' });
    });
  });

  it('should apply correct health color for degraded agents', async () => {
    const mockTopology = {
      agent_count: 1,
      healthy_count: 0,
      regions: ['us-east'],
      agents: [
        { id: 'edge-001', health: 'degraded', location: 'us-east-1a', buffer_utilization: 85, events_per_second: 50 }
      ]
    };
    maximusAI.getTopology.mockResolvedValue(mockTopology);

    const { container } = render(<DistributedTopologyWidget />);

    await waitFor(() => {
      const indicator = container.querySelector('.health-indicator');
      expect(indicator).toHaveStyle({ backgroundColor: '#ffa500' });
    });
  });

  it('should show "no agents" when topology is empty', async () => {
    const mockTopology = {
      agent_count: 0,
      healthy_count: 0,
      regions: [],
      agents: null
    };
    maximusAI.getTopology.mockResolvedValue(mockTopology);

    render(<DistributedTopologyWidget />);

    await waitFor(() => {
      expect(screen.getByText('No agents available')).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    maximusAI.getTopology.mockRejectedValue(new Error('Network error'));

    render(<DistributedTopologyWidget />);

    await waitFor(() => {
      expect(consoleError).toHaveBeenCalledWith('Topology fetch failed:', expect.any(Error));
    });

    consoleError.mockRestore();
  });

  it('should cleanup interval on unmount', async () => {
    maximusAI.getTopology.mockResolvedValue({ agents: [], regions: [] });

    const { unmount } = render(<DistributedTopologyWidget />);

    await waitFor(() => {
      expect(maximusAI.getTopology).toHaveBeenCalledTimes(1);
    });

    unmount();

    vi.advanceTimersByTime(20000);

    // Should not call again after unmount
    expect(maximusAI.getTopology).toHaveBeenCalledTimes(1);
  });

  it('should refetch when switching between views', async () => {
    const user = userEvent.setup({ delay: null });
    maximusAI.getTopology.mockResolvedValue({ agents: [], regions: [] });
    maximusAI.getGlobalMetrics.mockResolvedValue({ events_per_second: 1000 });

    render(<DistributedTopologyWidget />);

    await waitFor(() => {
      expect(maximusAI.getTopology).toHaveBeenCalledTimes(1);
    });

    // Switch to metrics
    await user.click(screen.getByText('📈 Global Metrics'));

    await waitFor(() => {
      expect(maximusAI.getGlobalMetrics).toHaveBeenCalled();
    });

    // Switch back to topology
    await user.click(screen.getByText('📊 Topology'));

    await waitFor(() => {
      expect(maximusAI.getTopology).toHaveBeenCalledTimes(2);
    });
  });
});
