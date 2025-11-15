import React, { useState } from 'react';
import logger from "@/utils/logger";
import PropTypes from 'prop-types';
import { useDecisionSubmit } from '../hooks/useDecisionSubmit';
import styles from './DecisionPanel.module.css';

const DecisionPanel = ({ review, apvSelected, onSuccess }) => {
  const [justification, setJustification] = useState('');
  const [confidence, setConfidence] = useState(0.9);
  const { submit, loading, error, success } = useDecisionSubmit();

  if (!apvSelected) {
    return <div className={styles.empty}><p>Select APV to decide</p></div>;
  }

  const handleDecision = async (decision) => {
    if (!justification || justification.length < 10) {
      alert('Justification required (min 10 chars)');
      return;
    }
    
    try {
      await submit({
        apv_id: review.apv_id,
        decision,
        justification,
        confidence,
        reviewer_name: 'Security Reviewer',
        reviewer_email: 'reviewer@example.com'
      });
      if (onSuccess) onSuccess();
      setJustification('');
    } catch (err) {
      logger.error('Decision failed:', err);
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>DECISION PANEL</h2>
      
      <div className={styles.buttons}>
        <button className={`${styles.btn} ${styles.approve}`} onClick={() => handleDecision('approve')} disabled={loading}>
          ✅ APPROVE
        </button>
        <button className={`${styles.btn} ${styles.reject}`} onClick={() => handleDecision('reject')} disabled={loading}>
          ❌ REJECT
        </button>
        <button className={`${styles.btn} ${styles.modify}`} onClick={() => handleDecision('modify')} disabled={loading}>
          🔧 MODIFY
        </button>
        <button className={`${styles.btn} ${styles.escalate}`} onClick={() => handleDecision('escalate')} disabled={loading}>
          ⬆️ ESCALATE
        </button>
      </div>

      {/* Boris Cherny Standard - GAP #76 FIX: Add maxLength validation */}
      <textarea
        className={styles.textarea}
        placeholder="Justification (min 10 chars)..."
        value={justification}
        onChange={(e) => setJustification(e.target.value)}
        rows={4}
        maxLength={500}
      />

      <div className={styles.slider}>
        <label>Confidence: {(confidence * 100).toFixed(0)}%</label>
        <input
          type="range"
          min="0"
          max="100"
          value={confidence * 100}
          onChange={(e) => setConfidence(e.target.value / 100)}
        />
      </div>

      {error && <div className={styles.error}>Error: {error.message}</div>}
      {success && <div className={styles.success}>✅ Decision submitted!</div>}
    </div>
  );
};

DecisionPanel.propTypes = {
  review: PropTypes.object,
  apvSelected: PropTypes.bool,
  onSuccess: PropTypes.func
};

export default DecisionPanel;
