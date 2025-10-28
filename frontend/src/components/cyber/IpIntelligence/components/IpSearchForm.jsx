/**
 * IP SEARCH FORM - Semantic Form for IP Intelligence Analysis
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <form> with proper semantic structure
 * - <label> associated with input via htmlFor/id
 * - <fieldset> for history group
 * - aria-describedby for loading status
 *
 * WCAG 2.1 AAA Compliance:
 * - All form controls labeled
 * - Keyboard accessible
 * - Screen reader friendly
 * - Focus indicators
 *
 * @version 2.0.0 (Maximus Vision)
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from 'react';
import { Button, Input } from '../../../shared';
import styles from './IpSearchForm.module.css';

const IpSearchForm = ({
  ipAddress,
  setIpAddress,
  loading,
  loadingMyIp,
  searchHistory,
  handleAnalyzeIP,
  handleAnalyzeMyIP,
}) => {

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!loading && !loadingMyIp && ipAddress.trim()) {
      handleAnalyzeIP(ipAddress);
    }
  };

  return (
    <form
      className={styles.searchContainer}
      onSubmit={handleSubmit}
      role="search"
      aria-label="IP intelligence search">

      <div className={styles.inputGroup}>
        <label htmlFor="ip-address-input" className={styles.visuallyHidden}>
          IP Address
        </label>
        <Input
          id="ip-address-input"
          type="text"
          value={ipAddress}
          onChange={(e) => setIpAddress(e.target.value)}
          placeholder=">>> INSERIR ENDEREÇO IP PARA ANÁLISE"
          variant="cyber"
          size="lg"
          disabled={loading || loadingMyIp}
          icon={loading && <div className={styles.loadingSpinner}></div>}
          aria-describedby={loading ? "ip-search-status" : undefined}
        />

        <div className={styles.buttonGroup} role="group" aria-label="Search actions">
          <Button
            type="submit"
            disabled={loading || loadingMyIp || !ipAddress.trim()}
            variant="cyber"
            size="lg"
            className={styles.analyzeButton}
            aria-label="Analyze IP address">
            {loading ? 'ANALISANDO...' : 'EXECUTAR ANÁLISE'}
          </Button>

          <Button
            type="button"
            onClick={handleAnalyzeMyIP}
            disabled={loading || loadingMyIp}
            variant="warning"
            size="lg"
            className={styles.myIpButton}
            icon={loadingMyIp ? <i className="fas fa-spinner fa-spin"></i> : <i className="fas fa-crosshairs"></i>}
            aria-label="Analyze my IP address">
            MEU IP
          </Button>
        </div>
      </div>

      {loading && (
        <div id="ip-search-status" className={styles.visuallyHidden} role="status" aria-live="polite">
          Analyzing IP address...
        </div>
      )}

      {searchHistory.length > 0 && (
        <fieldset className={styles.historyContainer}>
          <legend className={styles.historyLabel}>HISTÓRICO:</legend>
          <div role="group" aria-label="Recent searches">
            {searchHistory.slice(0, 5).map((historicIP, index) => (
              <button
                key={index}
                type="button"
                onClick={() => setIpAddress(historicIP)}
                className={styles.historyButton}
                aria-label={`Load IP ${historicIP}`}>
                {historicIP}
              </button>
            ))}
          </div>
        </fieldset>
      )}
    </form>
  );
};

export default React.memo(IpSearchForm);
