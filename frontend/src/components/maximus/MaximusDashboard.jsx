/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MAXIMUS AI DASHBOARD - O Cérebro do Vértice
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Dashboard cinematográfico para visualizar os componentes de AI do MAXIMUS:
 * - ORÁCULO: Self-improvement engine
 * - EUREKA: Deep malware analysis
 * - AI INSIGHTS: Unified intelligence view
 *
 * Design Philosophy: Cyberpunk meets Military Intelligence
 */

import React, { useState } from 'react';
import logger from '@/utils/logger';
import { useTranslation } from 'react-i18next';
import { OraculoPanel } from './OraculoPanel';
import { EurekaPanel } from './EurekaPanel';
import { AIInsightsPanel } from './AIInsightsPanel';
import { MaximusAI3Panel } from './MaximusAI3Panel';
import { MaximusCore } from './MaximusCore';
import { WorkflowsPanel } from './WorkflowsPanel';
import MaximusTerminal from './MaximusTerminal';
import { ConsciousnessPanel } from './ConsciousnessPanel';
import { AdaptiveImmunityPanel } from './AdaptiveImmunityPanel';
import { BackgroundEffect } from './BackgroundEffects';
import SkipLink from '../shared/SkipLink';
import { DashboardFooter } from '../shared/DashboardFooter';
import useKeyboardNavigation from '../../hooks/useKeyboardNavigation';
import { useClock } from '../../hooks/useClock';
import { useMaximusHealth } from '../../hooks/useMaximusHealth';
import { useBrainActivity } from '../../hooks/useBrainActivity';
import { MaximusHeader } from './components/MaximusHeader';
import styles from './MaximusDashboard.module.css';

export const MaximusDashboard = ({ setCurrentView }) => {
  const { t } = useTranslation();
  const [activePanel, setActivePanel] = useState('core');
  const [backgroundEffect, setBackgroundEffect] = useState('matrix');

  // Custom hooks
  const currentTime = useClock();
  const { aiStatus, setAiStatus } = useMaximusHealth();
  const brainActivity = useBrainActivity();

  // Debug log
  logger.debug('🧠 MAXIMUS Dashboard renderizando...', { backgroundEffect, activePanel });

  const panels = [
    { id: 'core', name: t('dashboard.maximus.panels.core'), icon: '🤖', description: t('dashboard.maximus.panelDescriptions.core') },
    { id: 'workflows', name: t('dashboard.maximus.panels.workflows'), icon: '🔄', description: t('dashboard.maximus.panelDescriptions.workflows') },
    { id: 'terminal', name: t('dashboard.maximus.panels.terminal'), icon: '⚡', description: t('dashboard.maximus.panelDescriptions.terminal') },
    { id: 'consciousness', name: 'Consciousness', icon: '🧠', description: 'Real-time consciousness monitoring (TIG, ESGT, MCEA)' },
    { id: 'adaptive-immunity', name: 'Adaptive Immunity', icon: '🧬', description: 'ML-powered patch validation monitoring (Oráculo→Eureka→Crisol)' },
    { id: 'insights', name: t('dashboard.maximus.panels.insights'), icon: '💡', description: t('dashboard.maximus.panelDescriptions.insights') },
    { id: 'ai3', name: t('dashboard.maximus.panels.ai3'), icon: '🧬', description: t('dashboard.maximus.panelDescriptions.ai3') },
    { id: 'oraculo', name: t('dashboard.maximus.panels.oracle'), icon: '🔮', description: t('dashboard.maximus.panelDescriptions.oracle') },
    { id: 'eureka', name: t('dashboard.maximus.panels.eureka'), icon: '🔬', description: t('dashboard.maximus.panelDescriptions.eureka') }
  ];

  const { getItemProps } = useKeyboardNavigation({
    itemCount: panels.length,
    onSelect: (index) => setActivePanel(panels[index].id),
    orientation: 'horizontal',
    loop: true
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'text-green-400';
      case 'idle': return 'text-orange-400';
      case 'running': return 'text-red-400 animate-pulse';
      case 'degraded': return 'text-yellow-400';
      case 'offline': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const renderActivePanel = () => {
    switch (activePanel) {
      case 'core':
        return <MaximusCore aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'workflows':
        return <WorkflowsPanel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'terminal':
        return <MaximusTerminal />;
      case 'consciousness':
        return <ConsciousnessPanel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'adaptive-immunity':
        return <AdaptiveImmunityPanel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'ai3':
        return <MaximusAI3Panel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'oraculo':
        return <OraculoPanel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'eureka':
        return <EurekaPanel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
      case 'insights':
        return <AIInsightsPanel aiStatus={aiStatus} brainActivity={brainActivity} />;
      default:
        return <MaximusCore aiStatus={aiStatus} setAiStatus={setAiStatus} />;
    }
  };

  // Calculate active brain activities
  const activeBrainCount = brainActivity.filter(a => a.severity !== 'info').length;
  const totalEvents = brainActivity.length;

  return (
    <div className={styles.maximusDashboard}>
      <SkipLink href="#main-content">{t('accessibility.skipToMain')}</SkipLink>

      {/* Animated Background Grid */}
      <div className={styles.maximusGridBg}></div>

      {/* Background Effect (Scanline/Matrix/Particles) */}
      <BackgroundEffect effectId={backgroundEffect} />

      {/* HEADER - Mission Control */}
      <MaximusHeader
        aiStatus={aiStatus}
        currentTime={currentTime}
        activePanel={activePanel}
        panels={panels}
        setActivePanel={setActivePanel}
        setCurrentView={setCurrentView}
        getItemProps={getItemProps}
        getStatusColor={getStatusColor}
        backgroundEffect={backgroundEffect}
        onEffectChange={setBackgroundEffect}
      />

      {/* MAIN CONTENT - Active Panel */}
      <main id="main-content" className={styles.maximusMain}>
        {renderActivePanel()}
      </main>

      {/* FOOTER - Unified */}
      <DashboardFooter
        moduleName="MAXIMUS AI CORE"
        classification="TOP SECRET"
        statusItems={[
          { label: 'AI STATUS', value: (aiStatus?.core?.status || 'OFFLINE').toUpperCase(), online: aiStatus?.core?.status === 'online' },
          { label: 'BRAIN ACTIVITY', value: activeBrainCount > 0 ? 'PROCESSING' : 'IDLE', online: true }
        ]}
        metricsItems={[
          { label: 'EVENTS', value: totalEvents },
          { label: 'ACTIVE PANEL', value: activePanel.toUpperCase() }
        ]}
        showTimestamp={true}
      />
    </div>
  );
};

export default MaximusDashboard;
