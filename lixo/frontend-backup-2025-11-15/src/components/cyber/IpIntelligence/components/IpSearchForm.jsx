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
 * SECURITY (Boris Cherny Standard):
 * - GAP #10 FIXED: IP address validation
 * - GAP #9 FIXED: Input sanitization
 * - GAP #15 FIXED: maxLength on inputs
 * - GAP #16 FIXED: Whitespace-only prevention
 *
 * @version 3.0.0 (Security Hardened)
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React, { useState } from 'react';
import { Button, Input } from '../../../shared';
import { validateIP } from '../../../../utils/validation';
import { sanitizeIP } from '../../../../utils/sanitization';
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
  const [error, setError] = useState(null);

  // Secure IP input handler - GAP #10 FIX
  const handleIPChange = (e) => {
    const sanitized = sanitizeIP(e.target.value);
    setIpAddress(sanitized);
    // Clear error on change
    if (error) setError(null);
  };

  // Validate IP on blur
  const handleIPBlur = () => {
    if (!ipAddress.trim()) {
      setError(null);
      return; // Empty is OK
    }

    const result = validateIP(ipAddress);
    if (!result.valid) {
      setError(result.error);
    } else {
      setError(null);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validate before submission
    if (!ipAddress.trim()) {
      setError('IP address is required');
      return;
    }

    const result = validateIP(ipAddress);
    if (!result.valid) {
      setError(result.error);
      return;
    }

    if (!loading && !loadingMyIp) {
      handleAnalyzeIP(result.sanitized);
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
        <div>
          <Input
            id="ip-address-input"
            type="text"
            value={ipAddress}
            onChange={handleIPChange}
            onBlur={handleIPBlur}
            placeholder=">>> INSERIR ENDEREÇO IP PARA ANÁLISE"
            variant="cyber"
            size="lg"
            maxLength={45}
            disabled={loading || loadingMyIp}
            icon={loading && <div className={styles.loadingSpinner}></div>}
            aria-invalid={!!error}
            aria-describedby={error ? "ip-input-error" : (loading ? "ip-search-status" : undefined)}
          />
          {error && (
            <div
              id="ip-input-error"
              className={styles.error}
              role="alert"
              aria-live="polite"
            >
              ⚠️ {error}
            </div>
          )}
        </div>

        <div className={styles.buttonGroup} role="group" aria-label="Search actions">
          <Button
            type="submit"
            disabled={loading || loadingMyIp || !ipAddress.trim() || !!error}
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
            icon={loadingMyIp ? <i className="fas fa-spinner fa-spin" aria-hidden="true"></i> : <i className="fas fa-crosshairs" aria-hidden="true"></i>}
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
