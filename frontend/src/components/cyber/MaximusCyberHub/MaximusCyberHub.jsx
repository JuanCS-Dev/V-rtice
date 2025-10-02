import React from 'react';
import { HubHeader } from './components/HubHeader';
import { TargetInput } from './components/TargetInput';
import { ServicesStatus } from './components/ServicesStatus';
import { InvestigationInfo } from './components/InvestigationInfo';
import { ExecutionTimeline } from './components/ExecutionTimeline';
import { FinalReport } from './components/FinalReport';
import { useAuroraHub } from './hooks/useAuroraHub';
import styles from './MaximusCyberHub.module.css';

export const MaximusCyberHub = () => {
  const {
    investigation,
    isAnalyzing,
    targetInput,
    setTargetInput,
    investigationType,
    setInvestigationType,
    analysisSteps,
    results,
    services,
    startInvestigation
  } = useAuroraHub();

  return (
    <div className={styles.container}>
      <HubHeader />

      <div className={styles.content}>
        {/* Painel de Controle */}
        <div className={styles.controlPanel}>
          <TargetInput
            targetInput={targetInput}
            setTargetInput={setTargetInput}
            investigationType={investigationType}
            setInvestigationType={setInvestigationType}
            isAnalyzing={isAnalyzing}
            onStart={startInvestigation}
          />

          <ServicesStatus services={services} />
        </div>

        {/* Timeline de Análise */}
        <div className={styles.timelinePanel}>
          <InvestigationInfo investigation={investigation} />

          <ExecutionTimeline analysisSteps={analysisSteps} />

          <FinalReport investigation={investigation} results={results} />
        </div>
      </div>
    </div>
  );
};

export default MaximusCyberHub;
