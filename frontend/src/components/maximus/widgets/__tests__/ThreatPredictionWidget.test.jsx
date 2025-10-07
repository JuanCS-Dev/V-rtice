/**
 * ThreatPredictionWidget Component Tests
 * =======================================
 *
 * Tests for FASE 8 Threat Prediction Widget
 * - Time-series analysis
 * - Bayesian inference
 * - Vulnerability exploitation forecasting
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThreatPredictionWidget } from '../ThreatPredictionWidget';
import * as maximusAI from '../../../../api/maximusAI';

// Mock API
vi.mock('../../../../api/maximusAI', () => ({
  predictThreats: vi.fn()
}));

describe('ThreatPredictionWidget Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render widget with header', () => {
    render(<ThreatPredictionWidget />);

    expect(screen.getByText('🔮 Threat Prediction')).toBeInTheDocument();
    expect(screen.getByText('FASE 8')).toBeInTheDocument();
  });

  it('should have time horizon selector with default 24h', () => {
    render(<ThreatPredictionWidget />);

    const select = screen.getByLabelText('Time Horizon (hours)');
    expect(select).toHaveValue('24');
    expect(screen.getByText('12h')).toBeInTheDocument();
    expect(screen.getByText('24h')).toBeInTheDocument();
    expect(screen.getByText('48h')).toBeInTheDocument();
    expect(screen.getByText('72h')).toBeInTheDocument();
  });

  it('should have min confidence selector with default 60%', () => {
    render(<ThreatPredictionWidget />);

    const select = screen.getByLabelText('Min Confidence');
    expect(select).toHaveValue('0.6');
  });

  it('should allow changing time horizon', async () => {
    const user = userEvent.setup();
    render(<ThreatPredictionWidget />);

    const select = screen.getByLabelText('Time Horizon (hours)');
    await user.selectOptions(select, '48');

    expect(select).toHaveValue('48');
  });

  it('should allow changing min confidence', async () => {
    const user = userEvent.setup();
    render(<ThreatPredictionWidget />);

    const select = screen.getByLabelText('Min Confidence');
    await user.selectOptions(select, '0.8');

    expect(select).toHaveValue('0.8');
  });

  it('should call predictThreats when run prediction clicked', async () => {
    const user = userEvent.setup();
    const mockResult = {
      predicted_attacks: [],
      vuln_forecast: [],
      hunting_recommendations: []
    };
    maximusAI.predictThreats.mockResolvedValue(mockResult);

    render(<ThreatPredictionWidget />);

    const predictBtn = screen.getByText('🎯 Run Prediction');
    await user.click(predictBtn);

    await waitFor(() => {
      expect(maximusAI.predictThreats).toHaveBeenCalledWith(
        {
          recent_alerts: [],
          historical_events: [],
          current_environment: 'production'
        },
        {
          timeHorizon: 24,
          minConfidence: 0.6,
          includeVulnForecast: true
        }
      );
    });
  });

  it('should show loading state during prediction', async () => {
    const user = userEvent.setup();
    maximusAI.predictThreats.mockImplementation(() =>
      new Promise(resolve => setTimeout(resolve, 1000))
    );

    render(<ThreatPredictionWidget />);

    const predictBtn = screen.getByText('🎯 Run Prediction');
    await user.click(predictBtn);

    expect(screen.getByText('⏳ Predicting...')).toBeInTheDocument();
    expect(predictBtn).toBeDisabled();
  });

  it('should display predicted threats', async () => {
    const user = userEvent.setup();
    const mockResult = {
      predicted_attacks: [
        { type: 'Ransomware', confidence: 0.85 },
        { type: 'DDoS', confidence: 0.72 }
      ],
      vuln_forecast: [],
      hunting_recommendations: []
    };
    maximusAI.predictThreats.mockResolvedValue(mockResult);

    render(<ThreatPredictionWidget />);

    await user.click(screen.getByText('🎯 Run Prediction'));

    await waitFor(() => {
      expect(screen.getByText('Predicted Threats')).toBeInTheDocument();
      expect(screen.getByText('Ransomware')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('DDoS')).toBeInTheDocument();
      expect(screen.getByText('72%')).toBeInTheDocument();
    });
  });

  it('should display vulnerability forecast', async () => {
    const user = userEvent.setup();
    const mockResult = {
      predicted_attacks: [],
      vuln_forecast: [
        { cve: 'CVE-2024-1234', exploit_probability: 0.91 },
        { cve: 'CVE-2024-5678', exploit_probability: 0.68 }
      ],
      hunting_recommendations: []
    };
    maximusAI.predictThreats.mockResolvedValue(mockResult);

    render(<ThreatPredictionWidget />);

    await user.click(screen.getByText('🎯 Run Prediction'));

    await waitFor(() => {
      expect(screen.getByText('Vulnerability Forecast')).toBeInTheDocument();
      expect(screen.getByText('CVE-2024-1234')).toBeInTheDocument();
      expect(screen.getByText('91%')).toBeInTheDocument();
      expect(screen.getByText('CVE-2024-5678')).toBeInTheDocument();
      expect(screen.getByText('68%')).toBeInTheDocument();
    });
  });

  it('should display hunting recommendations', async () => {
    const user = userEvent.setup();
    const mockResult = {
      predicted_attacks: [],
      vuln_forecast: [],
      hunting_recommendations: [
        'Monitor for unusual PowerShell activity',
        'Check for lateral movement indicators'
      ]
    };
    maximusAI.predictThreats.mockResolvedValue(mockResult);

    render(<ThreatPredictionWidget />);

    await user.click(screen.getByText('🎯 Run Prediction'));

    await waitFor(() => {
      expect(screen.getByText('Hunting Recommendations')).toBeInTheDocument();
      expect(screen.getByText('Monitor for unusual PowerShell activity')).toBeInTheDocument();
      expect(screen.getByText('Check for lateral movement indicators')).toBeInTheDocument();
    });
  });

  it('should show "no threats predicted" when empty', async () => {
    const user = userEvent.setup();
    const mockResult = {
      predicted_attacks: [],
      vuln_forecast: [],
      hunting_recommendations: []
    };
    maximusAI.predictThreats.mockResolvedValue(mockResult);

    render(<ThreatPredictionWidget />);

    await user.click(screen.getByText('🎯 Run Prediction'));

    await waitFor(() => {
      expect(screen.getByText('No threats predicted')).toBeInTheDocument();
      expect(screen.getByText('No vulnerabilities forecasted')).toBeInTheDocument();
      expect(screen.getByText('No recommendations')).toBeInTheDocument();
    });
  });

  it('should show placeholder before first prediction', () => {
    render(<ThreatPredictionWidget />);

    expect(screen.getByText(/Configure parameters and run prediction/)).toBeInTheDocument();
  });

  it('should hide placeholder after prediction', async () => {
    const user = userEvent.setup();
    const mockResult = {
      predicted_attacks: [],
      vuln_forecast: [],
      hunting_recommendations: []
    };
    maximusAI.predictThreats.mockResolvedValue(mockResult);

    render(<ThreatPredictionWidget />);

    await user.click(screen.getByText('🎯 Run Prediction'));

    await waitFor(() => {
      expect(screen.queryByText(/Configure parameters and run prediction/)).not.toBeInTheDocument();
    });
  });

  it('should handle prediction with custom parameters', async () => {
    const user = userEvent.setup();
    const mockResult = { predicted_attacks: [], vuln_forecast: [], hunting_recommendations: [] };
    maximusAI.predictThreats.mockResolvedValue(mockResult);

    render(<ThreatPredictionWidget />);

    // Change parameters
    await user.selectOptions(screen.getByLabelText('Time Horizon (hours)'), '72');
    await user.selectOptions(screen.getByLabelText('Min Confidence'), '0.8');

    await user.click(screen.getByText('🎯 Run Prediction'));

    await waitFor(() => {
      expect(maximusAI.predictThreats).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          timeHorizon: 72,
          minConfidence: 0.8
        })
      );
    });
  });

  it('should not crash on null predictions', async () => {
    const user = userEvent.setup();
    const mockResult = {
      predicted_attacks: null,
      vuln_forecast: null,
      hunting_recommendations: null
    };
    maximusAI.predictThreats.mockResolvedValue(mockResult);

    render(<ThreatPredictionWidget />);

    await user.click(screen.getByText('🎯 Run Prediction'));

    await waitFor(() => {
      expect(screen.getByText('No threats predicted')).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    const user = userEvent.setup();
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    maximusAI.predictThreats.mockRejectedValue(new Error('Prediction failed'));

    render(<ThreatPredictionWidget />);

    await user.click(screen.getByText('🎯 Run Prediction'));

    await waitFor(() => {
      expect(consoleError).toHaveBeenCalledWith('Prediction failed:', expect.any(Error));
    });

    consoleError.mockRestore();
  });

  it('should not display results on API failure', async () => {
    const user = userEvent.setup();
    const mockResult = { success: false };
    maximusAI.predictThreats.mockResolvedValue(mockResult);

    render(<ThreatPredictionWidget />);

    await user.click(screen.getByText('🎯 Run Prediction'));

    await waitFor(() => {
      expect(screen.getByText('🎯 Run Prediction')).toBeInTheDocument();
    });

    // Results should not be displayed
    expect(screen.queryByText('Predicted Threats')).not.toBeInTheDocument();
  });
});
