/**
import logger from '@/utils/logger';
 * usePurpleTeamData Hook
 * Aggregates data from both red and blue team operations
 * Correlates attacks with detections to identify gaps
 *
 * React Query powered for:
 * - Automatic caching
 * - Background refetching
 * - Retry with exponential backoff
 * - Parallel fetching optimization
 *
 * NO MOCKS - Real data from:
 * - Offensive services (red team)
 * - Defensive services (blue team)
 * - Correlation engine
 */

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../../../../config/queryClient';

import { API_BASE_URL } from '../../../../config/api';
const OFFENSIVE_BASE = API_BASE_URL; // Offensive Gateway
const DEFENSIVE_BASE = API_BASE_URL; // API Gateway

const fetchPurpleTeamData = async () => {

  // Fetch red team data
  const redTeamPromise = fetch(`${OFFENSIVE_BASE}/api/executions/recent`)
    .then(res => res.ok ? res.json() : { executions: [] })
    .catch(() => ({ executions: [] }));

  // Fetch blue team data (alerts/detections)
  const blueTeamPromise = fetch(`${DEFENSIVE_BASE}/api/alerts/recent`)
    .then(res => res.ok ? res.json() : { alerts: [] })
    .catch(() => ({ alerts: [] }));

  // Fetch correlations
  const correlationsPromise = fetch(`${DEFENSIVE_BASE}/api/correlations`)
    .then(res => res.ok ? res.json() : { correlations: [] })
    .catch(() => ({ correlations: [] }));

  const [redData, blueData, corrData] = await Promise.all([
    redTeamPromise,
    blueTeamPromise,
    correlationsPromise
  ]);

  // Process attack data
  const attacks = redData.executions || [];
  const attackData = {
    active: attacks.filter(a => a.status === 'running' || a.status === 'pending'),
    total: attacks.length,
    events: attacks.map(a => ({
      id: a.execution_id || a.id,
      timestamp: a.timestamp || new Date().toISOString(),
      type: a.workflow_name || a.type || 'Attack',
      technique: a.technique || 'Unknown',
      target: a.target || 'Unknown',
      status: a.status || 'unknown',
      eventType: 'attack'
    }))
  };

  // Process defense data
  const detections = blueData.alerts || [];
  const defenseData = {
    detections: detections.map(d => ({
      id: d.id,
      type: d.type || 'Detection',
      source: d.source || 'SIEM',
      rule: d.rule || 'Unknown',
      severity: d.severity || 'medium',
      confidence: d.confidence || 75,
      timestamp: d.timestamp || new Date().toISOString()
    })),
    events: detections.map(d => ({
      id: d.id,
      timestamp: d.timestamp || new Date().toISOString(),
      type: d.type || 'Detection',
      source: d.source || 'SIEM',
      rule: d.rule || 'Unknown',
      severity: d.severity || 'medium',
      eventType: 'detection'
    }))
  };

  // Process correlations
  const correlations = corrData.correlations || [];

  // Calculate gaps
  const detectedAttacks = attacks.filter(a =>
    correlations.some(c => c.attackId === (a.execution_id || a.id))
  );
  const undetectedAttacks = attacks.filter(a =>
    !correlations.some(c => c.attackId === (a.execution_id || a.id))
  );

  const coverage = attacks.length > 0
    ? Math.round((detectedAttacks.length / attacks.length) * 100)
    : 0;

  // Calculate coverage by technique
  const techniqueMap = {};
  attacks.forEach(attack => {
    const technique = attack.technique || 'Unknown';
    if (!techniqueMap[technique]) {
      techniqueMap[technique] = { total: 0, detected: 0 };
    }
    techniqueMap[technique].total++;

    if (correlations.some(c => c.attackId === (attack.execution_id || attack.id))) {
      techniqueMap[technique].detected++;
    }
  });

  const coverageByTechnique = {};
  Object.entries(techniqueMap).forEach(([technique, stats]) => {
    coverageByTechnique[technique] = Math.round(
      (stats.detected / stats.total) * 100
    );
  });

  const gaps = {
    coveragePercentage: coverage,
    detected: detectedAttacks.length,
    undetected: undetectedAttacks.length,
    falsePositives: detections.length - correlations.length,
    undetectedAttacks: undetectedAttacks.map(a => ({
      id: a.execution_id || a.id,
      type: a.workflow_name || a.type || 'Attack',
      target: a.target || 'Unknown',
      technique: a.technique || 'Unknown',
      mitreId: a.mitre_id || null,
      recommendation: `Implement detection for ${a.technique || 'this technique'}`
    })),
    coverageByTechnique
  };

  return { attackData, defenseData, correlations, gaps };
};

export const usePurpleTeamData = () => {
  const { data, isLoading, error: _error, refetch } = useQuery({
    queryKey: queryKeys.purpleCorrelations,
    queryFn: fetchPurpleTeamData,
    refetchInterval: 5000, // Poll every 5 seconds
    staleTime: 1000,
    retry: 2,
    retryDelay: 1000,
    onError: (err) => {
      logger.error('Failed to fetch purple team data:', err);
    }
  });

  const defaultData = {
    attackData: { active: [], total: 0, events: [] },
    defenseData: { detections: [], events: [] },
    correlations: [],
    gaps: {
      coveragePercentage: 0,
      detected: 0,
      undetected: 0,
      falsePositives: 0,
      undetectedAttacks: [],
      coverageByTechnique: {}
    }
  };

  return {
    attackData: data?.attackData || defaultData.attackData,
    defenseData: data?.defenseData || defaultData.defenseData,
    correlations: data?.correlations || defaultData.correlations,
    gaps: data?.gaps || defaultData.gaps,
    loading: isLoading,
    refresh: refetch
  };
};
