/**
 * IP INTELLIGENCE SEARCH HEADER - Semantic Form with Multiple Actions
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <form> with role="search"
 * - <label> associated with input
 * - role="group" for action buttons
 * - <fieldset> for history group
 * - aria-live for loading status
 *
 * WCAG 2.1 AAA Compliance:
 * - All form controls labeled
 * - Button actions clearly described
 * - Loading status announced
 * - Keyboard accessible (Enter key)
 *
 * @version 2.0.0 (Maximus Vision)
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from 'react';
import { Input, Button } from '../../../shared';
import { useKeyPress } from '../../../../hooks';
import styles from './SearchHeader.module.css';

export const SearchHeader = ({
  ipAddress,
  setIpAddress,
  loading,
  loadingMyIp,
  onAnalyze,
  onAnalyzeMyIP,
  searchHistory,
  onSelectHistory
}) => {
  useKeyPress('Enter', () => {
    if (ipAddress.trim() && !loading && !loadingMyIp) {
      onAnalyze();
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (ipAddress.trim() && !loading && !loadingMyIp) {
      onAnalyze();
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>IP INTELLIGENCE & GEOLOCATION</h2>

      <form
        className={styles.searchBar}
        onSubmit={handleSubmit}
        role="search"
        aria-label="IP intelligence search">

        <label htmlFor="ip-header-input" className={styles.visuallyHidden}>
          IP Address
        </label>
        <Input
          id="ip-header-input"
          variant="cyber"
          size="lg"
          value={ipAddress}
          onChange={(e) => setIpAddress(e.target.value)}
          placeholder=">>> INSERIR ENDEREÇO IP PARA ANÁLISE"
          disabled={loading}
          fullWidth
          className={styles.input}
          aria-describedby={loading || loadingMyIp ? "ip-header-status" : undefined}
        />

        <div className={styles.actions} role="group" aria-label="Analysis actions">
          <Button
            type="submit"
            variant="cyber"
            size="md"
            disabled={loading || loadingMyIp || !ipAddress.trim()}
            loading={loading}
            fullWidth
            aria-label="Analyze IP address">
            {loading ? 'ANALISANDO...' : 'EXECUTAR ANÁLISE'}
          </Button>

          <Button
            type="button"
            variant="warning"
            size="md"
            onClick={onAnalyzeMyIP}
            disabled={loading || loadingMyIp}
            loading={loadingMyIp}
            icon="fas fa-bullseye"
            aria-label="Detect and analyze my IP address">
            {loadingMyIp ? 'DETECTANDO...' : 'MEU IP'}
          </Button>
        </div>
      </form>

      {(loading || loadingMyIp) && (
        <div id="ip-header-status" className={styles.visuallyHidden} role="status" aria-live="polite">
          {loading ? 'Analyzing IP address...' : 'Detecting your IP address...'}
        </div>
      )}

      {searchHistory.length > 0 && (
        <fieldset className={styles.history}>
          <legend className={styles.historyLabel}>HISTÓRICO:</legend>
          <div className={styles.historyItems} role="group" aria-label="Recent IP searches">
            {searchHistory.slice(0, 5).map((historicIP, index) => (
              <button
                key={index}
                type="button"
                onClick={() => onSelectHistory(historicIP)}
                className={styles.historyItem}
                aria-label={`Load IP ${historicIP}`}>
                {historicIP}
              </button>
            ))}
          </div>
        </fieldset>
      )}
    </div>
  );
};

export default SearchHeader;
