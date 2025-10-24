/**
 * ImmuneEnhancementWidget Component Tests
 * ========================================
 *
 * Tests for FASE 9 Immune Enhancement Widget
 * - False Positive Suppression (Regulatory T-Cells)
 * - Memory Consolidation (STM → LTM)
 * - Long-Term Memory Query
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ImmuneEnhancementWidget } from '../ImmuneEnhancementWidget';
import { suppressFalsePositives, consolidateMemory, queryLongTermMemory } from '../../../../api/maximusAI';

// Mock API functions with factory function
vi.mock('../../../../api/maximusAI', () => ({
  suppressFalsePositives: vi.fn(() => Promise.resolve({ total_alerts: 0, suppressed_count: 0 })),
  consolidateMemory: vi.fn(() => Promise.resolve({ patterns_count: 0, ltm_entries_created: 0 })),
  queryLongTermMemory: vi.fn(() => Promise.resolve({ memories: [] }))
}));

describe('ImmuneEnhancementWidget Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Reset mocks to default implementations
    suppressFalsePositives.mockResolvedValue({ total_alerts: 0, suppressed_count: 0 });
    consolidateMemory.mockResolvedValue({ patterns_count: 0, ltm_entries_created: 0 });
    queryLongTermMemory.mockResolvedValue({ memories: [] });
  });

  it('should render with default FP Suppression tab active', () => {
    render(<ImmuneEnhancementWidget />);

    expect(screen.getByText('🛡️ Immune Enhancement')).toBeInTheDocument();
    expect(screen.getByText('FASE 9')).toBeInTheDocument();
    expect(screen.getByText('FP Suppression')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/alert_001/)).toBeInTheDocument();
  });

  it('should have three tabs', () => {
    render(<ImmuneEnhancementWidget />);

    expect(screen.getByText('FP Suppression')).toBeInTheDocument();
    expect(screen.getByText('Memory STM → LTM')).toBeInTheDocument();
    expect(screen.getByText('LTM Query')).toBeInTheDocument();
  });

  it('should switch to consolidation tab', async () => {
    const user = userEvent.setup();
    render(<ImmuneEnhancementWidget />);

    const consolidationTab = screen.getByText('Memory STM → LTM');
    await user.click(consolidationTab);

    expect(screen.getByText(/Trigger memory consolidation cycle/)).toBeInTheDocument();
    expect(screen.getByText('💾 Run Consolidation')).toBeInTheDocument();
  });

  it('should switch to LTM Query tab', async () => {
    const user = userEvent.setup();
    render(<ImmuneEnhancementWidget />);

    const ltmTab = screen.getByText('LTM Query');
    await user.click(ltmTab);

    expect(screen.getByText(/Query long-term immunological memory/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter search query...')).toBeInTheDocument();
  });

  describe('FP Suppression Tab', () => {
    it('should show error when alerts input is empty', async () => {
      const user = userEvent.setup();
      render(<ImmuneEnhancementWidget />);

      const suppressBtn = screen.getByText('🔬 Suppress False Positives');
      await user.click(suppressBtn);

      await waitFor(() => {
        expect(screen.getByText(/Please provide alerts in JSON format/)).toBeInTheDocument();
      });
    });

    it('should show error for invalid JSON', async () => {
      const user = userEvent.setup();
      render(<ImmuneEnhancementWidget />);

      const textarea = screen.getByPlaceholderText(/alert_001/);
      await user.type(textarea, 'invalid json{');

      const suppressBtn = screen.getByText('🔬 Suppress False Positives');
      await user.click(suppressBtn);

      await waitFor(() => {
        expect(screen.getByText(/Unexpected token/i)).toBeInTheDocument();
      });
    });

    it('should show error for non-array input', async () => {
      const user = userEvent.setup();
      render(<ImmuneEnhancementWidget />);

      const textarea = screen.getByPlaceholderText(/alert_001/);
      await user.clear(textarea);
      await user.type(textarea, '{"not": "array"}');

      const suppressBtn = screen.getByText('🔬 Suppress False Positives');
      await user.click(suppressBtn);

      await waitFor(() => {
        expect(screen.getByText(/Alerts must be a non-empty array/)).toBeInTheDocument();
      });
    });

    it('should call suppressFalsePositives with valid alerts', async () => {
      const user = userEvent.setup();
      const mockResult = {
        total_alerts: 2,
        suppressed_count: 1,
        avg_tolerance_score: 0.85
      };
      suppressFalsePositives.mockResolvedValue(mockResult);

      render(<ImmuneEnhancementWidget />);

      const alertsJSON = JSON.stringify([
        { id: 'alert_001', severity: 'high', entity: '192.168.1.10', type: 'port_scan' },
        { id: 'alert_002', severity: 'medium', entity: '10.0.0.5', type: 'brute_force' }
      ]);

      const textarea = screen.getByPlaceholderText(/alert_001/);
      await user.clear(textarea);
      await user.type(textarea, alertsJSON);

      const suppressBtn = screen.getByText('🔬 Suppress False Positives');
      await user.click(suppressBtn);

      await waitFor(() => {
        expect(suppressFalsePositives).toHaveBeenCalledWith(
          expect.any(Array),
          0.7
        );
      });
    });

    it('should display FP suppression results', async () => {
      const user = userEvent.setup();
      const mockResult = {
        total_alerts: 5,
        suppressed_count: 2,
        avg_tolerance_score: 0.78
      };
      suppressFalsePositives.mockResolvedValue(mockResult);

      render(<ImmuneEnhancementWidget />);

      const alertsJSON = '[{"id":"a1"}]';
      const textarea = screen.getByPlaceholderText(/alert_001/);
      await user.clear(textarea);
      await user.type(textarea, alertsJSON);

      const suppressBtn = screen.getByText('🔬 Suppress False Positives');
      await user.click(suppressBtn);

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument(); // total_alerts
        expect(screen.getByText('2')).toBeInTheDocument(); // suppressed_count
        expect(screen.getByText('78.0%')).toBeInTheDocument(); // avg_tolerance_score
      });
    });

    it('should disable button when loading', async () => {
      const user = userEvent.setup();
      suppressFalsePositives.mockImplementation(() =>
        new Promise(resolve => setTimeout(resolve, 1000))
      );

      render(<ImmuneEnhancementWidget />);

      const alertsJSON = '[{"id":"a1"}]';
      const textarea = screen.getByPlaceholderText(/alert_001/);
      await user.clear(textarea);
      await user.type(textarea, alertsJSON);

      const suppressBtn = screen.getByText('🔬 Suppress False Positives');
      await user.click(suppressBtn);

      expect(screen.getByText('⏳ Evaluating...')).toBeInTheDocument();
      expect(suppressBtn).toBeDisabled();
    });
  });

  describe('Memory Consolidation Tab', () => {
    it('should call consolidateMemory when clicked', async () => {
      const user = userEvent.setup();
      const mockResult = {
        patterns_count: 12,
        ltm_entries_created: 8,
        duration_ms: 245
      };
      consolidateMemory.mockResolvedValue(mockResult);

      render(<ImmuneEnhancementWidget />);

      await user.click(screen.getByText('Memory STM → LTM'));
      await user.click(screen.getByText('💾 Run Consolidation'));

      await waitFor(() => {
        expect(consolidateMemory).toHaveBeenCalledWith({
          manual: true,
          threshold: 0.7
        });
      });
    });

    it('should display consolidation results', async () => {
      const user = userEvent.setup();
      const mockResult = {
        patterns_count: 15,
        ltm_entries_created: 10,
        duration_ms: 380
      };
      consolidateMemory.mockResolvedValue(mockResult);

      render(<ImmuneEnhancementWidget />);

      await user.click(screen.getByText('Memory STM → LTM'));
      await user.click(screen.getByText('💾 Run Consolidation'));

      await waitFor(() => {
        expect(screen.getByText('15')).toBeInTheDocument(); // patterns_count
        expect(screen.getByText('10')).toBeInTheDocument(); // ltm_entries_created
        expect(screen.getByText('380ms')).toBeInTheDocument(); // duration_ms
      });
    });

    it('should show loading state during consolidation', async () => {
      const user = userEvent.setup();
      consolidateMemory.mockImplementation(() =>
        new Promise(resolve => setTimeout(resolve, 1000))
      );

      render(<ImmuneEnhancementWidget />);

      await user.click(screen.getByText('Memory STM → LTM'));
      const consolidateBtn = screen.getByText('💾 Run Consolidation');
      await user.click(consolidateBtn);

      expect(screen.getByText('⏳ Consolidating...')).toBeInTheDocument();
      expect(consolidateBtn).toBeDisabled();
    });
  });

  describe('LTM Query Tab', () => {
    it('should have default query value', async () => {
      const user = userEvent.setup();
      render(<ImmuneEnhancementWidget />);

      await user.click(screen.getByText('LTM Query'));

      const input = screen.getByPlaceholderText('Enter search query...');
      expect(input).toHaveValue('ransomware campaigns');
    });

    it('should allow changing query', async () => {
      const user = userEvent.setup();
      render(<ImmuneEnhancementWidget />);

      await user.click(screen.getByText('LTM Query'));

      const input = screen.getByPlaceholderText('Enter search query...');
      await user.clear(input);
      await user.type(input, 'lateral movement');

      expect(input).toHaveValue('lateral movement');
    });

    it('should call queryLongTermMemory with correct parameters', async () => {
      const user = userEvent.setup();
      const mockResult = {
        memories: [
          { pattern_type: 'Attack Chain', importance: 0.92, description: 'Advanced APT pattern' }
        ]
      };
      queryLongTermMemory.mockResolvedValue(mockResult);

      render(<ImmuneEnhancementWidget />);

      await user.click(screen.getByText('LTM Query'));
      await user.click(screen.getByText('🔍 Search LTM'));

      await waitFor(() => {
        expect(queryLongTermMemory).toHaveBeenCalledWith(
          'ransomware campaigns',
          { limit: 5, minImportance: 0.7 }
        );
      });
    });

    it('should display LTM query results', async () => {
      const user = userEvent.setup();
      const mockResult = {
        memories: [
          { pattern_type: 'Ransomware', importance: 0.95, description: 'WannaCry-like behavior' },
          { pattern_type: 'Lateral Movement', importance: 0.85, description: 'SMB enumeration' }
        ]
      };
      queryLongTermMemory.mockResolvedValue(mockResult);

      render(<ImmuneEnhancementWidget />);

      await user.click(screen.getByText('LTM Query'));
      await user.click(screen.getByText('🔍 Search LTM'));

      await waitFor(() => {
        expect(screen.getByText('Ransomware')).toBeInTheDocument();
        expect(screen.getByText('95% importance')).toBeInTheDocument();
        expect(screen.getByText('WannaCry-like behavior')).toBeInTheDocument();
        expect(screen.getByText('Lateral Movement')).toBeInTheDocument();
      });
    });

    it('should show "no memories" when results are empty', async () => {
      const user = userEvent.setup();
      const mockResult = { memories: [] };
      queryLongTermMemory.mockResolvedValue(mockResult);

      render(<ImmuneEnhancementWidget />);

      await user.click(screen.getByText('LTM Query'));
      await user.click(screen.getByText('🔍 Search LTM'));

      await waitFor(() => {
        expect(screen.getByText('No memories found')).toBeInTheDocument();
      });
    });

    it('should disable search when query is empty', async () => {
      const user = userEvent.setup();
      render(<ImmuneEnhancementWidget />);

      await user.click(screen.getByText('LTM Query'));

      const input = screen.getByPlaceholderText('Enter search query...');
      await user.clear(input);

      const searchBtn = screen.getByText('🔍 Search LTM');
      expect(searchBtn).toBeDisabled();
    });
  });

  it('should handle API errors gracefully', async () => {
    const user = userEvent.setup();
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    suppressFalsePositives.mockRejectedValue(new Error('API Error'));

    render(<ImmuneEnhancementWidget />);

    const alertsJSON = '[{"id":"a1"}]';
    const textarea = screen.getByPlaceholderText(/alert_001/);
    await user.type(textarea, alertsJSON);

    await user.click(screen.getByText('🔬 Suppress False Positives'));

    await waitFor(() => {
      expect(consoleError).toHaveBeenCalled();
    });

    consoleError.mockRestore();
  });
});
