import React from 'react';
import { Input, Button } from '../../../shared';
import { useKeyPress } from '../../../../hooks';
import styles from './SearchHeader.module.css';

export const SearchHeader = ({
  domain,
  setDomain,
  loading,
  onAnalyze,
  searchHistory,
  onSelectHistory
}) => {
  useKeyPress('Enter', () => {
    if (domain.trim() && !loading) {
      onAnalyze();
    }
  });

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>DOMAIN INTELLIGENCE ANALYZER</h2>

      <div className={styles.searchBar}>
        <Input
          variant="cyber"
          size="lg"
          value={domain}
          onChange={(e) => setDomain(e.target.value.toLowerCase())}
          placeholder=">>> INSERIR DOMÍNIO PARA ANÁLISE"
          disabled={loading}
          fullWidth
          className={styles.input}
        />

        <Button
          variant="cyber"
          size="md"
          onClick={onAnalyze}
          disabled={loading || !domain.trim()}
          loading={loading}
        >
          {loading ? 'ANALISANDO...' : 'EXECUTAR ANÁLISE'}
        </Button>
      </div>

      {searchHistory.length > 0 && (
        <div className={styles.history}>
          <span className={styles.historyLabel}>HISTÓRICO:</span>
          <div className={styles.historyItems}>
            {searchHistory.slice(0, 5).map((historicDomain, index) => (
              <button
                key={index}
                onClick={() => onSelectHistory(historicDomain)}
                className={styles.historyItem}
              >
                {historicDomain}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchHeader;
