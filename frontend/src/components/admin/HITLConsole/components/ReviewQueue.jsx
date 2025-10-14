/**
 * ReviewQueue - List of pending APVs for human review
 *
 * Features:
 * - Paginated list of pending APVs
 * - Filters by severity, patch_strategy, wargame_verdict
 * - Visual severity badges
 * - Waiting time indicator
 * - Click to select APV for review
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import PropTypes from 'prop-types';
import styles from './ReviewQueue.module.css';

const ReviewQueue = ({
  reviews,
  loading,
  error,
  selectedAPV,
  onSelectAPV,
  filters,
  onFiltersChange,
}) => {
  const { t } = useTranslation();

  // Get severity badge class
  const getSeverityClass = (severity) => {
    const severityLower = severity?.toLowerCase();
    if (severityLower === 'critical') return styles.severityCritical;
    if (severityLower === 'high') return styles.severityHigh;
    if (severityLower === 'medium') return styles.severityMedium;
    if (severityLower === 'low') return styles.severityLow;
    return styles.severityUnknown;
  };

  // Get verdict badge class
  const getVerdictClass = (verdict) => {
    const verdictLower = verdict?.toLowerCase();
    if (verdictLower === 'success') return styles.verdictSuccess;
    if (verdictLower === 'partial') return styles.verdictPartial;
    if (verdictLower === 'failure') return styles.verdictFailure;
    if (verdictLower === 'inconclusive') return styles.verdictInconclusive;
    return styles.verdictUnknown;
  };

  // Get verdict icon
  const getVerdictIcon = (verdict) => {
    const verdictLower = verdict?.toLowerCase();
    if (verdictLower === 'success') return '✅';
    if (verdictLower === 'partial') return '⚠️';
    if (verdictLower === 'failure') return '❌';
    if (verdictLower === 'inconclusive') return '❓';
    return '⏹️';
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <h2 className={styles.title}>
          {t('hitl.queue.title', 'REVIEW QUEUE')}
        </h2>
        <span className={styles.count}>
          {reviews.length} {t('hitl.queue.pending', 'Pending')}
        </span>
      </div>

      {/* Filters */}
      <div className={styles.filters}>
        <select
          className={styles.filterSelect}
          value={filters.severity || ''}
          onChange={(e) => onFiltersChange({ ...filters, severity: e.target.value || null })}
          aria-label={t('hitl.queue.filter_severity', 'Filter by severity')}
        >
          <option value="">{t('hitl.queue.all_severities', 'All Severities')}</option>
          <option value="critical">{t('hitl.queue.critical', 'Critical')}</option>
          <option value="high">{t('hitl.queue.high', 'High')}</option>
          <option value="medium">{t('hitl.queue.medium', 'Medium')}</option>
          <option value="low">{t('hitl.queue.low', 'Low')}</option>
        </select>

        <select
          className={styles.filterSelect}
          value={filters.wargame_verdict || ''}
          onChange={(e) => onFiltersChange({ ...filters, wargame_verdict: e.target.value || null })}
          aria-label={t('hitl.queue.filter_verdict', 'Filter by verdict')}
        >
          <option value="">{t('hitl.queue.all_verdicts', 'All Verdicts')}</option>
          <option value="success">{t('hitl.queue.success', 'Success')}</option>
          <option value="partial">{t('hitl.queue.partial', 'Partial')}</option>
          <option value="failure">{t('hitl.queue.failure', 'Failure')}</option>
          <option value="inconclusive">{t('hitl.queue.inconclusive', 'Inconclusive')}</option>
        </select>
      </div>

      {/* Queue List */}
      <div className={styles.queueList} role="list">
        {loading && (
          <div className={styles.loading}>
            <div className={styles.spinner} />
            <p>{t('hitl.queue.loading', 'Loading reviews...')}</p>
          </div>
        )}

        {error && (
          <div className={styles.error}>
            <p>❌ {t('hitl.queue.error', 'Error loading reviews')}</p>
            <p className={styles.errorDetail}>{error.message}</p>
          </div>
        )}

        {!loading && !error && reviews.length === 0 && (
          <div className={styles.empty}>
            <p className={styles.emptyIcon}>✅</p>
            <p>{t('hitl.queue.empty', 'No reviews pending')}</p>
            <p className={styles.emptyHint}>
              {t('hitl.queue.empty_hint', 'All APVs have been reviewed')}
            </p>
          </div>
        )}

        {!loading && !error && reviews.map((review) => (
          <div
            key={review.apv_id}
            role="listitem"
            className={`${styles.queueItem} ${
              selectedAPV === review.apv_id ? styles.queueItemSelected : ''
            }`}
            onClick={() => onSelectAPV(review)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelectAPV(review);
              }
            }}
            tabIndex={0}
            aria-label={`Review ${review.apv_code} - ${review.severity} severity`}
          >
            {/* Header: Severity + APV Code */}
            <div className={styles.queueItemHeader}>
              <span className={`${styles.severityBadge} ${getSeverityClass(review.severity)}`}>
                {review.severity?.toUpperCase()}
              </span>
              <span className={styles.apvCode}>{review.apv_code}</span>
            </div>

            {/* Info */}
            <div className={styles.queueItemInfo}>
              <p className={styles.cveId}>{review.cve_id}</p>
              <p className={styles.packageName}>{review.package_name}</p>
            </div>

            {/* Footer: Verdict + Wait Time */}
            <div className={styles.queueItemFooter}>
              <span className={`${styles.verdictBadge} ${getVerdictClass(review.wargame_verdict)}`}>
                {getVerdictIcon(review.wargame_verdict)}
                {review.wargame_verdict?.toUpperCase()}
              </span>
              <span className={styles.waitTime}>
                ⏱️ {review.waiting_since?.toFixed(1)}h
              </span>
            </div>

            {/* Confidence Bar */}
            <div className={styles.confidenceBar}>
              <div
                className={styles.confidenceFill}
                style={{ width: `${(review.confirmation_confidence * 100).toFixed(0)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

ReviewQueue.propTypes = {
  reviews: PropTypes.arrayOf(
    PropTypes.shape({
      apv_id: PropTypes.string.isRequired,
      apv_code: PropTypes.string.isRequired,
      cve_id: PropTypes.string.isRequired,
      severity: PropTypes.string.isRequired,
      package_name: PropTypes.string.isRequired,
      wargame_verdict: PropTypes.string,
      confirmation_confidence: PropTypes.number,
      waiting_since: PropTypes.number,
    })
  ),
  loading: PropTypes.bool,
  error: PropTypes.object,
  selectedAPV: PropTypes.string,
  onSelectAPV: PropTypes.func.isRequired,
  filters: PropTypes.shape({
    severity: PropTypes.string,
    patch_strategy: PropTypes.string,
    wargame_verdict: PropTypes.string,
  }),
  onFiltersChange: PropTypes.func.isRequired,
};

ReviewQueue.defaultProps = {
  reviews: [],
  loading: false,
  error: null,
  selectedAPV: null,
  filters: {},
};

export default ReviewQueue;
