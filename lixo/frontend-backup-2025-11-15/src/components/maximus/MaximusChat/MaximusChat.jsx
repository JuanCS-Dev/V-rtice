/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MAXIMUS CHAT - NLP Interface for Maximus AI
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Chat interface estilo Claude com integração NLP
 * Substitui o antigo MaximusTerminal.jsx
 *
 * Features:
 * - Conversas persistentes (localStorage)
 * - Sidebar com histórico vertical
 * - Input expansível com markdown
 * - Thinking indicator animado
 * - Mock API (preparado para backend real)
 *
 * Design: Cyberpunk + Maximus theme (red/orange/green)
 */

import React from 'react';
import { ConversationSidebar } from './components/ConversationSidebar';
import { ChatWindow } from './components/ChatWindow';
import { MessageInput } from './components/MessageInput';
import { useMaximusChat } from './hooks/useMaximusChat';
import styles from './MaximusChat.module.css';

const MaximusChat = () => {
  const {
    conversations,
    activeConversationId,
    messages,
    isThinking,
    sendMessage,
    createNewConversation,
    selectConversation
  } = useMaximusChat();

  const handlePromptSelect = (promptText) => {
    sendMessage(promptText);
  };

  return (
    <div className={styles.chatContainer}>
      {/* Sidebar com histórico de conversas */}
      <ConversationSidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={selectConversation}
        onNewConversation={createNewConversation}
      />

      {/* Área principal do chat */}
      <div className={styles.chatMain}>
        {/* Header */}
        <div className={styles.chatHeader}>
          <div className={styles.chatTitle}>
            <div className={styles.statusDot} />
            <span className={styles.chatTitleText}>
              ⚡ MAXIMUS NLP INTERFACE
            </span>
          </div>
          <span className={styles.chatVersion}>v2.0 • vcli-go</span>
        </div>

        {/* Messages area */}
        <ChatWindow
          messages={messages}
          isThinking={isThinking}
          onPromptSelect={handlePromptSelect}
        />

        {/* Input area */}
        <MessageInput
          onSendMessage={sendMessage}
          isDisabled={isThinking}
        />
      </div>
    </div>
  );
};

export default MaximusChat;
