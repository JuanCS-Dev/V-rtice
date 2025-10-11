import React, { useState } from 'react';
import { Button, Input } from '../../../shared';
import styles from './BreachSearchForm.module.css';

const QUERY_TYPES = [
    { value: 'email', label: 'E-mail', placeholder: 'user@example.com', icon: '📧' },
    { value: 'username', label: 'Username', placeholder: 'john_doe', icon: '👤' },
    { value: 'phone', label: 'Telefone', placeholder: '+5511999999999', icon: '📱' },
    { value: 'domain', label: 'Domínio', placeholder: 'example.com', icon: '🌐' }
];

/**
 * Form for submitting a breach data search.
 * Handles query input and query type selection.
 */
export const BreachSearchForm = ({ onSearch, loading, error }) => {
  const [query, setQuery] = useState('');
  const [queryType, setQueryType] = useState('email');

  const currentQueryType = QUERY_TYPES.find(qt => qt.value === queryType);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query, queryType);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
        handleSubmit(e);
    }
  }

  return (
    <div className={styles.formContainer}>
        <div className={styles.queryTypeSelector} role="group" aria-labelledby="query-type-label">
            <span id="query-type-label" className={styles.visuallyHidden}>Query Type</span>
            {QUERY_TYPES.map(type => (
              <button
                key={type.value}
                type="button"
                aria-pressed={queryType === type.value}
                className={`${styles.typeButton} ${queryType === type.value ? styles.active : ''}`}
                onClick={() => setQueryType(type.value)}
                disabled={loading}
              >
                <span className={styles.typeIcon}>{type.icon}</span>
                <span className={styles.typeLabel}>{type.label}</span>
              </button>
            ))}
        </div>

        <form onSubmit={handleSubmit} className={styles.searchForm}>
            <label htmlFor="search-input" className={styles.visuallyHidden}>Search Query</label>
            <Input
              id="search-input"
              type="text"
              placeholder={currentQueryType?.placeholder}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
              variant="critical" // Custom variant for breach theme
              size="lg"
              icon={<i className="fas fa-search"></i>}
              error={error}
            />
            <Button
              type="submit"
              variant="danger" // Using danger for the critical theme
              size="lg"
              loading={loading}
              disabled={!query.trim()}
            >
              {loading ? 'BUSCANDO...' : 'BUSCAR'}
            </Button>
        </form>

        <p className={styles.hint}>
            <i className="fas fa-shield-alt"></i>
            Busca em fontes: HIBP, DeHashed, Snusbase, IntelX
        </p>
    </div>
  );
};

export default BreachSearchForm;
