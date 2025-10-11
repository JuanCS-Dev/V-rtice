import React from 'react';
import AskMaximusButton from '../../shared/AskMaximusButton';
import { useNmapScanner } from './hooks/useNmapScanner';
import { ScanForm } from './components/ScanForm';
import { ScanResults } from './components/ScanResults';
import styles from './NmapScanner.module.css';

/**
 * NmapScanner - Scanner de rede completo usando Nmap
 * Suporta múltiplos perfis de scan e análise de segurança
 */
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
    executeScan
  } = useNmapScanner();

  return (
    <div className={styles.container}>
      {scanResult && (
        <div style={{ marginBottom: '1rem' }}>
          <AskMaximusButton
            context={{
              type: 'nmap_scan',
              data: scanResult,
              target,
              profile: selectedProfile
            }}
            prompt="Analyze these Nmap scan results and identify security vulnerabilities, open ports risks, and recommendations"
            size="medium"
            variant="secondary"
          />
        </div>
      )}

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

      {scanResult && <ScanResults result={scanResult} />}
    </div>
  );
};

export default NmapScanner;
