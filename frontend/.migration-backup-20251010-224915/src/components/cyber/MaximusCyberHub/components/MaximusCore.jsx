/**
 * MaximusCore.jsx - AI Chat & Tool Execution Interface
 * ====================================================
 *
 * Widget principal para interação direta com Maximus AI Core.
 *
 * Features:
 * - Chat AI com streaming em tempo real
 * - Visualização de tool execution
 * - Display de reasoning chain-of-thought
 * - Painel de contexto e memória
 * - Sugestões inteligentes
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  chatWithMaximus,
  getAIMemory,
  getAISuggestions,
  getToolCatalog,
  callTool,
  getMaximusHealth
} from '../../../../api/maximusAI';
import styles from './MaximusCore.module.css';

export const MaximusCore = () => {
  // Chat state
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');

  // AI state
  const [aiStatus, setAiStatus] = useState({ status: 'checking', tools_count: 0 });
  const [toolCatalog, setToolCatalog] = useState(null);
  const [activeTools, setActiveTools] = useState([]);
  const [aiMemory, setAiMemory] = useState([]);
  const [suggestions, setSuggestions] = useState([]);

  // UI state
  const [showMemory, setShowMemory] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const chatEndRef = useRef(null);

  // Initialize
  useEffect(() => {
    loadAIStatus();
    loadToolCatalog();
    loadMemory();
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentStreamingMessage]);

  // Load AI health status
  const loadAIStatus = async () => {
    const health = await getMaximusHealth();
    if (health.success !== false) {
      setAiStatus({
        status: health.status || 'online',
        tools_count: health.total_integrated_tools || 0,
        model: health.ai_model || 'Claude Opus'
      });
    } else {
      setAiStatus({ status: 'offline', tools_count: 0 });
    }
  };

  // Load tool catalog
  const loadToolCatalog = async () => {
    const catalog = await getToolCatalog();
    if (catalog.success !== false) {
      setToolCatalog(catalog);
    }
  };

  // Load AI memory
  const loadMemory = async () => {
    const memory = await getAIMemory();
    if (memory.success !== false && memory.memories) {
      setAiMemory(memory.memories.slice(0, 5)); // Last 5 memories
    }
  };

  // Load suggestions based on context
  const loadSuggestions = async (context) => {
    const sugg = await getAISuggestions(context, 'next_action');
    if (sugg.success !== false && sugg.suggestions) {
      setSuggestions(sugg.suggestions.slice(0, 3)); // Top 3 suggestions
    }
  };

  // Handle send message
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isStreaming) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsStreaming(true);
    setCurrentStreamingMessage('');

    try {
      // Chat with streaming
      const response = await chatWithMaximus(
        inputMessage,
        {
          mode: 'deep_analysis',
          context: messages.slice(-5) // Last 5 messages for context
        },
        (chunk, fullResponse) => {
          setCurrentStreamingMessage(fullResponse);
        }
      );

      if (response.success) {
        const aiMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response.response || currentStreamingMessage,
          timestamp: new Date().toISOString(),
          tools_used: response.tools_used || [],
          reasoning: response.reasoning || null
        };

        setMessages(prev => [...prev, aiMessage]);

        // Track active tools
        if (response.tools_used && response.tools_used.length > 0) {
          setActiveTools(prev => [...new Set([...prev, ...response.tools_used])]);
        }

        // Load suggestions for next action
        loadSuggestions({ last_message: inputMessage, ai_response: response });
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'system',
        content: `Error: ${error.message}`,
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsStreaming(false);
      setCurrentStreamingMessage('');
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion.action || suggestion.text);
  };

  // Handle quick tool call
  const handleQuickToolCall = async (toolName, params = {}) => {
    setActiveTools(prev => [...new Set([...prev, toolName])]);

    const result = await callTool(toolName, params);

    if (result.success) {
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: 'tool',
        tool_name: toolName,
        content: JSON.stringify(result.result, null, 2),
        timestamp: new Date().toISOString()
      }]);
    }
  };

  // Render message
  const renderMessage = (msg) => {
    const isUser = msg.role === 'user';
    const isSystem = msg.role === 'system';
    const isTool = msg.role === 'tool';

    return (
      <div
        key={msg.id}
        className={`${styles.message} ${isUser ? styles.userMessage : ''} ${isSystem ? styles.systemMessage : ''} ${isTool ? styles.toolMessage : ''}`}
      >
        <div className={styles.messageHeader}>
          <span className={styles.messageRole}>
            {isUser ? '👤 You' : isTool ? `🔧 ${msg.tool_name}` : '🤖 Maximus AI'}
          </span>
          <span className={styles.messageTime}>
            {new Date(msg.timestamp).toLocaleTimeString()}
          </span>
        </div>

        <div className={styles.messageContent}>
          {isTool ? (
            <pre className={styles.toolOutput}>{msg.content}</pre>
          ) : (
            <p>{msg.content}</p>
          )}
        </div>

        {msg.tools_used && msg.tools_used.length > 0 && (
          <div className={styles.toolsUsed}>
            <span className={styles.toolsLabel}>Tools used:</span>
            {msg.tools_used.map((tool, idx) => (
              <span key={idx} className={styles.toolBadge}>{tool}</span>
            ))}
          </div>
        )}

        {msg.reasoning && (
          <details className={styles.reasoning}>
            <summary>💭 Reasoning</summary>
            <pre>{JSON.stringify(msg.reasoning, null, 2)}</pre>
          </details>
        )}
      </div>
    );
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h2 className={styles.title}>🤖 Maximus AI Core</h2>
          <span className={`${styles.status} ${styles[aiStatus.status]}`}>
            {aiStatus.status === 'online' ? '🟢' : '🔴'} {aiStatus.status}
          </span>
        </div>

        <div className={styles.headerRight}>
          <button
            className={styles.iconButton}
            onClick={() => setShowTools(!showTools)}
            title="Tools"
          >
            🔧 {toolCatalog?.total_tools || 0}
          </button>
          <button
            className={styles.iconButton}
            onClick={() => setShowMemory(!showMemory)}
            title="Memory"
          >
            🧠 Memory
          </button>
          <button
            className={styles.iconButton}
            onClick={loadAIStatus}
            title="Refresh"
          >
            🔄
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className={styles.content}>
        {/* Sidebar - Tools or Memory */}
        {(showTools || showMemory) && (
          <div className={styles.sidebar}>
            {showTools && toolCatalog && (
              <div className={styles.toolsPanel}>
                <h3>🔧 Available Tools ({toolCatalog.total_tools})</h3>

                {toolCatalog.offensive_arsenal && (
                  <div className={styles.toolCategory}>
                    <h4>Offensive Arsenal ({toolCatalog.offensive_arsenal.count})</h4>
                    <div className={styles.toolList}>
                      {toolCatalog.offensive_arsenal.tools.map(tool => (
                        <button
                          key={tool}
                          className={styles.toolItem}
                          onClick={() => handleQuickToolCall(tool)}
                        >
                          {tool}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {toolCatalog.world_class_tools && (
                  <div className={styles.toolCategory}>
                    <h4>World-Class Tools ({toolCatalog.world_class_tools.count})</h4>
                    <div className={styles.toolList}>
                      {toolCatalog.world_class_tools.tools.slice(0, 8).map(tool => (
                        <button
                          key={tool}
                          className={styles.toolItem}
                        >
                          {tool}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {showMemory && (
              <div className={styles.memoryPanel}>
                <h3>🧠 AI Memory</h3>
                <div className={styles.memoryList}>
                  {aiMemory.length > 0 ? (
                    aiMemory.map((mem, idx) => (
                      <div key={idx} className={styles.memoryItem}>
                        <span className={styles.memoryType}>{mem.type}</span>
                        <p className={styles.memoryContent}>{mem.content}</p>
                      </div>
                    ))
                  ) : (
                    <p className={styles.emptyState}>No memories yet</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Chat Area */}
        <div className={styles.chatArea}>
          {/* Messages */}
          <div className={styles.messages}>
            {messages.length === 0 ? (
              <div className={styles.welcomeMessage}>
                <h3>👋 Welcome to Maximus AI Core</h3>
                <p>I'm your AI orchestrator with access to {aiStatus.tools_count}+ tools.</p>
                <p>Ask me to analyze threats, run scans, investigate targets, or orchestrate complex workflows.</p>

                <div className={styles.quickActions}>
                  <button onClick={() => setInputMessage('Show me a full security assessment workflow')}>
                    📊 Full Assessment
                  </button>
                  <button onClick={() => setInputMessage('Run an OSINT investigation on')}>
                    🔍 OSINT Investigation
                  </button>
                  <button onClick={() => setInputMessage('Analyze network 192.168.1.0/24')}>
                    🌐 Network Analysis
                  </button>
                </div>
              </div>
            ) : (
              <>
                {messages.map(renderMessage)}

                {isStreaming && currentStreamingMessage && (
                  <div className={`${styles.message} ${styles.streaming}`}>
                    <div className={styles.messageHeader}>
                      <span className={styles.messageRole}>🤖 Maximus AI</span>
                      <span className={styles.streamingIndicator}>● Thinking...</span>
                    </div>
                    <div className={styles.messageContent}>
                      <p>{currentStreamingMessage}</p>
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className={styles.suggestions}>
              <span className={styles.suggestionsLabel}>💡 Suggestions:</span>
              {suggestions.map((sugg, idx) => (
                <button
                  key={idx}
                  className={styles.suggestionChip}
                  onClick={() => handleSuggestionClick(sugg)}
                >
                  {sugg.text || sugg.action}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className={styles.inputArea}>
            <input
              type="text"
              className={styles.input}
              placeholder="Ask Maximus AI anything..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              disabled={isStreaming}
            />
            <button
              className={styles.sendButton}
              onClick={handleSendMessage}
              disabled={isStreaming || !inputMessage.trim()}
            >
              {isStreaming ? '⏳' : '📤'} Send
            </button>
          </div>
        </div>
      </div>

      {/* Active Tools Indicator */}
      {activeTools.length > 0 && (
        <div className={styles.activeToolsBar}>
          <span>🔧 Active: </span>
          {activeTools.map((tool, idx) => (
            <span key={idx} className={styles.activeToolBadge}>{tool}</span>
          ))}
        </div>
      )}
    </div>
  );
};

export default MaximusCore;
