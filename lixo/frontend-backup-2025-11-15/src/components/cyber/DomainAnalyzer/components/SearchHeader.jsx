/**
 * DOMAIN SEARCH HEADER - Semantic Form for Domain Analysis
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <form> with role="search"
 * - <label> associated with input
 * - <fieldset> for history group
 * - aria-live for loading status
 *
 * WCAG 2.1 AAA Compliance:
 * - All form controls labeled
 * - Keyboard accessible (Enter key support)
 * - Loading status announced
 * - History as shortcuts
 *
 * @version 2.0.0 (Maximus Vision)
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from 'react';
import { Input, Button } from '../../../shared';
import { useKeyPress } from '../../../../hooks';
import styles from './SearchHeader.module.css';

export const SearchHeader = ({
  domain,
  setDomain,
  loading,
  onAnalyze,
  searchHistory,
  onSelectHistory
}) => {
  useKeyPress('Enter', () => {
    if (domain.trim() && !loading) {
      onAnalyze();
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (domain.trim() && !loading) {
      onAnalyze();
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>DOMAIN INTELLIGENCE ANALYZER</h2>

      <form
        className={styles.searchBar}
        onSubmit={handleSubmit}
        role="search"
        aria-label="Domain intelligence search">

        <label htmlFor="domain-input" className={styles.visuallyHidden}>
          Domain Name
        </label>
        <Input
          id="domain-input"
          variant="cyber"
          size="lg"
          value={domain}
          onChange={(e) => setDomain(e.target.value.toLowerCase())}
          placeholder=">>> INSERIR DOMÍNIO PARA ANÁLISE"
          disabled={loading}
          fullWidth
          className={styles.input}
          aria-describedby={loading ? "domain-search-status" : undefined}
        />

        <Button
          type="submit"
          variant="cyber"
          size="md"
          disabled={loading || !domain.trim()}
          loading={loading}
          aria-label="Analyze domain">
          {loading ? 'ANALISANDO...' : 'EXECUTAR ANÁLISE'}
        </Button>
      </form>

      {loading && (
        <div id="domain-search-status" className={styles.visuallyHidden} role="status" aria-live="polite">
          Analyzing domain...
        </div>
      )}

      {searchHistory.length > 0 && (
        <fieldset className={styles.history}>
          <legend className={styles.historyLabel}>HISTÓRICO:</legend>
          <div className={styles.historyItems} role="group" aria-label="Recent domain searches">
            {searchHistory.slice(0, 5).map((historicDomain, index) => (
              <button
                key={index}
                type="button"
                onClick={() => onSelectHistory(historicDomain)}
                className={styles.historyItem}
                aria-label={`Load domain ${historicDomain}`}>
                {historicDomain}
              </button>
            ))}
          </div>
        </fieldset>
      )}
    </div>
  );
};

export default SearchHeader;
