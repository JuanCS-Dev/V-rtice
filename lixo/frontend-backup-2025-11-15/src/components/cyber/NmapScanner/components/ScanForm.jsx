/**
 * NMAP SCAN FORM - Semantic Form for Network Scanning
 *
 * AI-FIRST DESIGN:
 * - <form> with proper structure
 * - All inputs labeled
 * - <fieldset> for history group
 * - aria-live for loading status
 *
 * SECURITY (Boris Cherny Standard):
 * - GAP #11 FIXED: Command injection prevention in customArgs
 * - GAP #10 FIXED: IP address validation
 * - GAP #13 FIXED: Port validation (if applicable)
 * - GAP #15 FIXED: maxLength on all inputs
 * - GAP #16 FIXED: Whitespace-only input prevention
 *
 * @version 3.0.0 (Security Hardened)
 */

import React, { useState } from "react";
import { Input, Button } from "../../../shared";
import { useKeyPress } from "../../../../hooks";
import {
  validateNmapArgs,
  validateIP,
  validateDomain,
  validateText,
} from "../../../../utils/validation";
import {
  sanitizeCommandArgs,
  sanitizePlainText,
} from "../../../../utils/sanitization";
import styles from "./ScanForm.module.css";

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
  // Error states for validation feedback
  const [targetError, setTargetError] = useState(null);
  const [customArgsError, setCustomArgsError] = useState(null);

  // Secure target input handler
  const handleTargetChange = (e) => {
    const sanitized = sanitizePlainText(e.target.value);
    setTarget(sanitized);
    // Clear error on change
    if (targetError) setTargetError(null);
  };

  // CRITICAL: Secure custom args handler - GAP #11 FIX
  const handleCustomArgsChange = (e) => {
    const sanitized = sanitizeCommandArgs(e.target.value);
    setCustomArgs(sanitized);
    // Clear error on change
    if (customArgsError) setCustomArgsError(null);
  };

  // Validate target on blur
  const handleTargetBlur = () => {
    if (!target.trim()) {
      return; // Empty is OK, just won't be able to submit
    }

    // Try IP validation first
    const ipResult = validateIP(target);
    if (ipResult.valid) {
      setTargetError(null);
      return;
    }

    // Try domain validation
    const domainResult = validateDomain(target);
    if (domainResult.valid) {
      setTargetError(null);
      return;
    }

    // Check if it's a CIDR notation (IP with /subnet)
    if (/^[\d.]+\/\d+$/.test(target)) {
      const ipPart = target.split("/")[0];
      const ipCheck = validateIP(ipPart);
      if (ipCheck.valid) {
        setTargetError(null);
        return;
      }
    }

    setTargetError("Invalid target. Use IP address, domain, or CIDR notation");
  };

  // CRITICAL: Validate custom args on blur - GAP #11 FIX
  const handleCustomArgsBlur = () => {
    if (!customArgs.trim()) {
      setCustomArgsError(null);
      return; // Empty is OK
    }

    const result = validateNmapArgs(customArgs);
    if (!result.valid) {
      setCustomArgsError(result.error);
    } else {
      setCustomArgsError(null);
    }
  };

  useKeyPress("Enter", () => {
    if (target.trim() && !loading && !targetError && !customArgsError) {
      onScan();
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validate before submission
    let hasErrors = false;

    // Validate target
    if (!target.trim()) {
      setTargetError("Target is required");
      hasErrors = true;
    } else {
      handleTargetBlur();
      if (targetError) hasErrors = true;
    }

    // Validate custom args
    if (customArgs.trim()) {
      const result = validateNmapArgs(customArgs);
      if (!result.valid) {
        setCustomArgsError(result.error);
        hasErrors = true;
      }
    }

    // Only proceed if no errors
    if (!hasErrors && !loading) {
      onScan();
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>NMAP NETWORK SCANNER</h2>

      <form
        className={styles.form}
        onSubmit={handleSubmit}
        aria-label="Nmap scan configuration"
      >
        <div>
          <Input
            label="Target (IP/CIDR/Hostname)"
            variant="cyber"
            size="md"
            value={target}
            onChange={handleTargetChange}
            onBlur={handleTargetBlur}
            placeholder="8.8.8.8"
            disabled={loading}
            fullWidth
            maxLength={500}
            aria-required="true"
            aria-invalid={!!targetError}
            aria-describedby={targetError ? "target-error" : undefined}
          />
          {targetError && (
            <div
              id="target-error"
              className={styles.error}
              role="alert"
              aria-live="polite"
            >
              {targetError}
            </div>
          )}
        </div>

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
            aria-label="Select scan profile"
          >
            {Object.entries(profiles).map(([key, profile]) => (
              <option key={key} value={key}>
                {profile.name} - {profile.description}
              </option>
            ))}
          </select>
        </div>

        <div>
          <Input
            label="Argumentos Customizados (opcional)"
            variant="cyber"
            size="sm"
            value={customArgs}
            onChange={handleCustomArgsChange}
            onBlur={handleCustomArgsBlur}
            placeholder="-p 1-1000 --script vuln"
            disabled={loading}
            fullWidth
            maxLength={500}
            aria-invalid={!!customArgsError}
            aria-describedby={customArgsError ? "args-error" : undefined}
          />
          {customArgsError && (
            <div
              id="args-error"
              className={styles.error}
              role="alert"
              aria-live="assertive"
            >
              ⚠️ {customArgsError}
            </div>
          )}
        </div>

        <Button
          type="submit"
          variant="cyber"
          size="md"
          disabled={
            loading || !target.trim() || !!targetError || !!customArgsError
          }
          loading={loading}
          fullWidth
          aria-label="Start Nmap scan"
        >
          {loading ? "EXECUTANDO SCAN..." : "INICIAR SCAN"}
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
          <div
            className={styles.historyItems}
            role="group"
            aria-label="Recent scans"
          >
            {scanHistory.slice(0, 5).map((item, index) => (
              <button
                key={index}
                type="button"
                onClick={() => {
                  setTarget(item.target);
                  setSelectedProfile(item.profile);
                }}
                className={styles.historyItem}
                aria-label={`Load scan: ${item.target} with ${item.profile} profile from ${item.timestamp}`}
              >
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
