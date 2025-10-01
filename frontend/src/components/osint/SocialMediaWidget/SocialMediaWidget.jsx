/**
 * Social Media Investigation Widget - REFATORADO
 *
 * OSINT em 20+ plataformas sociais. Este componente orquestra a UI,
 * delegando a lógica para o hook useSocialMediaInvestigation e a entrada
 * de dados para o componente InvestigationForm.
 *
 * @version 2.0.0
 * @author Gemini
 */

import React, { useCallback } from 'react';
import { Card, Badge, LoadingSpinner, Alert } from '../../../shared';
import { InvestigationForm } from './components/InvestigationForm';
import { useSocialMediaInvestigation } from './hooks/useSocialMediaInvestigation';
import { getConfidenceBadge, formatExecutionTime } from '../../../../api/worldClassTools';
import styles from './SocialMediaWidget.module.css';

export const SocialMediaWidget = () => {
  const { result, loading, error, investigate } = useSocialMediaInvestigation();

  const confidenceBadge = result ? getConfidenceBadge(result.confidence) : null;

  const renderPlatformData = useCallback((data) => {
    // Avoid rendering empty data objects
    if (!data || Object.keys(data).length === 0) return null;

    return (
        <div className={styles.platformData}>
            {Object.entries(data).map(([key, value]) => (
                <div key={key} className={styles.dataRow}>
                    <span className={styles.dataLabel}>{key}:</span>
                    <span className={styles.dataValue}>{String(value)}</span>
                </div>
            ))}
        </div>
    );
  }, []);

  return (
    <Card
      title="SOCIAL MEDIA DEEP DIVE"
      badge="OSINT"
      variant="osint"
      className={styles.widget}
    >
      <div className={styles.container}>
        <InvestigationForm
          onInvestigate={investigate}
          loading={loading}
          error={error}
        />

        {loading && (
          <LoadingSpinner
            variant="osint"
            size="lg"
            text="Investigando perfis sociais..."
          />
        )}

        {result && !loading && (
          <div className={styles.results}>
            <div className={styles.statusBar}>
              <div className={styles.statusItem}>
                <span className={styles.label}>TARGET:</span>
                <span className={styles.value}>{result.target}</span>
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

            {result.platforms_found?.length > 0 && (
              <div className={styles.section}>
                <h5 className={styles.sectionTitle}>
                  <i className="fas fa-check-circle"></i>
                  Plataformas Encontradas ({result.platforms_found.length})
                </h5>
                <div className={styles.platformList}>
                  {result.platforms_found.map((platform, index) => (
                    <div key={index} className={styles.platformCard}>
                      <div className={styles.platformHeader}>
                        <Badge variant="osint" size="sm">{platform.platform}</Badge>
                        {platform.verified && (
                          <Badge variant="success" size="sm">
                            <i className="fas fa-check"></i> VERIFICADO
                          </Badge>
                        )}
                      </div>
                      {platform.url && (
                        <a
                          href={platform.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={styles.platformLink}
                        >
                          <i className="fas fa-external-link-alt"></i>
                          {platform.url}
                          <span className={styles.visuallyHidden}>(opens in a new tab)</span>
                        </a>
                      )}
                      {renderPlatformData(platform.data)}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.insights?.length > 0 && (
              <div className={styles.section}>
                <h5 className={styles.sectionTitle}>
                  <i className="fas fa-brain"></i>
                  Insights
                </h5>
                <div className={styles.insightsList}>
                  {result.insights.map((insight, index) => (
                    <Alert key={index} variant="info" icon={<i className="fas fa-lightbulb"></i>}>
                      {insight}
                    </Alert>
                  ))}
                </div>
              </div>
            )}

            {result.warnings?.length > 0 && (
              <div className={styles.section}>
                 <h5 className={styles.sectionTitle}>
                  <i className="fas fa-exclamation-triangle"></i>
                  Warnings
                </h5>
                {result.warnings.map((warning, index) => (
                  <Alert key={index} variant="warning">
                    {warning}
                  </Alert>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

export default SocialMediaWidget;
