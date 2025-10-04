import React from 'react';
import AskMaximusButton from '../../shared/AskMaximusButton';
import { HubHeader } from './components/HubHeader';
import { TargetInput } from './components/TargetInput';
import { ServicesStatus } from './components/ServicesStatus';
import { InvestigationInfo } from './components/InvestigationInfo';
import { ExecutionTimeline } from './components/ExecutionTimeline';
import { FinalReport } from './components/FinalReport';
import { useMaximusHub } from './hooks/useMaximusHub';
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
  } = useMaximusHub();

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
          {/* Ask Maximus - Investigation Analysis */}
          {investigation && (
            <div style={{ marginBottom: '1rem' }}>
              <AskMaximusButton
                context={{
                  type: 'ai_investigation',
                  data: investigation,
                  results,
                  services,
                  stepsCompleted: analysisSteps.filter(s => s.status === 'completed').length,
                  totalSteps: analysisSteps.length,
                  investigationType
                }}
                prompt="Analyze this AI investigation. What are the key findings, security risks, and recommended next steps?"
                size="medium"
                variant="secondary"
              />
            </div>
          )}

          <InvestigationInfo investigation={investigation} />

          <ExecutionTimeline analysisSteps={analysisSteps} />

          <FinalReport investigation={investigation} results={results} />
        </div>
      </div>
    </div>
  );
};

export default MaximusCyberHub;
