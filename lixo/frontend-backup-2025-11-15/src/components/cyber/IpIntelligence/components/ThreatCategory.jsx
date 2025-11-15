import React from 'react';
import styles from './IpAnalysisResults.module.css';

/**
 * A memoized component to display a single threat category.
 */
const ThreatCategory = ({ category }) => {
  return (
    <div className={styles.threatCategoryItem}>
      {category.toUpperCase()}
    </div>
  );
};

export default React.memo(ThreatCategory);
