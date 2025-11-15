/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MESSAGE BUBBLE COMPONENT
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Individual chat message display with markdown support
 */

import React from "react";
import PropTypes from "prop-types";
import logger from "@/utils/logger";
import styles from "./MessageBubble.module.css";
import { formatTime } from "@/utils/dateHelpers";

export const MessageBubble = ({ message, isUser }) => {
  const formatTimestamp = (timestamp) => {
    return formatTime(timestamp, "--:--");
  };

  const renderMarkdown = (text) => {
    // Simple markdown rendering (can be enhanced with a library like react-markdown)
    let formatted = text;

    // Bold: **text**
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

    // Italic: *text*
    formatted = formatted.replace(/\*(.+?)\*/g, "<em>$1</em>");

    // Inline code: `code`
    formatted = formatted.replace(/`(.+?)`/g, "<code>$1</code>");

    // Line breaks
    formatted = formatted.replace(/\n/g, "<br />");

    return { __html: formatted };
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
  };

  // Boris Cherny Standard - GAP #83: Replace console.log with logger
  const handleRegenerate = () => {
    // Regenerate functionality will be enabled when backend is ready
    logger.debug("[MaximusChat] Regenerate requested for message:", message.id);
  };

  return (
    <div
      className={`${styles.messageBubble} ${isUser ? styles.user : styles.assistant}`}
    >
      <div
        className={`${styles.avatar} ${isUser ? styles.user : styles.assistant}`}
      >
        {isUser ? "👤" : "🧠"}
      </div>

      <div className={styles.messageContent}>
        <div className={styles.messageHeader}>
          <span className={styles.senderName}>
            {isUser ? "Você" : "Maximus"}
          </span>
          <span className={styles.timestamp}>
            {formatTimestamp(message.timestamp)}
          </span>
        </div>

        <div
          className={styles.messageText}
          dangerouslySetInnerHTML={renderMarkdown(message.content)}
        />

        {!isUser && (
          <div className={styles.messageActions}>
            <button
              className={styles.actionButton}
              onClick={handleCopy}
              type="button"
              aria-label="Copiar mensagem"
            >
              📋
            </button>
            <button
              className={styles.actionButton}
              onClick={handleRegenerate}
              type="button"
              aria-label="Regenerar resposta"
            >
              🔄
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

MessageBubble.propTypes = {
  message: PropTypes.shape({
    id: PropTypes.string.isRequired,
    content: PropTypes.string.isRequired,
    timestamp: PropTypes.number.isRequired,
    role: PropTypes.oneOf(["user", "assistant"]).isRequired,
  }).isRequired,
  isUser: PropTypes.bool.isRequired,
};
