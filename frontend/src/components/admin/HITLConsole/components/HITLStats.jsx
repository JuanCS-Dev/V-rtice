import React from 'react';
import PropTypes from 'prop-types';
import styles from './HITLStats.module.css';

const HITLStats = ({ stats, loading }) => {
  if (loading || !stats) {
    return <div className={styles.loading}>Loading stats...</div>;
  }

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>HITL STATISTICS</h2>
      
      <div className={styles.grid}>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Pending Reviews</span>
          <span className={styles.statValue}>{stats.pending_reviews}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Total Decisions</span>
          <span className={styles.statValue}>{stats.total_decisions}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Today</span>
          <span className={styles.statValue}>{stats.decisions_today}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>This Week</span>
          <span className={styles.statValue}>{stats.decisions_this_week}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Avg Review Time</span>
          <span className={styles.statValue}>{Math.floor(stats.average_review_time_seconds / 60)}m</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Agreement Rate</span>
          <span className={styles.statValue}>{(stats.human_ai_agreement_rate * 100).toFixed(0)}%</span>
        </div>
      </div>

      <div className={styles.breakdown}>
        <h3 className={styles.breakdownTitle}>Decision Breakdown</h3>
        <div className={styles.breakdownItems}>
          <div className={styles.breakdownItem}>
            <span>✅ Approved:</span>
            <span>{stats.approved_count}</span>
          </div>
          <div className={styles.breakdownItem}>
            <span>❌ Rejected:</span>
            <span>{stats.rejected_count}</span>
          </div>
          <div className={styles.breakdownItem}>
            <span>🔧 Modified:</span>
            <span>{stats.modified_count}</span>
          </div>
          <div className={styles.breakdownItem}>
            <span>⬆️ Escalated:</span>
            <span>{stats.escalated_count}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

HITLStats.propTypes = {
  stats: PropTypes.object,
  loading: PropTypes.bool
};

export default HITLStats;
