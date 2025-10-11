import React, { forwardRef } from 'react';
import styles from '../TerminalEmulator.module.css';

/**
 * The display area for the xterm.js instance.
 */
const TerminalDisplay = React.memo(forwardRef((props, ref) => {
  return <div ref={ref} className={styles.terminalContainer} />;
}));

TerminalDisplay.displayName = 'TerminalDisplay';

export default TerminalDisplay;
