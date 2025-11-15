import React from 'react';
import { Badge, LoadingSpinner } from '../../../shared';
import { getSeverityVariant } from '../utils/securityUtils';
import styles from './AnalysisPanel.module.css';

/**
 * AnalysisPanel - Painel genérico para exibir dados de análise
 */
export const AnalysisPanel = ({
  title,
  icon,
  data,
  loading,
  emptyMessage = 'Nenhum dado disponível'
}) => {
  if (loading) {
    return (
      <div className={styles.container}>
        <h3 className={styles.title}>
          {icon} {title}
        </h3>
        <LoadingSpinner variant="cyber" size="md" />
      </div>
    );
  }

  if (!data || (Array.isArray(data) && data.length === 0)) {
    return (
      <div className={styles.container}>
        <h3 className={styles.title}>
          {icon} {title}
        </h3>
        <div className={styles.empty}>{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>
        {icon} {title}
      </h3>
      <div className={styles.content}>
        {Array.isArray(data) ? (
          data.map((item, index) => (
            <div key={index} className={styles.item}>
              {item.severity && (
                <Badge variant={getSeverityVariant(item.severity)} size="sm">
                  {item.severity}
                </Badge>
              )}
              <div className={styles.itemContent}>
                {item.name && <div className={styles.itemName}>{item.name}</div>}
                {item.description && <div className={styles.itemDesc}>{item.description}</div>}
                {item.details && <div className={styles.itemDetails}>{item.details}</div>}
              </div>
            </div>
          ))
        ) : (
          <div className={styles.dataGrid}>
            {Object.entries(data).map(([key, value]) => (
              <div key={key} className={styles.dataItem}>
                <span className={styles.dataKey}>{key}:</span>
                <span className={styles.dataValue}>{String(value)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisPanel;
