import React from 'react';
import styles from './AccessDenied.module.css';

export const AccessDenied = () => {
  return (
    <div className={styles.container}>
      <div className={styles.icon}>🔒</div>
      <h3 className={styles.title}>Acesso Negado</h3>
      <p className={styles.description}>
        Você não tem permissão para acessar ferramentas de Social Engineering.
        <br />
        Apenas usuários com permissão 'offensive' podem utilizar este módulo.
      </p>
    </div>
  );
};

export default AccessDenied;
