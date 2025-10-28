/**
 * SYSTEM SECURITY - Comprehensive System Security Analysis
 *
 * Análise completa de segurança do sistema
 * Monitora portas, integridade de arquivos, processos e configurações
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="system-security"
 * - <header> for SecurityHeader component
 * - <section> for AI assistance
 * - <section> for analysis panels (port, file, process, config, logs)
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="system-security"
 * - Monitor analysis via data-maximus-status
 * - Access header via data-maximus-section="header"
 * - Interpret security analysis via semantic structure
 *
 * @version 2.0.0 (Maximus Vision)
 * @author Gemini + Maximus Vision Protocol
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from 'react';
import AskMaximusButton from '../../shared/AskMaximusButton';
import { useSystemSecurity } from './hooks/useSystemSecurity';
import { SecurityHeader } from './components/SecurityHeader';
import { AnalysisPanel } from './components/AnalysisPanel';
import styles from './SystemSecurity.module.css';

export const SystemSecurity = () => {
  const { securityData, loading, lastUpdate, refresh } = useSystemSecurity();

  const isAnalyzing = Object.values(loading).some(l => l);

  return (
    <article
      className={styles.container}
      role="article"
      aria-labelledby="system-security-title"
      data-maximus-tool="system-security"
      data-maximus-category="shared"
      data-maximus-status={isAnalyzing ? 'analyzing' : 'ready'}>

      <header
        role="region"
        aria-label="System security header"
        data-maximus-section="header">
        <h2 id="system-security-title" className={styles.visuallyHidden}>System Security</h2>
        <SecurityHeader lastUpdate={lastUpdate} onRefresh={refresh} />
      </header>

      <section
        style={{ margin: '1rem 0' }}
        role="region"
        aria-label="AI assistance"
        data-maximus-section="ai-assistance">
        <AskMaximusButton
          context={{
            type: 'system_security',
            data: securityData,
            lastUpdate
          }}
          prompt="Analyze this system security status and identify vulnerabilities, misconfigurations, or security risks"
          size="medium"
          variant="secondary"
        />
      </section>

      <section
        className={styles.panels}
        role="region"
        aria-label="Security analysis panels"
        data-maximus-section="analysis-panels">
        <AnalysisPanel
          title="ANÁLISE DE PORTAS"
          icon="🔍"
          data={securityData.portAnalysis}
          loading={loading.portAnalysis}
          emptyMessage="Nenhuma porta suspeita detectada"
        />

        <AnalysisPanel
          title="INTEGRIDADE DE ARQUIVOS"
          icon="📁"
          data={securityData.fileIntegrity}
          loading={loading.fileIntegrity}
          emptyMessage="Todos os arquivos íntegros"
        />

        <AnalysisPanel
          title="ANÁLISE DE PROCESSOS"
          icon="⚙️"
          data={securityData.processAnalysis}
          loading={loading.processAnalysis}
          emptyMessage="Nenhum processo suspeito"
        />

        <AnalysisPanel
          title="CONFIGURAÇÃO DE SEGURANÇA"
          icon="🔐"
          data={securityData.securityConfig}
          loading={loading.securityConfig}
          emptyMessage="Configurações não disponíveis"
        />

        <AnalysisPanel
          title="LOGS DE SEGURANÇA"
          icon="📋"
          data={securityData.securityLogs}
          loading={loading.securityLogs}
          emptyMessage="Nenhum log recente"
        />
      </section>
    </article>
  );
};

export default SystemSecurity;
