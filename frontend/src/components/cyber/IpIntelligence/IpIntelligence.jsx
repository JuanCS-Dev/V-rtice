/**
 * IP Intelligence & Geolocation Widget - REFATORADO
 *
 * Fornece análise detalhada de endereços IP, incluindo geolocalização,
 * infraestrutura e reputação de ameaças.
 *
 * @version 2.0.0
 * @author Gemini
 */

import React from 'react';
import { Card } from '../../../shared';
import { IpSearchForm } from './components/IpSearchForm';
import { IpAnalysisResults } from './components/IpAnalysisResults';
import { useIpIntelligence } from './hooks/useIpIntelligence';
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
    >
      <div className={styles.widgetBody}>
        <IpSearchForm
          ipAddress={ipAddress}
          setIpAddress={setIpAddress}
          loading={loading}
          loadingMyIp={loadingMyIp}
          searchHistory={searchHistory}
          handleAnalyzeIP={handleAnalyzeIP}
          handleAnalyzeMyIP={handleAnalyzeMyIP}
        />

        {analysisResult && (
          <IpAnalysisResults
            analysisResult={analysisResult}
            getThreatColor={getThreatColor}
          />
        )}

        {!analysisResult && !loading && !loadingMyIp && (
          <div className={styles.initialState}>
            <div className={styles.initialStateIcon}>🎯</div>
            <h3 className={styles.initialStateTitle}>IP INTELLIGENCE READY</h3>
            <p className={styles.initialStateDescription}>Digite um endereço IP para análise completa de geolocalização e ameaças</p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default IpIntelligence;