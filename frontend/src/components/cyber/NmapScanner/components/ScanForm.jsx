/**
 * NMAP SCAN FORM - Semantic Form for Network Scanning
 *
 * AI-FIRST DESIGN:
 * - <form> with proper structure
 * - All inputs labeled
 * - <fieldset> for history group
 * - aria-live for loading status
 *
 * @version 2.0.0 (Maximus Vision)
 */

import React from 'react';
import { Input, Button } from '../../../shared';
import { useKeyPress } from '../../../../hooks';
import styles from './ScanForm.module.css';

export const ScanForm = ({
  target,
  setTarget,
  selectedProfile,
  setSelectedProfile,
  customArgs,
  setCustomArgs,
  profiles,
  onScan,
  loading,
  scanHistory,
}) => {
  useKeyPress('Enter', () => {
    if (target.trim() && !loading) {
      onScan();
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (target.trim() && !loading) {
      onScan();
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>NMAP NETWORK SCANNER</h2>

      <form className={styles.form} onSubmit={handleSubmit} aria-label="Nmap scan configuration">
        <Input
          label="Target (IP/CIDR/Hostname)"
          variant="cyber"
          size="md"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          placeholder="8.8.8.8"
          disabled={loading}
          fullWidth
          aria-required="true"
        />

        <div className={styles.field}>
          <label htmlFor="nmap-scan-profile" className={styles.label}>
            Perfil de Scan
          </label>
          <select
            id="nmap-scan-profile"
            value={selectedProfile}
            onChange={(e) => setSelectedProfile(e.target.value)}
            className={styles.select}
            disabled={loading}
            aria-label="Select scan profile">
            {Object.entries(profiles).map(([key, profile]) => (
              <option key={key} value={key}>
                {profile.name} - {profile.description}
              </option>
            ))}
          </select>
        </div>

        <Input
          label="Argumentos Customizados (opcional)"
          variant="cyber"
          size="sm"
          value={customArgs}
          onChange={(e) => setCustomArgs(e.target.value)}
          placeholder="-p 1-1000 --script vuln"
          disabled={loading}
          fullWidth
        />

        <Button
          type="submit"
          variant="cyber"
          size="md"
          disabled={loading || !target.trim()}
          loading={loading}
          fullWidth
          aria-label="Start Nmap scan">
          {loading ? 'EXECUTANDO SCAN...' : 'INICIAR SCAN'}
        </Button>
      </form>

      {loading && (
        <div className={styles.visuallyHidden} role="status" aria-live="polite">
          Executing Nmap scan...
        </div>
      )}

      {scanHistory.length > 0 && (
        <fieldset className={styles.history}>
          <legend className={styles.historyLabel}>HISTÓRICO RECENTE:</legend>
          <div className={styles.historyItems} role="group" aria-label="Recent scans">
            {scanHistory.slice(0, 5).map((item, index) => (
              <button
                key={index}
                type="button"
                onClick={() => {
                  setTarget(item.target);
                  setSelectedProfile(item.profile);
                }}
                className={styles.historyItem}
                aria-label={`Load scan: ${item.target} with ${item.profile} profile from ${item.timestamp}`}>
                {item.target} ({item.profile}) - {item.timestamp}
              </button>
            ))}
          </div>
        </fieldset>
      )}
    </div>
  );
};

export default ScanForm;
