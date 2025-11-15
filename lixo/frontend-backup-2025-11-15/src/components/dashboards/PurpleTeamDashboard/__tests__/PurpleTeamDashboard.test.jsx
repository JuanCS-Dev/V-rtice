/**
 * PurpleTeamDashboard Component Tests
 * ====================================
 *
 * Tests for purple team operations dashboard
 * - Split view (Red + Blue)
 * - Unified timeline
 * - Gap analysis
 * - Attack-to-detection correlation
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';
import userEvent from '@testing-library/user-event';
import i18n from '../../../../i18n';
import { PurpleTeamDashboard } from '../PurpleTeamDashboard';

// Mock hooks
vi.mock('../hooks/usePurpleTeamData', () => ({
  usePurpleTeamData: vi.fn(() => ({
    attackData: {
      active: [{ id: 1, type: 'port_scan' }],
      events: [{ id: 1, timestamp: Date.now(), type: 'attack' }]
    },
    defenseData: {
      detections: [{ id: 1, type: 'detection' }],
      events: [{ id: 1, timestamp: Date.now(), type: 'defense' }]
    },
    correlations: [{ attackId: 1, detectionId: 1, confidence: 0.95 }],
    gaps: {
      coveragePercentage: 78,
      undetectedAttacks: 3
    },
    loading: false
  }))
}));

// Mock sub-components
vi.mock('../components/PurpleHeader', () => ({
  PurpleHeader: ({ onBack, activeView, onViewChange, stats }) => (
    <div data-testid="purple-header">
      <button onClick={onBack}>Back</button>
      <button onClick={() => onViewChange('split')}>Split</button>
      <button onClick={() => onViewChange('timeline')}>Timeline</button>
      <button onClick={() => onViewChange('analysis')}>Analysis</button>
      <div data-testid="stats">{JSON.stringify(stats)}</div>
    </div>
  )
}));

vi.mock('../components/SplitView', () => ({
  SplitView: ({ attackData, defenseData, correlations, loading }) => (
    <div data-testid="split-view">
      Split View - Attacks: {attackData.active.length}, Detections: {defenseData.detections.length}
    </div>
  )
}));

vi.mock('../components/UnifiedTimeline', () => ({
  UnifiedTimeline: ({ events, correlations, loading }) => (
    <div data-testid="unified-timeline">
      Timeline - Events: {events.length}, Correlations: {correlations.length}
    </div>
  )
}));

vi.mock('../components/GapAnalysis', () => ({
  GapAnalysis: ({ gaps, attackData, defenseData, loading }) => (
    <div data-testid="gap-analysis">
      Gap Analysis - Coverage: {gaps.coveragePercentage}%
    </div>
  )
}));

vi.mock('../components/PurpleFooter', () => ({
  PurpleFooter: () => <div data-testid="purple-footer">Footer</div>
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, cacheTime: 0 }
    }
  });

  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      <I18nextProvider i18n={i18n}>
        {children}
      </I18nextProvider>
    </QueryClientProvider>
  );
};

describe('PurpleTeamDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render purple team dashboard with split view by default', () => {
    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    expect(screen.getByTestId('split-view')).toBeInTheDocument();
    expect(screen.getByTestId('purple-header')).toBeInTheDocument();
    expect(screen.getByTestId('purple-footer')).toBeInTheDocument();
  });

  it('should display purple team statistics in header', () => {
    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    const stats = screen.getByTestId('stats');
    const statsData = JSON.parse(stats.textContent);

    expect(statsData.activeAttacks).toBe(1);
    expect(statsData.detections).toBe(1);
    expect(statsData.coverage).toBe(78);
    expect(statsData.correlations).toBe(1);
  });

  it('should switch to timeline view', async () => {
    const user = userEvent.setup();
    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    const timelineBtn = screen.getByText('Timeline');
    await user.click(timelineBtn);

    await waitFor(() => {
      expect(screen.getByTestId('unified-timeline')).toBeInTheDocument();
    });
  });

  it('should switch to gap analysis view', async () => {
    const user = userEvent.setup();
    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    const analysisBtn = screen.getByText('Analysis');
    await user.click(analysisBtn);

    await waitFor(() => {
      expect(screen.getByTestId('gap-analysis')).toBeInTheDocument();
    });
  });

  it('should switch back to split view', async () => {
    const user = userEvent.setup();
    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    // Switch to timeline first
    await user.click(screen.getByText('Timeline'));

    // Then back to split
    await user.click(screen.getByText('Split'));

    await waitFor(() => {
      expect(screen.getByTestId('split-view')).toBeInTheDocument();
    });
  });

  it('should call setCurrentView on back button', async () => {
    const user = userEvent.setup();
    const mockSetView = vi.fn();

    render(<PurpleTeamDashboard setCurrentView={mockSetView} />, { wrapper: createWrapper() });

    const backBtn = screen.getByText('Back');
    await user.click(backBtn);

    expect(mockSetView).toHaveBeenCalledWith('main');
  });

  it('should pass attack and defense data to split view', () => {
    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    const splitView = screen.getByTestId('split-view');
    expect(splitView.textContent).toContain('Attacks: 1');
    expect(splitView.textContent).toContain('Detections: 1');
  });

  it('should combine events for timeline view', async () => {
    const user = userEvent.setup();
    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    await user.click(screen.getByText('Timeline'));

    const timeline = screen.getByTestId('unified-timeline');
    // Combined: 1 attack event + 1 defense event = 2
    expect(timeline.textContent).toContain('Events: 2');
  });

  it('should display correlations in timeline', async () => {
    const user = userEvent.setup();
    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    await user.click(screen.getByText('Timeline'));

    const timeline = screen.getByTestId('unified-timeline');
    expect(timeline.textContent).toContain('Correlations: 1');
  });

  it('should show coverage percentage in gap analysis', async () => {
    const user = userEvent.setup();
    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    await user.click(screen.getByText('Analysis'));

    const analysis = screen.getByTestId('gap-analysis');
    expect(analysis.textContent).toContain('Coverage: 78%');
  });

  it('should include skip link for accessibility', () => {
    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    const skipLink = screen.getByText(/skip/i);
    expect(skipLink).toBeInTheDocument();
  });

  it('should handle loading state', async () => {
    const { usePurpleTeamData } = await import('../hooks/usePurpleTeamData');
    usePurpleTeamData.mockReturnValue({
      attackData: { active: [], events: [] },
      defenseData: { detections: [], events: [] },
      correlations: [],
      gaps: { coveragePercentage: 0, undetectedAttacks: 0 },
      loading: true
    });

    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    const splitView = screen.getByTestId('split-view');
    expect(splitView).toBeInTheDocument();
  });

  it('should handle empty data sets', async () => {
    const { usePurpleTeamData } = await import('../hooks/usePurpleTeamData');
    usePurpleTeamData.mockReturnValue({
      attackData: { active: [], events: [] },
      defenseData: { detections: [], events: [] },
      correlations: [],
      gaps: { coveragePercentage: 0, undetectedAttacks: 0 },
      loading: false
    });

    render(<PurpleTeamDashboard />, { wrapper: createWrapper() });

    const stats = screen.getByTestId('stats');
    const statsData = JSON.parse(stats.textContent);

    expect(statsData.activeAttacks).toBe(0);
    expect(statsData.detections).toBe(0);
    expect(statsData.correlations).toBe(0);
  });
});
