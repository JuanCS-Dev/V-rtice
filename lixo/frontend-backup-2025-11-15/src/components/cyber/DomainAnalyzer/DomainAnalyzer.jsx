/**
 * DOMAIN ANALYZER - Comprehensive Domain Analysis Tool
 *
 * Análise completa de domínios
 * Inclui informações básicas, infraestrutura e análise de ameaças
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="domain-analyzer"
 * - <header> for search interface
 * - <section> for AI assistance
 * - <section> for analysis results (basic info, infrastructure, threat analysis)
 * - <section> for empty state (conditional)
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="domain-analyzer"
 * - Monitor analysis via data-maximus-status
 * - Access search via data-maximus-section="search"
 * - Interpret domain intelligence via semantic structure
 *
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React from 'react';
import { useDomainAnalysis } from './hooks/useDomainAnalysis';
import { SearchHeader } from './components/SearchHeader';
import { BasicInfoPanel } from './components/BasicInfoPanel';
import { InfrastructurePanel } from './components/InfrastructurePanel';
import { ThreatAnalysisPanel } from './components/ThreatAnalysisPanel';
import { EmptyState } from './components/EmptyState';
import { AskMaximusButton } from '../../shared/AskMaximusButton';
import styles from './DomainAnalyzer.module.css';

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
    <article
      className={styles.container}
      role="article"
      aria-labelledby="domain-analyzer-title"
      data-maximus-tool="domain-analyzer"
      data-maximus-category="shared"
      data-maximus-status={loading ? 'analyzing' : 'ready'}>

      <header
        role="region"
        aria-label="Domain search"
        data-maximus-section="search">
        <h2 id="domain-analyzer-title" className={styles.visuallyHidden}>Domain Analyzer</h2>
        <SearchHeader
          domain={domain}
          setDomain={setDomain}
          loading={loading}
          onAnalyze={analyzeDomain}
          searchHistory={searchHistory}
          onSelectHistory={selectFromHistory}
        />
      </header>

      {analysisResult && (
        <>
          <section
            className={styles.aiButtonContainer}
            role="region"
            aria-label="AI assistance"
            data-maximus-section="ai-assistance">
            <AskMaximusButton
              context={{
                type: 'domain_analysis',
                domain: domain,
                analysis: analysisResult
              }}
              prompt="Analyze this domain for security threats and provide recommendations"
              size="medium"
              variant="secondary"
            />
          </section>

          <section
            className={styles.results}
            role="region"
            aria-label="Domain analysis results"
            data-maximus-section="results">
            <BasicInfoPanel data={analysisResult} />
            <InfrastructurePanel data={analysisResult} />
            <ThreatAnalysisPanel data={analysisResult} />
          </section>
        </>
      )}

      {!analysisResult && !loading && (
        <section
          role="region"
          aria-label="Empty state"
          data-maximus-section="empty-state">
          <EmptyState />
        </section>
      )}
    </article>
  );
};

export default DomainAnalyzer;
