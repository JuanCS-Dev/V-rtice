/**
 * IP INTELLIGENCE & GEOLOCATION - Advanced IP Analysis Tool
 *
 * Fornece análise detalhada de endereços IP
 * Inclui geolocalização, infraestrutura e reputação de ameaças
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - Card wrapper with data-maximus-tool="ip-intelligence"
 * - <section> for search form
 * - <section> for analysis results
 * - <section> for empty state (conditional)
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="ip-intelligence"
 * - Monitor analysis via data-maximus-status
 * - Access search via data-maximus-section="search"
 * - Interpret IP intelligence via semantic structure
 *
 * @version 2.0.0 (Maximus Vision)
 * @author Gemini + Maximus Vision Protocol
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from 'react';
import { Card } from '../../shared/Card';
import IpSearchForm from './components/IpSearchForm';
import IpAnalysisResults from './components/IpAnalysisResults';
import { useIpIntelligence } from './hooks/useIpIntelligence';
import { AskMaximusButton } from '../../shared/AskMaximusButton';
import styles from './IpIntelligence.module.css';

export const IpIntelligence = () => {
  const {
    ipAddress, setIpAddress,
    loading,
    analysisResult,
    searchHistory,
    loadingMyIp,
    handleAnalyzeIP,
    handleAnalyzeMyIP,
    getThreatColor
  } = useIpIntelligence();

  return (
    <Card
      title="IP INTELLIGENCE & GEOLOCATION"
      badge="CYBER"
      variant="cyber"
      data-maximus-tool="ip-intelligence"
      data-maximus-category="shared"
      data-maximus-status={loading || loadingMyIp ? 'analyzing' : 'ready'}
      headerAction={
        analysisResult && (
          <AskMaximusButton
            context={{
              type: 'ip_intelligence',
              ip: ipAddress,
              analysis: analysisResult
            }}
            prompt="Analyze this IP intelligence data and assess threat level"
            size="small"
            variant="secondary"
            buttonText="🤖 Ask AI"
          />
        )
      }
    >
      <div className={styles.widgetBody}>
        <section
          role="region"
          aria-label="IP search form"
          data-maximus-section="search">
          <IpSearchForm
            ipAddress={ipAddress}
            setIpAddress={setIpAddress}
            loading={loading}
            loadingMyIp={loadingMyIp}
            searchHistory={searchHistory}
            handleAnalyzeIP={handleAnalyzeIP}
            handleAnalyzeMyIP={handleAnalyzeMyIP}
          />
        </section>

        {analysisResult && (
          <section
            role="region"
            aria-label="IP analysis results"
            data-maximus-section="results">
            <IpAnalysisResults
              analysisResult={analysisResult}
              getThreatColor={getThreatColor}
            />
          </section>
        )}

        {!analysisResult && !loading && !loadingMyIp && (
          <section
            className={styles.initialState}
            role="region"
            aria-label="Empty state"
            data-maximus-section="empty-state">
            <div className={styles.initialStateIcon}>🎯</div>
            <h3 className={styles.initialStateTitle}>IP INTELLIGENCE READY</h3>
            <p className={styles.initialStateDescription}>Digite um endereço IP para análise completa de geolocalização e ameaças</p>
          </section>
        )}
      </div>
    </Card>
  );
};

export default IpIntelligence;