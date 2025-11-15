/**
 * ═══════════════════════════════════════════════════════════════════════════
 * CHAT WINDOW COMPONENT
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Main chat display area with messages and thinking indicator
 */

import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { MessageBubble } from './MessageBubble';
import { ThinkingIndicator } from './ThinkingIndicator';
import styles from '../MaximusChat.module.css';

export const ChatWindow = ({ messages, isThinking, onPromptSelect }) => {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const suggestedPrompts = [
    {
      id: '1',
      text: 'Qual o status dos sistemas de consciência artificial?'
    },
    {
      id: '2',
      text: 'Analise os últimos alerts de segurança detectados'
    },
    {
      id: '3',
      text: 'Explique o funcionamento do sistema de imunidade adaptativa'
    },
    {
      id: '4',
      text: 'Gere um relatório de atividades ofensivas recentes'
    }
  ];

  return (
    <div className={styles.messagesContainer}>
      {messages.length === 0 && !isThinking ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyStateIcon}>🧠⚡</div>
          <div className={styles.emptyStateTitle}>
            Chat com Maximus AI
          </div>
          <div className={styles.emptyStateText}>
            Sistema de processamento de linguagem natural integrado com os módulos de consciência,
            análise de segurança e workflows de AI-driven operations. Pergunte o que quiser sobre
            o estado do sistema, solicite análises ou execute comandos complexos.
          </div>
          
          <div className={styles.suggestedPrompts}>
            {suggestedPrompts.map((prompt) => (
              <div
                key={prompt.id}
                className={styles.promptCard}
                onClick={() => onPromptSelect(prompt.text)}
                onKeyPress={(e) => e.key === 'Enter' && onPromptSelect(prompt.text)}
                role="button"
                tabIndex={0}
              >
                <div className={styles.promptText}>{prompt.text}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              isUser={message.role === 'user'}
            />
          ))}
          
          {isThinking && <ThinkingIndicator />}
          
          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  );
};

ChatWindow.propTypes = {
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      content: PropTypes.string.isRequired,
      role: PropTypes.oneOf(['user', 'assistant']).isRequired,
      timestamp: PropTypes.number.isRequired
    })
  ).isRequired,
  isThinking: PropTypes.bool,
  onPromptSelect: PropTypes.func.isRequired
};

ChatWindow.defaultProps = {
  isThinking: false
};
