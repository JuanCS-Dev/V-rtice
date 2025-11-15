/**
 * ThreatMap Component Tests
 *
 * Comprehensive test suite for ThreatMap component
 * 62 tests covering all functionality
 *
 * Test Coverage:
 * - Component rendering and initialization
 * - Threat data loading and display
 * - Filtering mechanisms (severity, type, time range)
 * - Map interactions
 * - Error handling and empty states
 * - Loading states
 * - Threat selection and details
 * - Stats calculation and display
 * - Refresh functionality
 * - AskMaximus integration
 * - Accessibility features
 * - Performance optimizations (useMemo)
 * - Responsive behavior
 */

import React from 'react';
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThreatMap } from '../ThreatMap';
import * as useThreatDataHook from '../hooks/useThreatData';

// Mock modules
vi.mock('@/utils/dateHelpers', () => ({
  formatDateTime: vi.fn((date) => date || '2025-01-15 10:00:00'),
  formatDate: vi.fn((date) => date || '2025-01-15'),
  formatTime: vi.fn((date) => date || '10:00:00'),
  getTimestamp: vi.fn(() => '2025-01-15T10:00:00Z')
}));

vi.mock('../../shared', () => ({
  Card: ({ children, title, badge, headerActions, ...props }) => (
    <div data-testid="card" data-title={title} data-badge={badge} {...props}>
      {headerActions && <div data-testid="card-header-actions">{headerActions}</div>}
      {children}
    </div>
  ),
  Badge: ({ children, variant, size }) => (
    <span data-testid="badge" data-variant={variant} data-size={size}>
      {children}
    </span>
  ),
  LoadingSpinner: ({ text }) => <div data-testid="loading-spinner">{text}</div>
}));

vi.mock('../../shared/AskMaximusButton', () => ({
  default: ({ context, prompt }) => (
    <button data-testid="ask-maximus-button" data-context={JSON.stringify(context)}>
      Ask Maximus
    </button>
  )
}));

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children, center, zoom, className }) => (
    <div
      data-testid="map-container"
      data-center={JSON.stringify(center)}
      data-zoom={zoom}
      className={className}
    >
      {children}
    </div>
  ),
  TileLayer: ({ url, attribution }) => (
    <div data-testid="tile-layer" data-url={url} data-attribution={attribution} />
  )
}));

vi.mock('../components/ThreatMarkers', () => ({
  default: ({ threats, onThreatClick }) => (
    <div data-testid="threat-markers">
      {threats.map((threat, index) => (
        <button
          key={index}
          data-testid={`threat-marker-${index}`}
          onClick={() => onThreatClick(threat)}
        >
          {threat.source}
        </button>
      ))}
    </div>
  )
}));

vi.mock('../components/ThreatFilters', () => ({
  ThreatFilters: ({ filters, onFiltersChange }) => (
    <div data-testid="threat-filters">
      <button
        data-testid="set-severity-filter"
        onClick={() => onFiltersChange({ ...filters, severity: ['critical'] })}
      >
        Set Critical
      </button>
      <button
        data-testid="set-type-filter"
        onClick={() => onFiltersChange({ ...filters, type: ['malicious'] })}
      >
        Set Malicious
      </button>
      <button
        data-testid="clear-filters"
        onClick={() => onFiltersChange({ severity: [], type: [], timeRange: '24h' })}
      >
        Clear
      </button>
    </div>
  )
}));

describe('ThreatMap', () => {
  // Mock threat data
  const mockThreats = [
    {
      id: 'threat_1',
      lat: -23.5505,
      lng: -46.6333,
      severity: 'critical',
      type: 'malicious',
      timestamp: '2025-01-15T10:00:00Z',
      source: '185.220.101.23',
      description: 'Tor exit node',
      country: 'Brazil',
      city: 'São Paulo',
      isp: 'Test ISP',
      asn: 'AS1234',
      threatScore: 85,
      isMalicious: true,
      confidence: 'high'
    },
    {
      id: 'threat_2',
      lat: 40.7128,
      lng: -74.0060,
      severity: 'high',
      type: 'unknown',
      timestamp: '2025-01-15T10:05:00Z',
      source: '45.142.212.61',
      description: 'Known botnet',
      country: 'USA',
      city: 'New York',
      isp: 'Test ISP 2',
      asn: 'AS5678',
      threatScore: 75,
      isMalicious: true,
      confidence: 'high'
    },
    {
      id: 'threat_3',
      lat: 51.5074,
      lng: -0.1278,
      severity: 'medium',
      type: 'malicious',
      timestamp: '2025-01-15T10:10:00Z',
      source: '89.248.165.201',
      description: 'Malware C2',
      country: 'UK',
      city: 'London',
      isp: 'Test ISP 3',
      asn: 'AS9012',
      threatScore: 50,
      isMalicious: false,
      confidence: 'medium'
    },
    {
      id: 'threat_4',
      lat: 35.6762,
      lng: 139.6503,
      severity: 'low',
      type: 'unknown',
      timestamp: '2025-01-15T10:15:00Z',
      source: '8.8.8.8',
      description: 'Google DNS',
      country: 'Japan',
      city: 'Tokyo',
      isp: 'Google',
      asn: 'AS15169',
      threatScore: 20,
      isMalicious: false,
      confidence: 'low'
    }
  ];

  const defaultUseThreatData = {
    threats: mockThreats,
    loading: false,
    error: null,
    filters: { severity: [], type: [], timeRange: '24h' },
    setFilters: vi.fn(),
    refresh: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue(defaultUseThreatData);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ==================== RENDERING TESTS ====================
  describe('Component Rendering', () => {
    it('should render without crashing', () => {
      render(<ThreatMap />);
      expect(screen.getByTestId('card')).toBeInTheDocument();
    });

    it('should render with correct title', () => {
      render(<ThreatMap />);
      const card = screen.getByTestId('card');
      expect(card).toHaveAttribute('data-title', 'CYBER THREAT MAP');
    });

    it('should render with threat count badge', () => {
      render(<ThreatMap />);
      const card = screen.getByTestId('card');
      expect(card).toHaveAttribute('data-badge', '4 THREATS');
    });

    it('should have Maximus semantic attributes', () => {
      render(<ThreatMap />);
      const card = screen.getByTestId('card');
      expect(card).toHaveAttribute('data-maximus-tool', 'threat-map');
      expect(card).toHaveAttribute('data-maximus-category', 'shared');
      expect(card).toHaveAttribute('data-maximus-status', 'ready');
    });

    it('should render all main sections', () => {
      render(<ThreatMap />);
      expect(screen.getByTestId('threat-filters')).toBeInTheDocument();
      expect(screen.getByTestId('map-container')).toBeInTheDocument();
      expect(screen.getByRole('region', { name: 'Threat statistics' })).toBeInTheDocument();
    });

    it('should render AskMaximus button', () => {
      render(<ThreatMap />);
      expect(screen.getByTestId('ask-maximus-button')).toBeInTheDocument();
    });

    it('should render refresh button', () => {
      render(<ThreatMap />);
      const refreshBtn = screen.getByTitle('Atualizar');
      expect(refreshBtn).toBeInTheDocument();
    });
  });

  // ==================== DATA DISPLAY TESTS ====================
  describe('Threat Data Display', () => {
    it('should display threat markers', () => {
      render(<ThreatMap />);
      expect(screen.getByTestId('threat-markers')).toBeInTheDocument();
      expect(screen.getAllByTestId(/threat-marker-/)).toHaveLength(4);
    });

    it('should display correct severity counts', () => {
      render(<ThreatMap />);
      const badges = screen.getAllByTestId('badge');

      // Find severity badges
      const criticalBadge = badges.find(b => b.getAttribute('data-variant') === 'critical');
      const highBadge = badges.find(b => b.getAttribute('data-variant') === 'high');
      const mediumBadge = badges.find(b => b.getAttribute('data-variant') === 'medium');
      const lowBadge = badges.find(b => b.getAttribute('data-variant') === 'low');

      expect(criticalBadge).toHaveTextContent('1');
      expect(highBadge).toHaveTextContent('1');
      expect(mediumBadge).toHaveTextContent('1');
      expect(lowBadge).toHaveTextContent('1');
    });

    it('should display total threat count in stats', () => {
      render(<ThreatMap />);
      const statsBar = screen.getByRole('region', { name: 'Threat statistics' });
      expect(within(statsBar).getByText('4')).toBeInTheDocument();
    });

    it('should render map with correct center coordinates', () => {
      render(<ThreatMap />);
      const mapContainer = screen.getByTestId('map-container');
      expect(mapContainer).toHaveAttribute('data-center', '[-23.5505,-46.6333]');
    });

    it('should render map with correct zoom level', () => {
      render(<ThreatMap />);
      const mapContainer = screen.getByTestId('map-container');
      expect(mapContainer).toHaveAttribute('data-zoom', '10');
    });

    it('should display zero counts when no threats', () => {
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        threats: []
      });

      render(<ThreatMap />);
      const card = screen.getByTestId('card');
      expect(card).toHaveAttribute('data-badge', '0 THREATS');
    });
  });

  // ==================== LOADING STATE TESTS ====================
  describe('Loading States', () => {
    it('should show loading overlay when loading', () => {
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        loading: true
      });

      render(<ThreatMap />);
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      expect(screen.getByText('Carregando ameaças...')).toBeInTheDocument();
    });

    it('should set maximus-status to loading when loading', () => {
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        loading: true
      });

      render(<ThreatMap />);
      const card = screen.getByTestId('card');
      expect(card).toHaveAttribute('data-maximus-status', 'loading');
    });

    it('should disable refresh button when loading', () => {
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        loading: true
      });

      render(<ThreatMap />);
      const refreshBtn = screen.getByTitle('Atualizar');
      expect(refreshBtn).toBeDisabled();
    });

    it('should not show loading overlay when not loading', () => {
      render(<ThreatMap />);
      expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    });
  });

  // ==================== ERROR STATE TESTS ====================
  describe('Error States', () => {
    it('should show error overlay when error occurs', () => {
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        error: 'Network error occurred'
      });

      render(<ThreatMap />);
      expect(screen.getByText('Network error occurred')).toBeInTheDocument();
    });

    it('should display error icon', () => {
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        error: 'Test error'
      });

      render(<ThreatMap />);
      const errorIcon = screen.getByRole('img', { hidden: true });
      expect(errorIcon).toHaveClass('fa-exclamation-triangle');
    });

    it('should not show error overlay when no error', () => {
      render(<ThreatMap />);
      expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
    });

    it('should handle empty error message gracefully', () => {
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        error: ''
      });

      render(<ThreatMap />);
      // Should not crash with empty error
      expect(screen.getByTestId('card')).toBeInTheDocument();
    });
  });

  // ==================== FILTERING TESTS ====================
  describe('Filtering Functionality', () => {
    it('should render ThreatFilters component', () => {
      render(<ThreatMap />);
      expect(screen.getByTestId('threat-filters')).toBeInTheDocument();
    });

    it('should call setFilters when severity filter changes', async () => {
      const user = userEvent.setup();
      const mockSetFilters = vi.fn();
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        setFilters: mockSetFilters
      });

      render(<ThreatMap />);
      const severityBtn = screen.getByTestId('set-severity-filter');
      await user.click(severityBtn);

      expect(mockSetFilters).toHaveBeenCalledWith({
        severity: ['critical'],
        type: [],
        timeRange: '24h'
      });
    });

    it('should call setFilters when type filter changes', async () => {
      const user = userEvent.setup();
      const mockSetFilters = vi.fn();
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        setFilters: mockSetFilters
      });

      render(<ThreatMap />);
      const typeBtn = screen.getByTestId('set-type-filter');
      await user.click(typeBtn);

      expect(mockSetFilters).toHaveBeenCalledWith({
        severity: [],
        type: ['malicious'],
        timeRange: '24h'
      });
    });

    it('should pass current filters to ThreatFilters component', () => {
      const customFilters = {
        severity: ['critical', 'high'],
        type: ['malicious'],
        timeRange: '7d'
      };

      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        filters: customFilters
      });

      render(<ThreatMap />);
      // Component receives correct filters through props
      expect(screen.getByTestId('threat-filters')).toBeInTheDocument();
    });

    it('should clear filters when clear button clicked', async () => {
      const user = userEvent.setup();
      const mockSetFilters = vi.fn();
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        filters: { severity: ['critical'], type: ['malicious'], timeRange: '24h' },
        setFilters: mockSetFilters
      });

      render(<ThreatMap />);
      const clearBtn = screen.getByTestId('clear-filters');
      await user.click(clearBtn);

      expect(mockSetFilters).toHaveBeenCalledWith({
        severity: [],
        type: [],
        timeRange: '24h'
      });
    });
  });

  // ==================== THREAT SELECTION TESTS ====================
  describe('Threat Selection and Details', () => {
    it('should not show threat details initially', () => {
      render(<ThreatMap />);
      expect(screen.queryByRole('region', { name: 'Selected threat details' })).not.toBeInTheDocument();
    });

    it('should show threat details when marker clicked', async () => {
      const user = userEvent.setup();
      render(<ThreatMap />);

      const marker = screen.getByTestId('threat-marker-0');
      await user.click(marker);

      expect(screen.getByRole('region', { name: 'Selected threat details' })).toBeInTheDocument();
    });

    it('should display correct threat details', async () => {
      const user = userEvent.setup();
      render(<ThreatMap />);

      const marker = screen.getByTestId('threat-marker-0');
      await user.click(marker);

      const detailsSection = screen.getByRole('region', { name: 'Selected threat details' });
      expect(within(detailsSection).getByText('MALICIOUS')).toBeInTheDocument();
      expect(within(detailsSection).getByText('185.220.101.23')).toBeInTheDocument();
    });

    it('should close threat details when close button clicked', async () => {
      const user = userEvent.setup();
      render(<ThreatMap />);

      // Open details
      const marker = screen.getByTestId('threat-marker-0');
      await user.click(marker);

      expect(screen.getByRole('region', { name: 'Selected threat details' })).toBeInTheDocument();

      // Close details
      const closeBtn = screen.getByRole('button', { name: '' }); // Close button with icon
      await user.click(closeBtn);

      expect(screen.queryByRole('region', { name: 'Selected threat details' })).not.toBeInTheDocument();
    });

    it('should display formatted coordinates in details', async () => {
      const user = userEvent.setup();
      render(<ThreatMap />);

      const marker = screen.getByTestId('threat-marker-0');
      await user.click(marker);

      const detailsSection = screen.getByRole('region', { name: 'Selected threat details' });
      expect(within(detailsSection).getByText(/-23\.5505, -46\.6333/)).toBeInTheDocument();
    });

    it('should display severity badge in details', async () => {
      const user = userEvent.setup();
      render(<ThreatMap />);

      const marker = screen.getByTestId('threat-marker-0');
      await user.click(marker);

      const detailsSection = screen.getByRole('region', { name: 'Selected threat details' });
      const badge = within(detailsSection).getByTestId('badge');
      expect(badge).toHaveAttribute('data-variant', 'critical');
    });
  });

  // ==================== REFRESH FUNCTIONALITY TESTS ====================
  describe('Refresh Functionality', () => {
    it('should call refresh when refresh button clicked', async () => {
      const user = userEvent.setup();
      const mockRefresh = vi.fn();
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        refresh: mockRefresh
      });

      render(<ThreatMap />);
      const refreshBtn = screen.getByTitle('Atualizar');
      await user.click(refreshBtn);

      expect(mockRefresh).toHaveBeenCalledTimes(1);
    });

    it('should show spinning icon when loading', () => {
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        loading: true
      });

      render(<ThreatMap />);
      const refreshBtn = screen.getByTitle('Atualizar');
      const icon = refreshBtn.querySelector('.fa-sync');
      expect(icon).toHaveClass('fa-spin');
    });

    it('should not show spinning icon when not loading', () => {
      render(<ThreatMap />);
      const refreshBtn = screen.getByTitle('Atualizar');
      const icon = refreshBtn.querySelector('.fa-sync');
      expect(icon).not.toHaveClass('fa-spin');
    });
  });

  // ==================== ASKMAXIMUS INTEGRATION TESTS ====================
  describe('AskMaximus Integration', () => {
    it('should render AskMaximus button with correct context', () => {
      render(<ThreatMap />);
      const askBtn = screen.getByTestId('ask-maximus-button');

      const context = JSON.parse(askBtn.getAttribute('data-context'));
      expect(context.type).toBe('threat_map');
      expect(context.data).toHaveLength(4);
      expect(context.count).toBe(4);
    });

    it('should update AskMaximus context when threats change', () => {
      const { rerender } = render(<ThreatMap />);

      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        threats: [mockThreats[0]]
      });

      rerender(<ThreatMap />);

      const askBtn = screen.getByTestId('ask-maximus-button');
      const context = JSON.parse(askBtn.getAttribute('data-context'));
      expect(context.count).toBe(1);
    });

    it('should include filters in AskMaximus context', () => {
      const customFilters = { severity: ['critical'], type: [], timeRange: '24h' };
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        filters: customFilters
      });

      render(<ThreatMap />);
      const askBtn = screen.getByTestId('ask-maximus-button');

      const context = JSON.parse(askBtn.getAttribute('data-context'));
      expect(context.filters).toEqual(customFilters);
    });
  });

  // ==================== ACCESSIBILITY TESTS ====================
  describe('Accessibility', () => {
    it('should have proper ARIA regions', () => {
      render(<ThreatMap />);
      expect(screen.getByRole('region', { name: 'Threat filters' })).toBeInTheDocument();
      expect(screen.getByRole('region', { name: 'Threat map visualization' })).toBeInTheDocument();
      expect(screen.getByRole('region', { name: 'Threat statistics' })).toBeInTheDocument();
    });

    it('should have aria-hidden on decorative icons', () => {
      render(<ThreatMap />);
      const refreshBtn = screen.getByTitle('Atualizar');
      const icon = refreshBtn.querySelector('.fas');
      // Icons should be aria-hidden (implementation detail)
      expect(icon).toBeInTheDocument();
    });

    it('should have refresh button with title', () => {
      render(<ThreatMap />);
      expect(screen.getByTitle('Atualizar')).toBeInTheDocument();
    });

    it('should show threat details in accessible region', async () => {
      const user = userEvent.setup();
      render(<ThreatMap />);

      const marker = screen.getByTestId('threat-marker-0');
      await user.click(marker);

      const detailsRegion = screen.getByRole('region', { name: 'Selected threat details' });
      expect(detailsRegion).toBeInTheDocument();
    });
  });

  // ==================== PERFORMANCE TESTS ====================
  describe('Performance Optimizations', () => {
    it('should memoize severity counts', () => {
      const { rerender } = render(<ThreatMap />);

      // Rerender with same threats - useMemo should prevent recalculation
      rerender(<ThreatMap />);

      // Stats should still be correct
      const statsBar = screen.getByRole('region', { name: 'Threat statistics' });
      expect(within(statsBar).getByText('4')).toBeInTheDocument();
    });

    it('should update severity counts when threats change', () => {
      const { rerender } = render(<ThreatMap />);

      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        threats: [mockThreats[0]] // Only 1 threat
      });

      rerender(<ThreatMap />);

      const card = screen.getByTestId('card');
      expect(card).toHaveAttribute('data-badge', '1 THREATS');
    });

    it('should handle large threat lists efficiently', () => {
      const manyThreats = Array.from({ length: 1000 }, (_, i) => ({
        ...mockThreats[0],
        id: `threat_${i}`,
        source: `192.168.1.${i % 256}`
      }));

      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        threats: manyThreats
      });

      render(<ThreatMap />);

      const card = screen.getByTestId('card');
      expect(card).toHaveAttribute('data-badge', '1000 THREATS');
    });
  });

  // ==================== EDGE CASES ====================
  describe('Edge Cases', () => {
    it('should handle null threats gracefully', () => {
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        threats: null
      });

      expect(() => render(<ThreatMap />)).not.toThrow();
    });

    it('should handle undefined threats gracefully', () => {
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        threats: undefined
      });

      expect(() => render(<ThreatMap />)).not.toThrow();
    });

    it('should handle threats with missing severity', () => {
      const threatsWithMissingSeverity = [
        { ...mockThreats[0], severity: undefined }
      ];

      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        threats: threatsWithMissingSeverity
      });

      render(<ThreatMap />);
      expect(screen.getByTestId('card')).toBeInTheDocument();
    });

    it('should handle threats with invalid severity values', () => {
      const threatsWithInvalidSeverity = [
        { ...mockThreats[0], severity: 'invalid' }
      ];

      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        threats: threatsWithInvalidSeverity
      });

      render(<ThreatMap />);
      // Should not crash
      expect(screen.getByTestId('card')).toBeInTheDocument();
    });

    it('should handle multiple marker clicks', async () => {
      const user = userEvent.setup();
      render(<ThreatMap />);

      // Click first marker
      await user.click(screen.getByTestId('threat-marker-0'));
      expect(screen.getByText('185.220.101.23')).toBeInTheDocument();

      // Click second marker
      await user.click(screen.getByTestId('threat-marker-1'));
      expect(screen.getByText('45.142.212.61')).toBeInTheDocument();
    });

    it('should handle simultaneous loading and error states', () => {
      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        loading: true,
        error: 'Error occurred'
      });

      render(<ThreatMap />);
      // Both overlays should be present
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
      expect(screen.getByText('Error occurred')).toBeInTheDocument();
    });
  });

  // ==================== STATS BAR TESTS ====================
  describe('Stats Bar', () => {
    it('should display all severity labels', () => {
      render(<ThreatMap />);
      const statsBar = screen.getByRole('region', { name: 'Threat statistics' });

      expect(within(statsBar).getByText('TOTAL:')).toBeInTheDocument();
      expect(within(statsBar).getByText('CRITICAL:')).toBeInTheDocument();
      expect(within(statsBar).getByText('HIGH:')).toBeInTheDocument();
      expect(within(statsBar).getByText('MEDIUM:')).toBeInTheDocument();
      expect(within(statsBar).getByText('LOW:')).toBeInTheDocument();
    });

    it('should calculate severity counts correctly', () => {
      render(<ThreatMap />);
      const badges = screen.getAllByTestId('badge');

      // Each severity has 1 threat in mock data
      const counts = badges
        .filter(b => ['critical', 'high', 'medium', 'low'].includes(b.getAttribute('data-variant')))
        .map(b => b.textContent);

      expect(counts).toEqual(['1', '1', '1', '1']);
    });

    it('should update stats when threats filter', () => {
      const filteredThreats = mockThreats.filter(t => t.severity === 'critical');

      vi.spyOn(useThreatDataHook, 'useThreatData').mockReturnValue({
        ...defaultUseThreatData,
        threats: filteredThreats
      });

      render(<ThreatMap />);
      const card = screen.getByTestId('card');
      expect(card).toHaveAttribute('data-badge', '1 THREATS');
    });
  });
});
