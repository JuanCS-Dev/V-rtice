import React from 'react';
import { Badge, Alert } from '../../../shared';
import styles from './AnomalyResults.module.css';

/**
 * Displays the results of an anomaly detection analysis.
 */
const AnomalyResults = ({ result, dataInput }) => {

    if (!result) return null;

    const dataPointCount = dataInput.split(',').filter(v => v.trim()).length;

    return (
        <div className={styles.resultsContainer}>
            {/* Summary Card */}
            <div className={styles.card}>
                <h5><i className="fas fa-chart-bar" aria-hidden="true"></i> Resumo da Análise</h5>
                <div className={styles.summaryGrid}>
                    <div className={styles.summaryStat}>
                        <span className={`${styles.statIcon} icon-critical`}><i className="fas fa-exclamation-circle" aria-hidden="true"></i></span>
                        <div className={styles.statContent}>
                            <span className={styles.statValue}>{result.anomalies_found || 0}</span>
                            <span className={styles.statLabel}>Anomalias Detectadas</span>
                        </div>
                    </div>
                    <div className={styles.summaryStat}>
                        <span className={`${styles.statIcon} icon-analytics`}><i className="fas fa-database" aria-hidden="true"></i></span>
                        <div className={styles.statContent}>
                            <span className={styles.statValue}>{dataPointCount}</span>
                            <span className={styles.statLabel}>Pontos Analisados</span>
                        </div>
                    </div>
                    <div className={styles.summaryStat}>
                        <span className={`${styles.statIcon} icon-warning`}><i className="fas fa-percentage" aria-hidden="true"></i></span>
                        <div className={styles.statContent}>
                            <span className={styles.statValue}>
                                {result.anomalies_found && dataPointCount > 0
                                    ? ((result.anomalies_found / dataPointCount) * 100).toFixed(1)
                                    : 0}%
                            </span>
                            <span className={styles.statLabel}>Taxa de Anomalia</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Baseline Statistics */}
            {result.baseline_stats && (
                <div className={styles.card}>
                    <h5><i className="fas fa-chart-area" aria-hidden="true"></i> Estatísticas de Baseline</h5>
                    <div className={styles.baselineGrid}>
                        <div className={styles.baselineStat}>
                            <span className={styles.label}>Média:</span>
                            <span className={styles.value}>{result.baseline_stats.mean?.toFixed(3) || 'N/A'}</span>
                        </div>
                        <div className={styles.baselineStat}>
                            <span className={styles.label}>Desvio Padrão:</span>
                            <span className={styles.value}>{result.baseline_stats.std?.toFixed(3) || 'N/A'}</span>
                        </div>
                        <div className={styles.baselineStat}>
                            <span className={styles.label}>Mediana:</span>
                            <span className={styles.value}>{result.baseline_stats.median?.toFixed(3) || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Anomalies List */}
            {result.anomalies && result.anomalies.length > 0 && (
                <div className={`${styles.card} ${styles.anomaliesList}`}>
                    <h5><i className="fas fa-exclamation-triangle" aria-hidden="true"></i> Anomalias Detectadas ({result.anomalies.length})</h5>
                    {result.anomalies.map((anomaly, index) => (
                        <div key={index} className={styles.anomalyCard}>
                            <div className={styles.anomalyHeader}>
                                <span className={styles.anomalyIndex}>Anomalia #{index + 1}</span>
                                <Badge variant={anomaly.severity?.toLowerCase()} size="sm">{anomaly.severity || 'MEDIUM'}</Badge>
                            </div>
                            <div className={styles.anomalyBody}>
                                <div className={styles.anomalyInfo}>
                                    <div className={styles.infoItem}>
                                        <span className={styles.label}>Índice:</span>
                                        <span className={styles.value}>{anomaly.index}</span>
                                    </div>
                                    <div className={styles.infoItem}>
                                        <span className={styles.label}>Valor:</span>
                                        <span className={`${styles.value} ${styles.highlight}`}>{anomaly.value?.toFixed(3)}</span>
                                    </div>
                                    <div className={styles.infoItem}>
                                        <span className={styles.label}>Score de Anomalia:</span>
                                        <span className={styles.value}>{(anomaly.anomaly_score * 100).toFixed(1)}%</span>
                                    </div>
                                </div>
                                <div className={styles.anomalyDescription}>
                                    {anomaly.description}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {result.anomalies_found === 0 && (
                <div className={styles.noAnomalies}>
                    <i className="fas fa-check-circle" aria-hidden="true"></i>
                    <p>Nenhuma anomalia detectada. Dados dentro do padrão esperado.</p>
                </div>
            )}

            {/* Recommendations */}
            {result.recommendations && result.recommendations.length > 0 && (
                <div className={`${styles.card} ${styles.recommendations}`}>
                    <h5><i className="fas fa-lightbulb" aria-hidden="true"></i> Recomendações</h5>
                    {result.recommendations.map((rec, index) => (
                        <Alert key={index} variant="info">{rec}</Alert>
                    ))}
                </div>
            )}
        </div>
    );
};

export default React.memo(AnomalyResults);
