/**
 * StoryCard - Card de Narrativa Estilo Medium
 * ============================================
 *
 * Card editorial elegante para exibir narrativas geradas pelo MVP.
 */

import React, { useState } from "react";
import styles from "./StoryCard.module.css";

export const StoryCard = ({ narrative }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getToneColor = (tone) => {
    switch (tone) {
      case "analytical":
        return "blue";
      case "poetic":
        return "pink";
      case "technical":
        return "gray";
      default:
        return "purple";
    }
  };

  const getToneIcon = (tone) => {
    switch (tone) {
      case "analytical":
        return "🔬";
      case "poetic":
        return "🎭";
      case "technical":
        return "⚙️";
      default:
        return "📝";
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}min atrás`;
    if (diffHours < 24) return `${diffHours}h atrás`;
    if (diffDays < 7) return `${diffDays}d atrás`;

    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  const toneColor = getToneColor(narrative.tone);
  const toneIcon = getToneIcon(narrative.tone);
  const contentPreview = narrative.content?.substring(0, 280);
  const needsExpand = narrative.content?.length > 280;

  return (
    <article className={`${styles.card} ${styles[toneColor]}`}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.metadata}>
          <span className={`${styles.tone} ${styles[toneColor]}`}>
            <span className={styles.toneIcon}>{toneIcon}</span>
            <span className={styles.toneName}>{narrative.tone}</span>
          </span>
          <span className={styles.timestamp}>
            {formatTimestamp(narrative.created_at)}
          </span>
        </div>

        {narrative.nqs && (
          <div className={styles.nqsBadge}>
            <span className={styles.nqsLabel}>NQS</span>
            <span className={styles.nqsValue}>
              {(narrative.nqs * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </header>

      {/* Content */}
      <div className={styles.body}>
        <p className={styles.content}>
          {isExpanded ? narrative.content : contentPreview}
          {!isExpanded && needsExpand && "..."}
        </p>

        {needsExpand && (
          <button
            className={styles.expandButton}
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? "← Recolher" : "Ler mais →"}
          </button>
        )}
      </div>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.metrics}>
          <div className={styles.metric}>
            <span className={styles.metricIcon}>📏</span>
            <span className={styles.metricValue}>
              {narrative.content?.length || 0} caracteres
            </span>
          </div>

          {narrative.word_count && (
            <div className={styles.metric}>
              <span className={styles.metricIcon}>📝</span>
              <span className={styles.metricValue}>
                {narrative.word_count} palavras
              </span>
            </div>
          )}

          {narrative.reading_time && (
            <div className={styles.metric}>
              <span className={styles.metricIcon}>⏱️</span>
              <span className={styles.metricValue}>
                {narrative.reading_time} min
              </span>
            </div>
          )}
        </div>

        {narrative.narrative_id && (
          <div className={styles.id}>
            <span className={styles.idLabel}>ID:</span>
            <code className={styles.idValue}>{narrative.narrative_id}</code>
          </div>
        )}
      </footer>
    </article>
  );
};

export default StoryCard;
