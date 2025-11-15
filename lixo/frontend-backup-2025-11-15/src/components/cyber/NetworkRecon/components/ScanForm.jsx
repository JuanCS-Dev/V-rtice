/**
 * NETWORK RECON SCAN FORM - Semantic Form with Radio Group for Scan Types
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <form> with onSubmit handler
 * - role="radiogroup" for scan type buttons
 * - role="radio" + aria-checked for custom radio buttons
 * - <fieldset> for port presets and advanced options
 * - aria-live for loading status
 * - All emojis in aria-hidden spans
 *
 * WCAG 2.1 AAA Compliance:
 * - All form controls labeled
 * - Radio group with proper ARIA
 * - Checkbox inputs properly labeled
 * - Loading status announced
 * - Keyboard accessible
 *
 * SECURITY (Boris Cherny Standard):
 * - GAP #10 FIXED: IP address validation
 * - GAP #13 FIXED: Port validation
 * - maxLength on all inputs
 * - Sanitization of user input
 *
 * @version 3.0.0 (Security Hardened)
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React, { useState } from "react";
import {
  validateIP,
  validateDomain,
  validatePorts,
} from "../../../../utils/validation";
import { sanitizePlainText } from "../../../../utils/sanitization";

export const ScanForm = ({ config, onChange, onSubmit, isScanning }) => {
  // Error states for validation feedback
  const [targetError, setTargetError] = useState(null);
  const [portsError, setPortsError] = useState(null);

  const handleChange = (field, value) => {
    onChange({ ...config, [field]: value });
    // Clear errors on change
    if (field === "target" && targetError) setTargetError(null);
    if (field === "ports" && portsError) setPortsError(null);
  };

  // Secure target input handler
  const handleTargetChange = (e) => {
    const sanitized = sanitizePlainText(e.target.value);
    handleChange("target", sanitized);
  };

  // Secure ports input handler
  const handlePortsChange = (e) => {
    const sanitized = sanitizePlainText(e.target.value);
    handleChange("ports", sanitized);
  };

  // Validate target on blur
  const handleTargetBlur = () => {
    if (!config.target.trim()) {
      return;
    }

    // Try IP validation first
    const ipResult = validateIP(config.target);
    if (ipResult.valid) {
      setTargetError(null);
      return;
    }

    // Try domain validation
    const domainResult = validateDomain(config.target);
    if (domainResult.valid) {
      setTargetError(null);
      return;
    }

    // Check if it's a CIDR notation
    if (/^[\d.]+\/\d+$/.test(config.target)) {
      const ipPart = config.target.split("/")[0];
      const ipCheck = validateIP(ipPart);
      if (ipCheck.valid) {
        setTargetError(null);
        return;
      }
    }

    setTargetError("Invalid target. Use IP address, domain, or CIDR notation");
  };

  // Validate ports on blur
  const handlePortsBlur = () => {
    if (!config.ports.trim()) {
      setPortsError(null);
      return;
    }

    const result = validatePorts(config.ports);
    if (!result.valid) {
      setPortsError(result.error);
    } else {
      setPortsError(null);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validate before submission
    let hasErrors = false;

    // Validate target
    if (!config.target.trim()) {
      setTargetError("Target is required");
      hasErrors = true;
    } else {
      handleTargetBlur();
      if (targetError) hasErrors = true;
    }

    // Validate ports
    if (config.ports.trim()) {
      const result = validatePorts(config.ports);
      if (!result.valid) {
        setPortsError(result.error);
        hasErrors = true;
      }
    }

    // Only proceed if no errors
    if (!hasErrors && !isScanning) {
      onSubmit();
    }
  };

  const scanTypes = [
    {
      id: "quick",
      name: "Quick Scan",
      desc: "Top 1000 ports | ~30s",
      icon: "⚡",
      color: "cyan",
    },
    {
      id: "full",
      name: "Full Scan",
      desc: "All 65535 ports | ~5min",
      icon: "🔥",
      color: "orange",
    },
    {
      id: "stealth",
      name: "Stealth Scan",
      desc: "SYN scan + evasion | ~2min",
      icon: "👻",
      color: "purple",
    },
    {
      id: "aggressive",
      name: "Aggressive",
      desc: "OS + Service detection | ~3min",
      icon: "💥",
      color: "red",
    },
  ];

  const portPresets = [
    { label: "Top 100", value: "1-100" },
    { label: "Top 1000", value: "1-1000" },
    { label: "All Ports", value: "1-65535" },
    { label: "Web Ports", value: "80,443,8000,8080,8443" },
    { label: "Database", value: "1433,3306,5432,27017" },
    { label: "Custom", value: "custom" },
  ];

  return (
    <form
      onSubmit={handleSubmit}
      aria-label="Network reconnaissance scan configuration"
      className="space-y-6"
    >
      {/* Target Input */}
      <div className="bg-gradient-to-br from-red-900/20 to-orange-900/20 border border-red-400/30 rounded-lg p-6">
        <label
          htmlFor="recon-target-input"
          className="block text-red-400 font-bold mb-3 text-sm tracking-wider"
        >
          <span aria-hidden="true">🎯</span> TARGET
        </label>
        <input
          id="recon-target-input"
          type="text"
          value={config.target}
          onChange={handleTargetChange}
          onBlur={handleTargetBlur}
          placeholder="192.168.1.0/24, 10.0.0.1, example.com"
          className="w-full bg-black/50 border border-red-400/30 rounded px-4 py-3 text-red-400 font-mono focus:outline-none focus:border-red-400 transition-all"
          disabled={isScanning}
          maxLength={500}
          aria-required="true"
          aria-invalid={!!targetError}
          aria-describedby={targetError ? "target-error" : "target-hint"}
        />
        {targetError ? (
          <div
            id="target-error"
            className="text-red-400 text-xs mt-2 flex items-center gap-1"
            role="alert"
            aria-live="polite"
          >
            <span aria-hidden="true">⚠️</span>
            {targetError}
          </div>
        ) : (
          <p id="target-hint" className="text-red-400/50 text-xs mt-2">
            IP, CIDR range, or hostname
          </p>
        )}
      </div>

      {/* Scan Type Selection */}
      <fieldset>
        <legend className="block text-red-400 font-bold mb-3 text-sm tracking-wider">
          <span aria-hidden="true">⚙️</span> SCAN TYPE
        </legend>
        <div
          role="radiogroup"
          aria-label="Scan type selection"
          className="grid grid-cols-2 gap-4"
        >
          {scanTypes.map((type) => (
            <button
              key={type.id}
              type="button"
              role="radio"
              aria-checked={config.scanType === type.id}
              aria-label={`${type.name}: ${type.desc}`}
              onClick={() => handleChange("scanType", type.id)}
              disabled={isScanning}
              className={`
                p-4 rounded-lg border-2 transition-all text-left
                ${
                  config.scanType === type.id
                    ? `border-${type.color}-400 bg-${type.color}-400/20`
                    : "border-gray-600/30 bg-black/30 hover:border-gray-500"
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl" aria-hidden="true">
                  {type.icon}
                </span>
                <span
                  className={`font-bold ${config.scanType === type.id ? `text-${type.color}-400` : "text-gray-400"}`}
                >
                  {type.name}
                </span>
              </div>
              <p
                className={`text-xs ${config.scanType === type.id ? `text-${type.color}-400/70` : "text-gray-500"}`}
              >
                {type.desc}
              </p>
            </button>
          ))}
        </div>
      </fieldset>

      {/* Port Configuration */}
      <fieldset>
        <legend className="block text-red-400 font-bold mb-3 text-sm tracking-wider">
          <span aria-hidden="true">🔌</span> PORT RANGE
        </legend>
        <div
          className="flex gap-2 mb-3"
          role="group"
          aria-label="Port range presets"
        >
          {portPresets.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => {
                if (preset.value !== "custom") {
                  handleChange("ports", preset.value);
                }
              }}
              disabled={isScanning}
              aria-label={`Set port range to ${preset.label}`}
              className={`
                px-4 py-2 rounded text-sm font-bold transition-all
                ${
                  config.ports === preset.value
                    ? "bg-red-400/20 text-red-400 border border-red-400"
                    : "bg-black/30 text-red-400/50 border border-red-400/20 hover:text-red-400"
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              {preset.label}
            </button>
          ))}
        </div>

        <label htmlFor="port-input" className="sr-only">
          Custom port range
        </label>
        <input
          id="port-input"
          type="text"
          value={config.ports}
          onChange={handlePortsChange}
          onBlur={handlePortsBlur}
          placeholder="1-1000, 8000-9000, 80,443"
          className="w-full bg-black/50 border border-red-400/30 rounded px-4 py-2 text-red-400 font-mono text-sm focus:outline-none focus:border-red-400 transition-all"
          disabled={isScanning}
          maxLength={100}
          aria-invalid={!!portsError}
          aria-describedby={portsError ? "ports-error" : undefined}
        />
        {portsError && (
          <div
            id="ports-error"
            className="text-red-400 text-xs mt-2 flex items-center gap-1"
            role="alert"
            aria-live="polite"
          >
            <span aria-hidden="true">⚠️</span>
            {portsError}
          </div>
        )}
      </fieldset>

      {/* Advanced Options */}
      <fieldset className="bg-black/30 border border-red-400/20 rounded-lg p-4">
        <legend className="block text-red-400/70 font-bold mb-3 text-xs tracking-wider">
          <span aria-hidden="true">🔧</span> ADVANCED OPTIONS
        </legend>
        <div className="grid grid-cols-2 gap-4">
          <label
            htmlFor="service-detection-checkbox"
            className="flex items-center gap-2 text-red-400/70 text-sm cursor-pointer"
          >
            <input
              id="service-detection-checkbox"
              type="checkbox"
              checked={config.serviceDetection}
              onChange={(e) =>
                handleChange("serviceDetection", e.target.checked)
              }
              disabled={isScanning}
              className="w-4 h-4 accent-red-400"
            />
            Service Detection
          </label>

          <label
            htmlFor="os-detection-checkbox"
            className="flex items-center gap-2 text-red-400/70 text-sm cursor-pointer"
          >
            <input
              id="os-detection-checkbox"
              type="checkbox"
              checked={config.osDetection}
              onChange={(e) => handleChange("osDetection", e.target.checked)}
              disabled={isScanning}
              className="w-4 h-4 accent-red-400"
            />
            OS Detection
          </label>
        </div>
      </fieldset>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isScanning || !config.target}
        aria-label={
          isScanning ? "Scan in progress" : "Launch reconnaissance scan"
        }
        className={`
          w-full py-4 rounded-lg font-bold text-lg tracking-wider transition-all
          ${
            isScanning
              ? "bg-orange-400/20 text-orange-400 border-2 border-orange-400 cursor-wait"
              : "bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white border-2 border-red-400 hover:border-red-300"
          }
          disabled:opacity-50 disabled:cursor-not-allowed
          shadow-lg shadow-red-400/20
        `}
      >
        {isScanning ? (
          <span className="flex items-center justify-center gap-3">
            <span className="animate-spin" aria-hidden="true">
              ⚙️
            </span>
            SCANNING IN PROGRESS...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-3">
            <span aria-hidden="true">🚀</span>
            LAUNCH SCAN
          </span>
        )}
      </button>

      {isScanning && (
        <div className="sr-only" role="status" aria-live="polite">
          Network reconnaissance scan in progress...
        </div>
      )}

      {!config.target && (
        <p className="text-center text-red-400/50 text-sm">
          Enter a target to begin reconnaissance
        </p>
      )}
    </form>
  );
};

export default ScanForm;
