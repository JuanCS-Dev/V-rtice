import React from 'react';
import { Alert } from '../../shared';
import { useSocialEngineering } from './hooks/useSocialEngineering';
import { AccessDenied } from './components/AccessDenied';
import { CampaignForm } from './components/CampaignForm';
import { AwarenessForm } from './components/AwarenessForm';
import styles from './SocialEngineering.module.css';

/**
 * SocialEngineering - Ferramentas de engenharia social
 * Gestão de campanhas de phishing e treinamentos de awareness
 * Requer permissão 'offensive'
 */
export const SocialEngineering = () => {
  const {
    socialEngData,
    loading,
    hasOffensivePermission,
    createCampaign,
    createAwarenessCampaign
  } = useSocialEngineering();

  if (!hasOffensivePermission) {
    return <AccessDenied />;
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>🎭 Social Engineering</h2>
          <p className={styles.description}>
            Ferramentas para testes de engenharia social e awareness training
          </p>
        </div>
        <Alert variant="warning" size="sm">
          ⚠️ Uso autorizado apenas para testes internos e treinamentos
        </Alert>
      </div>

      {/* Forms Grid */}
      <div className={styles.forms}>
        <CampaignForm
          templates={socialEngData.templates}
          onSubmit={createCampaign}
          loading={loading.campaign}
        />
        <AwarenessForm
          onSubmit={createAwarenessCampaign}
          loading={loading.awareness}
        />
      </div>
    </div>
  );
};

export default SocialEngineering;
