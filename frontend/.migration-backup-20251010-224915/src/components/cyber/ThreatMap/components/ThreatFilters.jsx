import React from 'react';
import { Badge } from '../../../shared';
import styles from './ThreatFilters.module.css';

const SEVERITIES = [
  { value: 'critical', label: 'Critical', variant: 'critical' },
  { value: 'high', label: 'High', variant: 'high' },
  { value: 'medium', label: 'Medium', variant: 'medium' },
  { value: 'low', label: 'Low', variant: 'low' }
];

const THREAT_TYPES = [
  { value: 'malware', label: 'Malware', icon: '🦠' },
  { value: 'botnet', label: 'Botnet', icon: '🤖' },
  { value: 'phishing', label: 'Phishing', icon: '🎣' },
  { value: 'ddos', label: 'DDoS', icon: '💥' },
  { value: 'exploit', label: 'Exploit', icon: '⚡' }
];

export const ThreatFilters = ({ filters, onFiltersChange }) => {
  const toggleFilter = (filterType, value) => {
    const currentFilters = filters[filterType] || [];
    const newFilters = currentFilters.includes(value)
      ? currentFilters.filter(v => v !== value)
      : [...currentFilters, value];

    onFiltersChange({
      ...filters,
      [filterType]: newFilters
    });
  };

  return (
    <div className={styles.container}>
      {/* Severity Filters */}
      <div className={styles.filterGroup}>
        <label className={styles.filterLabel}>
          <i className="fas fa-exclamation-triangle"></i>
          Severidade:
        </label>
        <div className={styles.filterButtons}>
          {SEVERITIES.map(severity => (
            <button
              key={severity.value}
              type="button"
              className={`${styles.filterButton} ${
                filters.severity.includes(severity.value) ? styles.active : ''
              }`}
              onClick={() => toggleFilter('severity', severity.value)}
            >
              <Badge variant={severity.variant} size="sm">
                {severity.label}
              </Badge>
            </button>
          ))}
        </div>
      </div>

      {/* Type Filters */}
      <div className={styles.filterGroup}>
        <label className={styles.filterLabel}>
          <i className="fas fa-shield-virus"></i>
          Tipo de Ameaça:
        </label>
        <div className={styles.filterButtons}>
          {THREAT_TYPES.map(type => (
            <button
              key={type.value}
              type="button"
              className={`${styles.filterButton} ${
                filters.type.includes(type.value) ? styles.active : ''
              }`}
              onClick={() => toggleFilter('type', type.value)}
            >
              <span className={styles.typeIcon}>{type.icon}</span>
              <span>{type.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ThreatFilters;
