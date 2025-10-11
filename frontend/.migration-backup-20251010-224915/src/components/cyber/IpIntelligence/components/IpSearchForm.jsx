import React from 'react';
import { Button, Input } from '../../../shared';
import styles from './IpSearchForm.module.css';

/**
 * Form for IP intelligence search, including input, analyze buttons, and search history.
 */
const IpSearchForm = ({
  ipAddress,
  setIpAddress,
  loading,
  loadingMyIp,
  searchHistory,
  handleAnalyzeIP,
  handleAnalyzeMyIP,
}) => {

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading && !loadingMyIp) {
      handleAnalyzeIP(ipAddress);
    }
  };

  return (
    <div className={styles.searchContainer}>
      <div className={styles.inputGroup}>
        <Input
          type="text"
          value={ipAddress}
          onChange={(e) => setIpAddress(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder=">>> INSERIR ENDEREÇO IP PARA ANÁLISE"
          variant="cyber"
          size="lg"
          disabled={loading || loadingMyIp}
          icon={loading && <div className={styles.loadingSpinner}></div>}
        />

        <div className={styles.buttonGroup}>
          <Button
            onClick={() => handleAnalyzeIP(ipAddress)}
            disabled={loading || loadingMyIp || !ipAddress.trim()}
            variant="cyber"
            size="lg"
            className={styles.analyzeButton}
          >
            {loading ? 'ANALISANDO...' : 'EXECUTAR ANÁLISE'}
          </Button>

          <Button
            onClick={handleAnalyzeMyIP}
            disabled={loading || loadingMyIp}
            variant="warning"
            size="lg"
            className={styles.myIpButton}
            icon={loadingMyIp ? <i className="fas fa-spinner fa-spin"></i> : <i className="fas fa-crosshairs"></i>}
          >
            MEU IP
          </Button>
        </div>
      </div>

      {searchHistory.length > 0 && (
        <div className={styles.historyContainer}>
          <span className={styles.historyLabel}>HISTÓRICO:</span>
          {searchHistory.slice(0, 5).map((historicIP, index) => (
            <button
              key={index}
              onClick={() => setIpAddress(historicIP)}
              className={styles.historyButton}
            >
              {historicIP}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default React.memo(IpSearchForm);
