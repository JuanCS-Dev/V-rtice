import React from 'react';
import AskMaximusButton from '../../shared/AskMaximusButton';
import { useSystemSecurity } from './hooks/useSystemSecurity';
import { SecurityHeader } from './components/SecurityHeader';
import { AnalysisPanel } from './components/AnalysisPanel';
import styles from './SystemSecurity.module.css';

/**
 * SystemSecurity - Análise completa de segurança do sistema
 * Monitora portas, integridade de arquivos, processos e configurações
 */
export const SystemSecurity = () => {
  const { securityData, loading, lastUpdate, refresh } = useSystemSecurity();

  return (
    <div className={styles.container}>
      <SecurityHeader lastUpdate={lastUpdate} onRefresh={refresh} />

      <div style={{ margin: '1rem 0' }}>
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
      </div>

      <div className={styles.panels}>
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
      </div>
    </div>
  );
};

export default SystemSecurity;
