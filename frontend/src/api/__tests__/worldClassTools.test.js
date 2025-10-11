/**
 * Testes Automatizados - World Class Tools API Client
 * Projeto Vértice - PASSO 5: TESTING & VALIDATION
 *
 * Objetivo: Garantir que o API client funciona corretamente e mantém compatibilidade
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  executeTool,
  executeParallel,
  searchExploits,
  socialMediaInvestigation,
  searchBreachData,
  detectAnomalies,
  getConfidenceBadge,
  getSeverityColor,
  isResultActionable,
  formatExecutionTime
} from '../worldClassTools';

describe('World Class Tools API Client', () => {

  beforeEach(() => {
    // Reset mocks antes de cada teste
    global.fetch.mockReset();
  });

  describe('executeTool', () => {
    it('deve executar uma ferramenta com sucesso', async () => {
      const mockResponse = {
        success: true,
        result: {
          cve_id: 'CVE-2024-1086',
          cvss_score: 9.8,
          confidence: 95
        },
        execution_time_ms: 234
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await executeTool('exploit_search', { cve_id: 'CVE-2024-1086' });

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8017/tools/world-class/execute',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      );
    });

    it('deve lançar erro quando a API retorna erro', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Invalid CVE ID' })
      });

      await expect(
        executeTool('exploit_search', { cve_id: 'INVALID' })
      ).rejects.toThrow('Invalid CVE ID');
    });

    it('deve lançar erro em caso de falha de rede', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      await expect(
        executeTool('exploit_search', { cve_id: 'CVE-2024-1086' })
      ).rejects.toThrow('Network error');
    });
  });

  describe('executeParallel', () => {
    it('deve executar múltiplas ferramentas em paralelo', async () => {
      const mockResponse = {
        results: [
          { success: true, result: { exploits_found: 3 } },
          { success: true, result: { profiles_found: 2 } }
        ],
        summary: { total: 2, successful: 2, failed: 0 }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const executions = [
        { tool_name: 'exploit_search', tool_input: { cve_id: 'CVE-2024-1086' } },
        { tool_name: 'social_media_deep_dive', tool_input: { username: 'test' } }
      ];

      const response = await executeParallel(executions);

      expect(response.results).toHaveLength(2);
      expect(response.summary.successful).toBe(2);
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it('deve lidar com falhas parciais em execução paralela', async () => {
      const mockResponse = {
        results: [
          { success: true, result: {} },
          { success: false, error: 'Internal error' }
        ],
        summary: { total: 2, successful: 1, failed: 1 }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const executions = [
        { tool_name: 'exploit_search', tool_input: { cve_id: 'CVE-2024-1086' } },
        { tool_name: 'social_media_deep_dive', tool_input: { username: 'test' } }
      ];

      const response = await executeParallel(executions);

      expect(response.results[0]).toHaveProperty('success', true);
      expect(response.results[1]).toHaveProperty('success', false);
      expect(response.summary.failed).toBe(1);
    });
  });

  describe('searchExploits', () => {
    it('deve chamar executeTool com parâmetros corretos', async () => {
      const mockResult = {
        success: true,
        result: {
          cve_id: 'CVE-2024-1086',
          exploits_found: 3,
          cvss_score: 9.8
        }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResult
      });

      const result = await searchExploits('CVE-2024-1086', {
        includePoc: true,
        includeMetasploit: true
      });

      expect(result.result.cve_id).toBe('CVE-2024-1086');
      expect(result.result.exploits_found).toBe(3);

      const fetchCall = global.fetch.mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);
      expect(body.tool_name).toBe('exploit_search');
      expect(body.tool_input.cve_id).toBe('CVE-2024-1086');
      expect(body.tool_input.include_poc).toBe(true);
    });
  });

  describe('socialMediaInvestigation', () => {
    it('deve buscar perfis em redes sociais', async () => {
      const mockResult = {
        success: true,
        result: {
          username: 'elonmusk',
          profiles_found: 2,
          risk_score: 15
        }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResult
      });

      const result = await socialMediaInvestigation('elonmusk', {
        platforms: ['twitter', 'linkedin'],
        deepAnalysis: true
      });

      expect(result.result.username).toBe('elonmusk');
      expect(result.result.profiles_found).toBe(2);

      const fetchCall = global.fetch.mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);
      expect(body.tool_name).toBe('social_media_deep_dive');
      expect(body.tool_input.target).toBe('elonmusk');
      expect(body.tool_input.platforms).toEqual(['twitter', 'linkedin']);
    });
  });

  describe('searchBreachData', () => {
    it('deve buscar dados de vazamentos', async () => {
      const mockResult = {
        success: true,
        result: {
          identifier: 'test@example.com',
          breaches_found: 3,
          risk_score: 60
        }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResult
      });

      const result = await searchBreachData('test@example.com', {
        queryType: 'email'
      });

      expect(result.result.identifier).toBe('test@example.com');
      expect(result.result.breaches_found).toBe(3);

      const fetchCall = global.fetch.mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);
      expect(body.tool_name).toBe('breach_data_search');
      expect(body.tool_input.query).toBe('test@example.com');
    });
  });

  describe('detectAnomalies', () => {
    it('deve detectar anomalias em dados', async () => {
      const mockResult = {
        success: true,
        result: {
          data_points_analyzed: 43,
          anomalies_detected: 3,
          method: 'isolation_forest'
        }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResult
      });

      const data = [1.2, 1.3, 15.7, 1.1, 0.2, 1.4];
      const result = await detectAnomalies(data, {
        method: 'isolation_forest',
        sensitivity: 0.05
      });

      expect(result.result.anomalies_detected).toBe(3);

      const fetchCall = global.fetch.mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);
      expect(body.tool_name).toBe('anomaly_detection');
      expect(body.tool_input.data).toEqual(data);
      expect(body.tool_input.method).toBe('isolation_forest');
    });
  });

  describe('Utility Functions', () => {
    describe('getConfidenceBadge', () => {
      it('deve retornar badge VERY HIGH para confiança >= 90', () => {
        const badge = getConfidenceBadge(95);
        expect(badge.label).toBe('VERY HIGH');
        expect(badge.color).toBe('#00ff00');
        expect(badge.icon).toBe('🟢');
      });

      it('deve retornar badge HIGH para confiança >= 75', () => {
        const badge = getConfidenceBadge(80);
        expect(badge.label).toBe('HIGH');
        expect(badge.color).toBe('#00ffff');
        expect(badge.icon).toBe('🔵');
      });

      it('deve retornar badge MEDIUM para confiança >= 50', () => {
        const badge = getConfidenceBadge(60);
        expect(badge.label).toBe('MEDIUM');
        expect(badge.color).toBe('#ffaa00');
        expect(badge.icon).toBe('🟡');
      });

      it('deve retornar badge LOW para confiança >= 25', () => {
        const badge = getConfidenceBadge(30);
        expect(badge.label).toBe('LOW');
        expect(badge.color).toBe('#ff4000');
        expect(badge.icon).toBe('🟠');
      });

      it('deve retornar badge VERY LOW para confiança < 25', () => {
        const badge = getConfidenceBadge(10);
        expect(badge.label).toBe('VERY LOW');
        expect(badge.color).toBe('#ff0040');
        expect(badge.icon).toBe('🔴');
      });
    });

    describe('getSeverityColor', () => {
      it('deve retornar cor correta para cada severidade', () => {
        expect(getSeverityColor('CRITICAL')).toBe('#ff0040');
        expect(getSeverityColor('HIGH')).toBe('#ff4000');
        expect(getSeverityColor('MEDIUM')).toBe('#ffaa00');
        expect(getSeverityColor('LOW')).toBe('#00aa00');
        expect(getSeverityColor('INFO')).toBe('#00aaff');
      });

      it('deve retornar cor padrão para severidade desconhecida', () => {
        expect(getSeverityColor('UNKNOWN')).toBe('#00aaff');
      });
    });

    describe('isResultActionable', () => {
      it('deve retornar true para resultado com confiança alta', () => {
        const result = { confidence: 85 };
        expect(isResultActionable(result)).toBe(true);
      });

      it('deve retornar true para resultado com is_actionable true', () => {
        const result = { is_actionable: true, confidence: 65 };
        expect(isResultActionable(result)).toBe(true);
      });

      it('deve retornar false para resultado com confiança baixa', () => {
        const result = { confidence: 65 };
        expect(isResultActionable(result)).toBe(false);
      });

      it('deve retornar false quando confidence não existe', () => {
        const result = {};
        expect(isResultActionable(result)).toBe(false);
      });
    });

    describe('formatExecutionTime', () => {
      it('deve formatar tempo em ms quando < 1000ms', () => {
        expect(formatExecutionTime(234)).toBe('234ms');
        expect(formatExecutionTime(999)).toBe('999ms');
      });

      it('deve formatar tempo em segundos quando >= 1000ms', () => {
        expect(formatExecutionTime(1000)).toBe('1.00s');
        expect(formatExecutionTime(2345)).toBe('2.35s');
        expect(formatExecutionTime(10000)).toBe('10.00s');
      });

      it('deve lidar com valores zero', () => {
        expect(formatExecutionTime(0)).toBe('0ms');
      });
    });
  });
});
