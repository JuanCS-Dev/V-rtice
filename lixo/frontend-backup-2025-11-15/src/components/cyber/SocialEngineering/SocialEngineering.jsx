/**
 * SOCIAL ENGINEERING - Phishing Campaigns & Awareness Training Tool
 *
 * Ferramentas para testes de engenharia social e awareness training
 * Gestão de campanhas de phishing e treinamentos de conscientização
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="social-engineering"
 * - <header> for tool header with warning
 * - <section> for campaign and awareness forms
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="social-engineering"
 * - Monitor campaign status via data-maximus-status
 * - Access forms via data-maximus-section="forms"
 * - Interpret campaign results via semantic structure
 *
 * Security: RBAC enforced, access denied without offensive permission
 * Philosophy: Dual-use - offensive testing + defensive training
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React from 'react';
import { Alert } from '../../shared';
import { useSocialEngineering } from './hooks/useSocialEngineering';
import { AccessDenied } from './components/AccessDenied';
import { CampaignForm } from './components/CampaignForm';
import { AwarenessForm } from './components/AwarenessForm';
import styles from './SocialEngineering.module.css';

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
    <article
      className={styles.container}
      role="article"
      aria-labelledby="social-engineering-title"
      data-maximus-tool="social-engineering"
      data-maximus-category="offensive"
      data-maximus-status={loading.campaign || loading.awareness ? 'creating' : 'ready'}>

      {/* Header */}
      <header
        className={styles.header}
        data-maximus-section="tool-header">
        <div>
          <h2 id="social-engineering-title" className={styles.title}><span aria-hidden="true">🎭</span> Social Engineering</h2>
          <p className={styles.description}>
            Ferramentas para testes de engenharia social e awareness training
          </p>
        </div>
        <Alert variant="warning" size="sm">
          ⚠️ Uso autorizado apenas para testes internos e treinamentos
        </Alert>
      </header>

      {/* Forms Grid */}
      <section
        className={styles.forms}
        role="region"
        aria-label="Campaign and awareness forms"
        data-maximus-section="forms">
        <CampaignForm
          templates={socialEngData.templates}
          onSubmit={createCampaign}
          loading={loading.campaign}
        />
        <AwarenessForm
          onSubmit={createAwarenessCampaign}
          loading={loading.awareness}
        />
      </section>
    </article>
  );
};

export default SocialEngineering;
