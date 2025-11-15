/**
 * ═══════════════════════════════════════════════════════════════════════════
 * CONVERSATION SIDEBAR COMPONENT
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Displays conversation history with vertical scroll
 */

import React from 'react';
import PropTypes from 'prop-types';
import styles from '../MaximusChat.module.css';

export const ConversationSidebar = ({ 
  conversations, 
  activeConversationId, 
  onSelectConversation,
  onNewConversation 
}) => {
  const formatRelativeTime = (timestamp) => {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'Agora';
    if (minutes < 60) return `${minutes}m atrás`;
    if (hours < 24) return `${hours}h atrás`;
    return `${days}d atrás`;
  };

  return (
    <div className={styles.sidebar}>
      <div className={styles.sidebarHeader}>
        <button 
          className={styles.newChatButton}
          onClick={onNewConversation}
        >
          <span>➕</span>
          Nova Conversa
        </button>
      </div>
      
      <div className={styles.conversationList}>
        {conversations.length === 0 ? (
          <div style={{ 
            padding: '2rem 1rem', 
            textAlign: 'center', 
            color: '#64748b',
            fontSize: '0.875rem'
          }}>
            Nenhuma conversa ainda
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`${styles.conversationItem} ${
                conv.id === activeConversationId ? styles.active : ''
              }`}
              onClick={() => onSelectConversation(conv.id)}
              onKeyPress={(e) => e.key === 'Enter' && onSelectConversation(conv.id)}
              role="button"
              tabIndex={0}
            >
              <div className={styles.conversationTitle}>
                {conv.title || 'Nova conversa'}
              </div>
              <div className={styles.conversationMeta}>
                <span>{conv.messageCount || 0} mensagens</span>
                <span>•</span>
                <span>{formatRelativeTime(conv.lastActivity)}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

ConversationSidebar.propTypes = {
  conversations: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string,
      messageCount: PropTypes.number,
      lastActivity: PropTypes.number.isRequired
    })
  ).isRequired,
  activeConversationId: PropTypes.string,
  onSelectConversation: PropTypes.func.isRequired,
  onNewConversation: PropTypes.func.isRequired
};
