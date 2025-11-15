/**
 * ═══════════════════════════════════════════════════════════════════════════
 * THINKING INDICATOR COMPONENT
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Animated indicator shown when Maximus is processing a response
 */

import React from "react";
import styles from "./ThinkingIndicator.module.css";

export const ThinkingIndicator = () => {
  return (
    <div className={styles.thinkingContainer}>
      <div className={styles.avatar}>🧠</div>

      <div className={styles.thinkingBubble}>
        <div className={styles.thinkingText}>Maximus está pensando...</div>

        <div className={styles.dotsContainer}>
          <div className={styles.dot} />
          <div className={styles.dot} />
          <div className={styles.dot} />
        </div>

        <div className={styles.brainActivity}>
          <span className={styles.activityLabel}>🧠 Processando NLP</span>
          <div className={styles.activityBar}>
            <div className={styles.activityProgress} />
          </div>
        </div>
      </div>
    </div>
  );
};
