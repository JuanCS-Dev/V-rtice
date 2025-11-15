/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MESSAGE INPUT COMPONENT
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Expandable textarea with send button and keyboard shortcuts
 */

import React, { useState, useRef, useEffect } from "react";
import PropTypes from "prop-types";
import styles from "../MaximusChat.module.css";

export const MessageInput = ({ onSendMessage, isDisabled }) => {
  const [message, setMessage] = useState("");
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleSubmit = () => {
    if (message.trim() && !isDisabled) {
      onSendMessage(message.trim());
      setMessage("");

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e) => {
    // Send on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className={styles.inputContainer}>
      <div className={styles.inputWrapper}>
        <div className={styles.inputBox}>
          {/* Boris Cherny Standard - GAP #76 FIX: Add maxLength validation */}
          <textarea
            ref={textareaRef}
            className={styles.textarea}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Pergunte algo ao Maximus... (Enter para enviar, Shift+Enter para nova linha)"
            disabled={isDisabled}
            rows={1}
            maxLength={5000}
          />

          <button
            className={styles.sendButton}
            onClick={handleSubmit}
            disabled={!message.trim() || isDisabled}
            title="Enviar mensagem (Enter)"
          >
            <span>⚡</span>
            Enviar
          </button>
        </div>

        <div className={styles.inputHint}>
          Powered by NLP Engine • vcli-go integration
        </div>
      </div>
    </div>
  );
};

MessageInput.propTypes = {
  onSendMessage: PropTypes.func.isRequired,
  isDisabled: PropTypes.bool,
};

MessageInput.defaultProps = {
  isDisabled: false,
};
