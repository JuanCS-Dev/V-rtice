/**
 * ReviewDetails - Display complete APV review context
 *
 * Features:
 * - Tabs for CVE, Patch, Wargame, Validation
 * - Syntax highlighted diff viewer
 * - Wargame evidence display
 * - Validation warnings
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import PropTypes from 'prop-types';
import styles from './ReviewDetails.module.css';

const ReviewDetails = ({ review, loading, apvSelected }) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('cve');

  const tabIds = ['cve', 'patch', 'wargame', 'validation'];

  const handleTabKeyDown = (e) => {
    const currentIndex = tabIds.indexOf(activeTab);

    if (e.key === 'ArrowRight') {
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % tabIds.length;
      setActiveTab(tabIds[nextIndex]);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + tabIds.length) % tabIds.length;
      setActiveTab(tabIds[prevIndex]);
    } else if (e.key === 'Home') {
      e.preventDefault();
      setActiveTab(tabIds[0]);
    } else if (e.key === 'End') {
      e.preventDefault();
      setActiveTab(tabIds[tabIds.length - 1]);
    }
  };

  if (!apvSelected) {
    return (
      <div className={styles.emptyState}>
        <p className={styles.emptyIcon}>👈</p>
        <p>{t('hitl.details.select', 'Select an APV to review')}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner} />
        <p>{t('hitl.details.loading', 'Loading details...')}</p>
      </div>
    );
  }

  if (!review) {
    return (
      <div className={styles.error}>
        <p>❌ {t('hitl.details.error', 'Error loading review details')}</p>
      </div>
    );
  }

  const tabs = [
    { id: 'cve', label: t('hitl.details.cve_tab', 'CVE'), icon: '🔍' },
    { id: 'patch', label: t('hitl.details.patch_tab', 'Patch'), icon: '🔧' },
    { id: 'wargame', label: t('hitl.details.wargame_tab', 'Wargame'), icon: '🎮' },
    { id: 'validation', label: t('hitl.details.validation_tab', 'Validation'), icon: '✅' },
  ];

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <h2 className={styles.title}>{review.apv_code}</h2>
        <span className={`${styles.severityBadge} ${styles[`severity${review.severity}`]}`}>
          {review.severity?.toUpperCase()}
        </span>
      </div>

      {/* Tabs */}
      <div className={styles.tabs} role="tablist" aria-label="Review details">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            id={`${tab.id}-tab`}
            className={`${styles.tab} ${activeTab === tab.id ? styles.tabActive : ''}`}
            onClick={() => setActiveTab(tab.id)}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            onKeyDown={handleTabKeyDown}
          >
            <span aria-hidden="true">{tab.icon}</span> {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className={styles.tabContent} role="tabpanel" id={`panel-${activeTab}`} aria-labelledby={`${activeTab}-tab`} tabIndex={0}>
        {activeTab === 'cve' && <CVETab review={review} />}
        {activeTab === 'patch' && <PatchTab review={review} />}
        {activeTab === 'wargame' && <WargameTab review={review} />}
        {activeTab === 'validation' && <ValidationTab review={review} />}
      </div>
    </div>
  );
};

// CVE Tab
const CVETab = ({ review }) => {
  const { t } = useTranslation();
  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>{t('hitl.details.cve_info', 'CVE Information')}</h3>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.cve_id', 'CVE ID')}:</span>
        <span className={styles.value}>{review.cve_id}</span>
      </div>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.title', 'Title')}:</span>
        <span className={styles.value}>{review.cve_title}</span>
      </div>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.description', 'Description')}:</span>
        <p className={styles.description}>{review.cve_description}</p>
      </div>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.cvss', 'CVSS Score')}:</span>
        <span className={styles.value}>{review.cvss_score}</span>
      </div>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.package', 'Package')}:</span>
        <span className={styles.value}>
          {review.package_name} {review.package_version} → {review.fixed_version}
        </span>
      </div>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.confidence', 'Confirmation')}:</span>
        <div className={styles.confidenceBar}>
          <div className={styles.confidenceFill} style={{ width: `${(review.confirmation_confidence * 100)}%` }} />
          <span className={styles.confidenceValue}>{(review.confirmation_confidence * 100).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
};

// Patch Tab
const PatchTab = ({ review }) => {
  const { t } = useTranslation();
  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>{t('hitl.details.patch_info', 'Patch Information')}</h3>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.strategy', 'Strategy')}:</span>
        <span className={styles.value}>{review.patch_strategy}</span>
      </div>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.patch_desc', 'Description')}:</span>
        <p className={styles.description}>{review.patch_description}</p>
      </div>
      {review.patch_diff && (
        <div className={styles.diff}>
          <pre className={styles.diffContent}>{review.patch_diff}</pre>
        </div>
      )}
      {review.pr_url && (
        <div className={styles.field}>
          <span className={styles.label}>{t('hitl.details.pr', 'Pull Request')}:</span>
          <a href={review.pr_url} target="_blank" rel="noopener noreferrer" className={styles.link}>
            PR #{review.pr_number}
          </a>
        </div>
      )}
    </div>
  );
};

// Wargame Tab
const WargameTab = ({ review }) => {
  const { t } = useTranslation();
  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>{t('hitl.details.wargame_results', 'Wargame Results')}</h3>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.verdict', 'Verdict')}:</span>
        <span className={`${styles.verdict} ${styles[`verdict${review.wargame_verdict}`]}`}>
          {review.wargame_verdict?.toUpperCase()}
        </span>
      </div>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.wargame_confidence', 'Confidence')}:</span>
        <span className={styles.value}>{(review.wargame_confidence * 100).toFixed(1)}%</span>
      </div>
      {review.wargame_run_url && (
        <div className={styles.field}>
          <span className={styles.label}>{t('hitl.details.workflow', 'Workflow')}:</span>
          <a href={review.wargame_run_url} target="_blank" rel="noopener noreferrer" className={styles.link}>
            {t('hitl.details.view_run', 'View GitHub Actions Run')}
          </a>
        </div>
      )}
      {review.wargame_evidence && (
        <div className={styles.evidence}>
          <pre>{JSON.stringify(review.wargame_evidence, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

// Validation Tab
const ValidationTab = ({ review }) => {
  const { t } = useTranslation();
  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>{t('hitl.details.validation_results', 'Validation Results')}</h3>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.status', 'Status')}:</span>
        <span className={`${styles.value} ${review.validation_passed ? styles.success : styles.error}`}>
          {review.validation_passed ? '✅ PASSED' : '❌ FAILED'}
        </span>
      </div>
      <div className={styles.field}>
        <span className={styles.label}>{t('hitl.details.validation_confidence', 'Confidence')}:</span>
        <span className={styles.value}>{(review.validation_confidence * 100).toFixed(1)}%</span>
      </div>
      {review.validation_warnings && review.validation_warnings.length > 0 && (
        <div className={styles.warnings}>
          <h4>{t('hitl.details.warnings', 'Warnings')}:</h4>
          <ul>
            {review.validation_warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

ReviewDetails.propTypes = {
  review: PropTypes.object,
  loading: PropTypes.bool,
  apvSelected: PropTypes.bool,
};

export default ReviewDetails;
