/**
 * ═══════════════════════════════════════════════════════════════════════════
 * useMaximusChat - Chat Logic Hook
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Manages chat state, conversations, and API integration
 * Backend integration preparado para /api/nlp/chat (mock até implementação)
 */

import { useState, useCallback, useEffect } from 'react';
import logger from '@/utils/logger';

const STORAGE_KEY = 'maximus_chat_conversations';

// Mock API response (será substituído por integração real)
const mockAPIResponse = async (userMessage) => {
  // Simula delay de processamento NLP
  await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 1000));
  
  // Mock responses baseadas em keywords
  const lowerMessage = userMessage.toLowerCase();
  
  if (lowerMessage.includes('status') || lowerMessage.includes('sistemas')) {
    return {
      content: `**Status dos Sistemas Principais:**\n\n` +
        `🧠 **Consciousness Core**: Operational (ESGT: 7.2Hz, TIG: Active)\n` +
        `🔬 **Oráculo Engine**: Running (Self-improvement cycles: 42)\n` +
        `🧬 **Adaptive Immunity**: Healthy (Patches validated: 156)\n` +
        `⚔️ **ADW Workflows**: Active (Red: 23, Blue: 18, Purple: 12)\n\n` +
        `Todos os módulos operando dentro dos parâmetros normais.`
    };
  }
  
  if (lowerMessage.includes('alert') || lowerMessage.includes('segurança')) {
    return {
      content: `**Últimos Alerts de Segurança:**\n\n` +
        `🔴 **CRITICAL** - Tentativa de SQL Injection bloqueada (10min atrás)\n` +
        `🟠 **HIGH** - Port scan detectado em subnet 192.168.1.0/24 (1h atrás)\n` +
        `🟡 **MEDIUM** - Certificado SSL próximo da expiração (3d restantes)\n\n` +
        `Ações recomendadas: Revisar logs do WAF e atualizar certificado.`
    };
  }
  
  if (lowerMessage.includes('imunidade') || lowerMessage.includes('immunity')) {
    return {
      content: `**Sistema de Imunidade Adaptativa:**\n\n` +
        `O sistema funciona em 3 fases:\n\n` +
        `1. **Oráculo** → Gera patches ML-driven\n` +
        `2. **Eureka** → Valida eficácia em sandbox\n` +
        `3. **Crisol** → Deploy gradual com rollback automático\n\n` +
        `Similar ao sistema imunológico humano: aprende com ataques e se adapta.`
    };
  }
  
  // Resposta genérica
  return {
    content: `Entendi sua pergunta sobre "${userMessage}".\n\n` +
      `Como sistema de IA do Maximus, posso ajudá-lo com:\n` +
      `• Status de sistemas e módulos\n` +
      `• Análise de segurança e alerts\n` +
      `• Workflows ofensivos/defensivos\n` +
      `• Relatórios e insights\n\n` +
      `Reformule sua pergunta ou selecione um dos prompts sugeridos.`
  };
};

export const useMaximusChat = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isThinking, setIsThinking] = useState(false);

  // Load conversations from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setConversations(parsed);
        
        // Auto-select most recent conversation
        if (parsed.length > 0) {
          const mostRecent = parsed.reduce((prev, current) => 
            current.lastActivity > prev.lastActivity ? current : prev
          );
          setActiveConversationId(mostRecent.id);
          setMessages(mostRecent.messages || []);
        }
      }
    } catch (error) {
      logger.error('[useMaximusChat] Failed to load conversations:', error);
    }
  }, []);

  // Save conversations to localStorage
  const saveConversations = useCallback((updatedConversations) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedConversations));
      setConversations(updatedConversations);
    } catch (error) {
      logger.error('[useMaximusChat] Failed to save conversations:', error);
    }
  }, []);

  // Create new conversation
  const createNewConversation = useCallback(() => {
    const newConv = {
      id: `conv_${Date.now()}`,
      title: 'Nova conversa',
      messages: [],
      messageCount: 0,
      lastActivity: Date.now()
    };
    
    const updated = [newConv, ...conversations];
    saveConversations(updated);
    setActiveConversationId(newConv.id);
    setMessages([]);
    
    logger.info('[useMaximusChat] New conversation created:', newConv.id);
  }, [conversations, saveConversations]);

  // Send message
  const sendMessage = useCallback(async (content) => {
    if (!activeConversationId) {
      createNewConversation();
      return;
    }

    // Add user message
    const userMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content,
      timestamp: Date.now()
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setIsThinking(true);

    try {
      // Call API (mock for now)
      const response = await mockAPIResponse(content);
      
      // Add assistant message
      const assistantMessage = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: response.content,
        timestamp: Date.now()
      };

      const finalMessages = [...updatedMessages, assistantMessage];
      setMessages(finalMessages);

      // Update conversation
      const updatedConversations = conversations.map(conv => {
        if (conv.id === activeConversationId) {
          return {
            ...conv,
            messages: finalMessages,
            messageCount: finalMessages.length,
            lastActivity: Date.now(),
            title: conv.title === 'Nova conversa' 
              ? content.slice(0, 50) + (content.length > 50 ? '...' : '')
              : conv.title
          };
        }
        return conv;
      });

      saveConversations(updatedConversations);
      
      logger.info('[useMaximusChat] Message sent successfully');
    } catch (error) {
      logger.error('[useMaximusChat] Failed to send message:', error);
      
      // Add error message
      const errorMessage = {
        id: `msg_${Date.now()}_error`,
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
        timestamp: Date.now(),
        isError: true
      };
      
      setMessages([...updatedMessages, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  }, [activeConversationId, messages, conversations, saveConversations, createNewConversation]);

  // Select conversation
  const selectConversation = useCallback((conversationId) => {
    const conv = conversations.find(c => c.id === conversationId);
    if (conv) {
      setActiveConversationId(conversationId);
      setMessages(conv.messages || []);
      logger.info('[useMaximusChat] Conversation selected:', conversationId);
    }
  }, [conversations]);

  return {
    conversations,
    activeConversationId,
    messages,
    isThinking,
    sendMessage,
    createNewConversation,
    selectConversation
  };
};
