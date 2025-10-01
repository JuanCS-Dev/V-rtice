/**
 * Dark Web Module - REFATORADO
 *
 * Monitoramento de atividades na dark web e mercados ocultos.
 * Este componente orquestra a UI, delegando a lógica de acesso para o hook
 * useDarkWebAccess e a mensagem de acesso restrito para o subcomponente RestrictedAccessMessage.
 *
 * @version 2.0.0
 * @author Gemini
 */

import React from 'react';
import { Card } from '@/components/shared';
import { RestrictedAccessMessage } from './components/RestrictedAccessMessage';
import { useDarkWebAccess } from './hooks/useDarkWebAccess';
import styles from './DarkWebModule.module.css';

export const DarkWebModule = () => {
  const { isRequestingAccess, requestAccess } = useDarkWebAccess();

  return (
    <Card
      title="DARK WEB MONITOR"
      badge="OSINT"
      variant="osint"
    >
      <div className={styles.widgetContainer}>
        <p className={styles.description}>
          Monitoramento de atividades na dark web e mercados ocultos
        </p>

        <RestrictedAccessMessage
          onRequestAccess={requestAccess}
          isRequestingAccess={isRequestingAccess}
        />

        <div className={styles.resourcesSection}>
          <h4 className={styles.resourcesTitle}>RECURSOS DISPONÍVEIS (COM AUTORIZAÇÃO)</h4>
          <ul className={styles.resourcesList}>
            <li>Monitoramento de mercados de dados vazados</li>
            <li>Análise de fóruns de hackers</li>
            <li>Detecção de credenciais comprometidas</li>
            <li>Rastreamento de atividades criminosas</li>
            <li>Alertas de ameaças emergentes</li>
          </ul>
        </div>
      </div>
    </Card>
  );
};

export default DarkWebModule;
