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
  // Trigger analysis on Enter key
  useKeyPress('Enter', () => {
    if (ipAddress.trim() && !loading && !loadingMyIp) {
      onAnalyze();
    }
  });

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>IP INTELLIGENCE & GEOLOCATION</h2>

      {/* Search Bar */}
      <div className={styles.searchBar}>
        <Input
          variant="cyber"
          size="lg"
          value={ipAddress}
          onChange={(e) => setIpAddress(e.target.value)}
          placeholder=">>> INSERIR ENDEREÇO IP PARA ANÁLISE"
          disabled={loading}
          fullWidth
          className={styles.input}
        />

        <div className={styles.actions}>
          <Button
            variant="cyber"
            size="md"
            onClick={onAnalyze}
            disabled={loading || loadingMyIp || !ipAddress.trim()}
            loading={loading}
            fullWidth
          >
            {loading ? 'ANALISANDO...' : 'EXECUTAR ANÁLISE'}
          </Button>

          <Button
            variant="warning"
            size="md"
            onClick={onAnalyzeMyIP}
            disabled={loading || loadingMyIp}
            loading={loadingMyIp}
            icon="fas fa-bullseye"
          >
            {loadingMyIp ? 'DETECTANDO...' : 'MEU IP'}
          </Button>
        </div>
      </div>

      {/* Search History */}
      {searchHistory.length > 0 && (
        <div className={styles.history}>
          <span className={styles.historyLabel}>HISTÓRICO:</span>
          <div className={styles.historyItems}>
            {searchHistory.slice(0, 5).map((historicIP, index) => (
              <button
                key={index}
                onClick={() => onSelectHistory(historicIP)}
                className={styles.historyItem}
              >
                {historicIP}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchHeader;
