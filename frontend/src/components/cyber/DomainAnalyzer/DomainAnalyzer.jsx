import React from 'react';
import { useDomainAnalysis } from './hooks/useDomainAnalysis';
import { SearchHeader } from './components/SearchHeader';
import { BasicInfoPanel } from './components/BasicInfoPanel';
import { InfrastructurePanel } from './components/InfrastructurePanel';
import { ThreatAnalysisPanel } from './components/ThreatAnalysisPanel';
import { EmptyState } from './components/EmptyState';
import styles from './DomainAnalyzer.module.css';

/**
 * DomainAnalyzer - Análise completa de domínios
 * Inclui informações básicas, infraestrutura e análise de ameaças
 */
export const DomainAnalyzer = () => {
  const {
    domain,
    setDomain,
    loading,
    analysisResult,
    searchHistory,
    analyzeDomain,
    selectFromHistory
  } = useDomainAnalysis();

  return (
    <div className={styles.container}>
      <SearchHeader
        domain={domain}
        setDomain={setDomain}
        loading={loading}
        onAnalyze={analyzeDomain}
        searchHistory={searchHistory}
        onSelectHistory={selectFromHistory}
      />

      {analysisResult && (
        <div className={styles.results}>
          <BasicInfoPanel data={analysisResult} />
          <InfrastructurePanel data={analysisResult} />
          <ThreatAnalysisPanel data={analysisResult} />
        </div>
      )}

      {!analysisResult && !loading && <EmptyState />}
    </div>
  );
};

export default DomainAnalyzer;
