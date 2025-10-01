import React from 'react';
import { Badge } from '../../../shared';
import { getStatusVariant } from '../utils/statusUtils';
import styles from './BasicInfoPanel.module.css';

export const BasicInfoPanel = ({ data }) => {
  return (
    <div className={styles.container}>
      <h3 className={styles.title}>INFORMAÇÕES BÁSICAS</h3>

      <div className={styles.fields}>
        <div className={styles.field}>
          <span className={styles.label}>DOMÍNIO</span>
          <span className={styles.value}>{data.domain}</span>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>STATUS</span>
          <Badge variant={getStatusVariant(data.status)} size="md">
            {data.status.toUpperCase()}
          </Badge>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>REGISTRAR</span>
          <span className={styles.value}>{data.registrar}</span>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>CRIAÇÃO</span>
          <span className={styles.value}>{data.creation_date}</span>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>EXPIRAÇÃO</span>
          <span className={styles.value}>{data.expiration_date}</span>
        </div>
      </div>
    </div>
  );
};

export default BasicInfoPanel;
