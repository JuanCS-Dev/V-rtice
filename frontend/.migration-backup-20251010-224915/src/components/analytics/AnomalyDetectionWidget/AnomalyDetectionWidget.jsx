/**
 * Anomaly Detection Widget - REFATORADO
 *
 * Orquestra a UI para detecção de anomalias, delegando a lógica para o hook
 * useAnomalyDetection e a UI para os subcomponentes AnomalyDetectionForm e AnomalyResults.
 *
 * @version 2.0.0
 * @author Gemini
 */

import React from 'react';
import { Card, LoadingSpinner, Alert } from '../../../shared';
import { AnomalyDetectionForm } from './components/AnomalyDetectionForm';
import { AnomalyResults } from './components/AnomalyResults';
import { useAnomalyDetection } from './hooks/useAnomalyDetection';
import { getConfidenceBadge, formatExecutionTime } from '../../../../api/worldClassTools';
import styles from './AnomalyDetectionWidget.module.css';

export const AnomalyDetectionWidget = () => {
    const {
        dataInput, setDataInput,
        method, setMethod,
        sensitivity, setSensitivity,
        loading,
        result,
        error,
        detect,
        generateSampleData
    } = useAnomalyDetection();

    const confidenceBadge = result ? getConfidenceBadge(result.confidence) : null;

    return (
        <Card
            title="ANOMALY DETECTION"
            badge="ML + STATS"
            variant="analytics"
        >
            <div className={styles.widgetBody}>
                <AnomalyDetectionForm
                    dataInput={dataInput}
                    setDataInput={setDataInput}
                    method={method}
                    setMethod={setMethod}
                    sensitivity={sensitivity}
                    setSensitivity={setSensitivity}
                    loading={loading}
                    onDetect={detect}
                    onGenerateSample={generateSampleData}
                />

                {error && (
                    <Alert variant="error" icon={<i className="fas fa-exclamation-triangle"></i>}>
                        {error}
                    </Alert>
                )}

                {loading && (
                    <LoadingSpinner
                        variant="analytics"
                        size="lg"
                        text="Analisando dados..."
                    />
                )}

                {result && !loading && (
                    <>
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
                        <AnomalyResults result={result} dataInput={dataInput} />
                    </>
                )}
            </div>
        </Card>
    );
};

export default AnomalyDetectionWidget;
