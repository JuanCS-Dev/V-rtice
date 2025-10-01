import React from 'react';
import { Button } from '@/components/shared';
import styles from './RestrictedAccessMessage.module.css';

/**
 * Displays a message for restricted access modules and a button to request access.
 */
const RestrictedAccessMessageComponent = React.memo(function RestrictedAccessMessage({ onRequestAccess, isRequestingAccess }) {
  return (
    <div className={styles.restrictedMessage}>
      <div className={styles.icon} role="img" aria-label="Warning">⚠️</div>
      <h3 className={styles.title}>MÓDULO RESTRITO</h3>
      <p className={styles.description}>
        Acesso ao Dark Web Monitor requer autorização especial
      </p>
      <p className={styles.hint}>
        Entre em contato com o administrador do sistema para solicitar acesso
      </p>

      <Button
        variant="danger"
        size="lg"
        onClick={onRequestAccess}
        loading={isRequestingAccess}
        disabled={isRequestingAccess}
        className={styles.requestButton}
        icon={<i className="fas fa-lock"></i>}
      >
        {isRequestingAccess ? 'SOLICITANDO...' : 'SOLICITAR ACESSO'}
      </Button>
    </div>
  );
});

export { RestrictedAccessMessageComponent as RestrictedAccessMessage };
export default RestrictedAccessMessageComponent;
