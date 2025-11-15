import React, { useState } from 'react';
import { Button, Input } from '../../../shared';
import { validateEmail } from '../../../../utils/validation';
import { sanitizeEmail } from '../../../../utils/sanitization';
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
 *
 * SECURITY (Boris Cherny Standard):
 * - GAP #12 FIXED: Email validation
 * - maxLength on all inputs
 * - Sanitization of user input
 *
 * @version 2.0.0 (Security Hardened)
 */
export const BreachSearchForm = ({ onSearch, loading, error }) => {
  const [query, setQuery] = useState('');
  const [queryType, setQueryType] = useState('email');
  const [validationError, setValidationError] = useState(null);

  const currentQueryType = QUERY_TYPES.find(qt => qt.value === queryType);

  // Secure input handler
  const handleQueryChange = (e) => {
    let sanitized = e.target.value;

    // Sanitize based on query type
    if (queryType === 'email') {
      sanitized = sanitizeEmail(sanitized);
    }

    setQuery(sanitized);
    if (validationError) setValidationError(null);
  };

  // Validate on blur
  const handleQueryBlur = () => {
    if (!query.trim()) {
      return;
    }

    // Validate email if query type is email
    if (queryType === 'email') {
      const result = validateEmail(query);
      if (!result.valid) {
        setValidationError(result.error);
      } else {
        setValidationError(null);
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validate before submission
    if (!query.trim()) {
      setValidationError('Query is required');
      return;
    }

    // Validate email if query type is email
    if (queryType === 'email') {
      const result = validateEmail(query);
      if (!result.valid) {
        setValidationError(result.error);
        return;
      }
    }

    // Only proceed if no errors
    if (!validationError && !loading) {
      onSearch(query, queryType);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
        handleSubmit(e);
    }
  }

  // Clear validation error when query type changes
  const handleQueryTypeChange = (newType) => {
    setQueryType(newType);
    setValidationError(null);
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
                onClick={() => handleQueryTypeChange(type.value)}
                disabled={loading}
              >
                <span className={styles.typeIcon}>{type.icon}</span>
                <span className={styles.typeLabel}>{type.label}</span>
              </button>
            ))}
        </div>

        <form onSubmit={handleSubmit} className={styles.searchForm}>
            <div>
              <label htmlFor="search-input" className={styles.visuallyHidden}>Search Query</label>
              <Input
                id="search-input"
                type="text"
                placeholder={currentQueryType?.placeholder}
                value={query}
                onChange={handleQueryChange}
                onBlur={handleQueryBlur}
                onKeyPress={handleKeyPress}
                disabled={loading}
                variant="critical"
                size="lg"
                icon={<i className="fas fa-search"></i>}
                error={error}
                maxLength={500}
                aria-invalid={!!validationError}
                aria-describedby={validationError ? "query-error" : undefined}
              />
              {validationError && (
                <div
                  id="query-error"
                  className={styles.error}
                  role="alert"
                  aria-live="polite"
                >
                  {validationError}
                </div>
              )}
            </div>
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
