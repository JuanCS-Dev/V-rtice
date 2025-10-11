/**
 * Breach Data Search Widget - REFATORADO
 *
 * Busca em 12B+ registros de vazamentos de dados de múltiplas fontes.
 * Este componente orquestra a UI, delegando a lógica para o hook
 * useBreachDataSearch e a entrada de dados para o BreachSearchForm.
 *
 * @version 2.0.0
 * @author Gemini
 */

import React, { useCallback } from 'react';
import { Card, Badge, LoadingSpinner, Alert } from '../../shared';
import { BreachSearchForm } from './components/BreachSearchForm';
import { useBreachDataSearch } from './hooks/useBreachDataSearch';
import { getConfidenceBadge, formatExecutionTime, getSeverityColor } from '../../../api/worldClassTools';
import styles from './BreachDataWidget.module.css';

export const BreachDataWidget = () => {
  const { result, loading, error, search } = useBreachDataSearch();

  const confidenceBadge = result ? getConfidenceBadge(result.confidence) : null;

  const formatDataTypes = useCallback((types) => {
    if (!types || types.length === 0) return null;
    return types.map((type, idx) => (
        <span key={idx} className={styles.dataPill}>
            {type}
        </span>
    ));
  }, []);

  return (
    <Card
      title="BREACH DATA SEARCH"
      badge={<span style={{color: 'var(--color-critical)'}}>12B+ RECORDS</span>}
      variant="critical"
    >
      <div className={styles.container}>
        <BreachSearchForm onSearch={search} loading={loading} error={error} />

        {loading && (
          <LoadingSpinner
            variant="critical"
            size="lg"
            text="Buscando em registros de vazamentos..."
          />
        )}

        {result && !loading && (
          <div className={styles.results}>
            <div className={styles.statusBar}>
                <div className={styles.statusItem}>
                    <span className={styles.label}>STATUS:</span>
                    <span className={styles.value} style={{ color: result.status === 'success' ? 'var(--color-success)' : 'var(--color-error)' }}>
                    {result.status === 'success' ? '✓ SUCCESS' : '✗ FAILED'}
                    </span>
                </div>
                {confidenceBadge && (
                    <div className={styles.statusItem}>
                        <span className={styles.label}>CONFIDENCE:</span>
                        <span className={styles.value} style={{ color: confidenceBadge.color }}>
                        {confidenceBadge.icon} {result.confidence.toFixed(1)}%
                        </span>
                    </div>
                )}
                <div className={styles.statusItem}>
                    <span className={styles.label}>TEMPO:</span>
                    <span className={styles.value}>{formatExecutionTime(result.execution_time_ms)}</span>
                </div>
            </div>

            <div className={styles.queryInfoCard}>
                <div className={styles.infoHeader}>
                    <h4>
                        <i className={`fas ${result.queryType === 'email' ? 'fa-envelope' : 'fa-user'}`}></i>
                        {result.query}
                    </h4>
                    {result.credentials_exposed && (
                        <div className={styles.exposedBadge}>
                            <i className="fas fa-exclamation-circle"></i>
                            CREDENCIAIS EXPOSTAS
                        </div>
                    )}
                </div>
                <div className={styles.exposureSummary}>
                    <div className={styles.summaryStat}>
                        <div className={styles.statIcon} style={{ color: 'var(--color-critical)' }}><i className="fas fa-database"></i></div>
                        <div className={styles.statContent}>
                            <span className={styles.statValue}>{result.breaches_found || 0}</span>
                            <span className={styles.statLabel}>Breaches</span>
                        </div>
                    </div>
                    <div className={styles.summaryStat}>
                        <div className={styles.statIcon} style={{ color: 'var(--color-high)' }}><i className="fas fa-key"></i></div>
                        <div className={styles.statContent}>
                            <span className={styles.statValue}>{result.total_exposures || 0}</span>
                            <span className={styles.statLabel}>Exposições</span>
                        </div>
                    </div>
                    <div className={styles.summaryStat}>
                        <div className={styles.statIcon} style={{ color: result.credentials_exposed ? 'var(--color-critical)' : 'var(--color-success)' }}><i className={`fas ${result.credentials_exposed ? 'fa-unlock' : 'fa-lock'}`}></i></div>
                        <div className={styles.statContent}>
                            <span className={styles.statValue} style={{ color: result.credentials_exposed ? 'var(--color-critical)' : 'var(--color-success)' }}>{result.credentials_exposed ? 'SIM' : 'NÃO'}</span>
                            <span className={styles.statLabel}>Credenciais Vazadas</span>
                        </div>
                    </div>
                </div>
            </div>

            {result.breaches?.length > 0 ? (
              <div className={styles.breachesList}>
                <h5><i className="fas fa-exclamation-triangle"></i> Vazamentos Detectados ({result.breaches.length})</h5>
                {result.breaches.map((breach, index) => (
                  <div key={index} className={styles.breachCard}>
                    <div className={styles.breachHeader} style={{ borderLeftColor: getSeverityColor(breach.severity) }}>
                        <div className={styles.breachSource}>
                            <i className="fas fa-database"></i>
                            <span>{breach.source}</span>
                        </div>
                        <div className={styles.breachMeta}>
                            <span className={styles.breachDate}><i className="far fa-calendar"></i> {new Date(breach.date).toLocaleDateString('pt-BR')}</span>
                            <Badge variant={breach.severity?.toLowerCase()} size="sm">{breach.severity || 'MEDIUM'}</Badge>
                        </div>
                    </div>
                    <div className={styles.breachBody}>
                        <div className={styles.breachStats}>
                            <div className={styles.statItem}><i className="fas fa-users"></i> <span>{breach.records_leaked?.toLocaleString() || 'N/A'} registros</span></div>
                        </div>
                        <div className={styles.dataTypesPills}>{formatDataTypes(breach.data_types)}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className={styles.noBreaches}>
                <i className="fas fa-shield-alt"></i>
                <p>Nenhum vazamento encontrado. Dados aparentemente seguros.</p>
              </div>
            )}

            {result.recommendations?.length > 0 && (
                <div className={styles.recommendations}>
                    <h5><i className="fas fa-shield-alt"></i> Recomendações de Segurança</h5>
                    {result.recommendations.map((rec, index) => (
                        <Alert key={index} variant="warning">{rec}</Alert>
                    ))}
                </div>
            )}

          </div>
        )}
      </div>
    </Card>
  );
};

export default BreachDataWidget;