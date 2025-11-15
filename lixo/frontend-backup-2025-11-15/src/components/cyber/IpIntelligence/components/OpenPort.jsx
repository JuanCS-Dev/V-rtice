import React from 'react';
import styles from './IpAnalysisResults.module.css';

/**
 * A memoized component to display a single open port.
 */
const OpenPort = ({ port }) => {
  return (
    <span className={styles.portPill}>
      {port}
    </span>
  );
};

export default React.memo(OpenPort);
