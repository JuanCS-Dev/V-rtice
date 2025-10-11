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

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>NMAP NETWORK SCANNER</h2>

      <div className={styles.form}>
        <Input
          label="Target (IP/CIDR/Hostname)"
          variant="cyber"
          size="md"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          placeholder="8.8.8.8"
          disabled={loading}
          fullWidth
        />

        <div className={styles.field}>
          <label htmlFor="select-perfil-de-scan-izv4s" className={styles.label}>Perfil de Scan</label>
<select id="select-perfil-de-scan-izv4s"
            value={selectedProfile}
            onChange={(e) => setSelectedProfile(e.target.value)}
            className={styles.select}
            disabled={loading}
          >
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
          variant="cyber"
          size="md"
          onClick={onScan}
          disabled={loading || !target.trim()}
          loading={loading}
          fullWidth
        >
          {loading ? 'EXECUTANDO SCAN...' : 'INICIAR SCAN'}
        </Button>
      </div>

      {scanHistory.length > 0 && (
        <div className={styles.history}>
          <span className={styles.historyLabel}>HISTÓRICO RECENTE:</span>
          <div className={styles.historyItems}>
            {scanHistory.slice(0, 5).map((item, index) => (
              <button
                key={index}
                onClick={() => {
                  setTarget(item.target);
                  setSelectedProfile(item.profile);
                }}
                className={styles.historyItem}
              >
                {item.target} ({item.profile}) - {item.timestamp}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanForm;
