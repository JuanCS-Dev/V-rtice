/**
 * NMAP SCANNER - Advanced Network Mapping Scanner
 *
 * Scanner de rede completo usando Nmap
 * Suporta múltiplos perfis de scan e análise de segurança
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="nmap-scanner"
 * - <header> visuallyHidden (UI has no distinct header)
 * - <section> for AI assistance (conditional)
 * - <section> for scan form
 * - <section> for scan results (conditional)
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="nmap-scanner"
 * - Monitor scan via data-maximus-status
 * - Access scan form via data-maximus-section="scan-form"
 * - Interpret scan results via semantic structure
 *
 * @version 2.0.0 (Maximus Vision)
 * @author Gemini + Maximus Vision Protocol
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 */

import React from "react";
import AskMaximusButton from "../../shared/AskMaximusButton";
import { useNmapScanner } from "./hooks/useNmapScanner";
import { ScanForm } from "./components/ScanForm";
import { ScanResults } from "./components/ScanResults";
import styles from "./NmapScanner.module.css";

export const NmapScanner = () => {
  const {
    target,
    setTarget,
    selectedProfile,
    setSelectedProfile,
    customArgs,
    setCustomArgs,
    loading,
    scanResult,
    profiles,
    scanHistory,
    executeScan,
  } = useNmapScanner();

  return (
    <article
      className={styles.container}
      role="article"
      aria-labelledby="nmap-scanner-title"
      data-maximus-tool="nmap-scanner"
      data-maximus-category="shared"
      data-maximus-status={loading ? "scanning" : "ready"}
    >
      <header className={styles.visuallyHidden}>
        <h2 id="nmap-scanner-title">Nmap Scanner</h2>
      </header>

      {scanResult && (
        <section
          style={{ marginBottom: "1rem" }}
          role="region"
          aria-label="AI assistance"
          data-maximus-section="ai-assistance"
        >
          <AskMaximusButton
            context={{
              type: "nmap_scan",
              data: scanResult,
              target,
              profile: selectedProfile,
            }}
            prompt="Analyze these Nmap scan results and identify security vulnerabilities, open ports risks, and recommendations"
            size="medium"
            variant="secondary"
          />
        </section>
      )}

      <section
        role="region"
        aria-label="Nmap scan configuration form"
        data-maximus-section="scan-form"
      >
        <ScanForm
          target={target}
          setTarget={setTarget}
          selectedProfile={selectedProfile}
          setSelectedProfile={setSelectedProfile}
          customArgs={customArgs}
          setCustomArgs={setCustomArgs}
          profiles={profiles}
          onScan={executeScan}
          loading={loading}
          scanHistory={scanHistory}
        />
      </section>

      {scanResult && (
        <section
          role="region"
          aria-label="Nmap scan results"
          data-maximus-section="results"
        >
          <ScanResults result={scanResult} />
        </section>
      )}
    </article>
  );
};

export default NmapScanner;
