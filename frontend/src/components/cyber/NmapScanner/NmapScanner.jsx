import React from 'react';
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
