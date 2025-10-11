/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MAXIMUS CORE - AI Chat & Orchestration Interface
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Painel principal de interação com Maximus AI Core.
 * Features:
 * - Chat AI com streaming em tempo real
 * - Visualização de tool execution (45+ ferramentas)
 * - Display de reasoning chain-of-thought
 * - Painel de contexto e memória
 * - Sugestões inteligentes baseadas em contexto
 *
 * Port: 8001 (maximus_core_service)
 * Regra: NO MOCK, NO PLACEHOLDER - Dados REAIS via API
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  chatWithMaximus,
  getAIMemory,
  getAISuggestions,
  getToolCatalog,
  callTool,
  getMaximusHealth
} from '../../api/maximusAI';
import { escapeHTML } from '../../utils/security';
import './MaximusCore.css';

export const MaximusCore = ({ aiStatus, setAiStatus }) => {
  // ═══════════════════════════════════════════════════════════════════════
  // STATE - Chat & Messages
  // ═══════════════════════════════════════════════════════════════════════
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState('');

  // ═══════════════════════════════════════════════════════════════════════
  // STATE - AI Intelligence
  // ═══════════════════════════════════════════════════════════════════════
  const [toolCatalog, setToolCatalog] = useState(null);
  const [activeTools, setActiveTools] = useState([]);
  const [aiMemory, setAiMemory] = useState([]);
  const [suggestions, setSuggestions] = useState([]);

  // ═══════════════════════════════════════════════════════════════════════
  // STATE - UI Controls
  // ═══════════════════════════════════════════════════════════════════════
  const [showMemory, setShowMemory] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const chatEndRef = useRef(null);

  // ═══════════════════════════════════════════════════════════════════════
  // INITIALIZATION
  // ═══════════════════════════════════════════════════════════════════════
  useEffect(() => {
    loadMaximusHealth();
    loadToolCatalog();
    loadMemory();

    // Welcome message
    setMessages([{
      id: Date.now(),
      role: 'assistant',
      content: '🤖 **Maximus AI Core Online**\n\nI have access to 45+ tools across offensive security, OSINT, cyber intelligence, and cognitive services. Ask me to:\n\n• Run security assessments\n• Investigate targets (OSINT)\n• Analyze threats\n• Execute MITRE ATT&CK simulations\n• Orchestrate multi-service workflows\n\nWhat would you like me to do?',
      timestamp: new Date().toISOString()
    }]);
  }, [loadMaximusHealth]);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentStreamingMessage]);

  // ═══════════════════════════════════════════════════════════════════════
  // DATA LOADING
  // ═══════════════════════════════════════════════════════════════════════

  const loadMaximusHealth = useCallback(async () => {
    const health = await getMaximusHealth();
    if (health.success !== false) {
      setAiStatus(prev => ({
        ...prev,
        core: {
          status: health.status === 'healthy' ? 'online' : 'degraded',
          uptime: health.uptime || '0h',
          reasoning: 'ready',
          tools_count: health.total_integrated_tools || 0
        }
      }));
    }
  }, [setAiStatus]);

  const loadToolCatalog = async () => {
    const catalog = await getToolCatalog();
    if (catalog.success !== false) {
      setToolCatalog(catalog);
    }
  };

  const loadMemory = async () => {
    const memory = await getAIMemory();
    if (memory.success !== false && memory.memories) {
      setAiMemory(memory.memories.slice(0, 10));
    }
  };

  const loadSuggestions = async (context) => {
    const sugg = await getAISuggestions(context, 'next_action');
    if (sugg.success !== false && sugg.suggestions) {
      setSuggestions(sugg.suggestions.slice(0, 3));
    }
  };

  // ═══════════════════════════════════════════════════════════════════════
  // CHAT HANDLERS
  // ═══════════════════════════════════════════════════════════════════════

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
      const response = await chatWithMaximus(
        inputMessage,
        {
          mode: 'deep_analysis',
          context: messages.slice(-5)
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

        if (response.tools_used && response.tools_used.length > 0) {
          setActiveTools(prev => [...new Set([...prev, ...response.tools_used])]);
        }

        loadSuggestions({ last_message: inputMessage, ai_response: response });
      } else {
        throw new Error(response.error || 'Chat failed');
      }
    } catch (error) {
      logger.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'system',
        content: `⚠️ Error: ${error.message}`,
        timestamp: new Date().toISOString(),
        isError: true
      }]);
    } finally {
      setIsStreaming(false);
      setCurrentStreamingMessage('');
    }
  };

  // ═══════════════════════════════════════════════════════════════════════
  // TOOL EXECUTION
  // ═══════════════════════════════════════════════════════════════════════

  const handleQuickToolCall = async (toolName, params = {}) => {
    setActiveTools(prev => [...new Set([...prev, toolName])]);

    const systemMsg = {
      id: Date.now(),
      role: 'system',
      content: `🔧 Executing tool: **${toolName}**...`,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, systemMsg]);

    const result = await callTool(toolName, params);

    if (result.success) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'tool',
        tool_name: toolName,
        content: JSON.stringify(result.result, null, 2),
        timestamp: new Date().toISOString(),
        category: result.category
      }]);
    } else {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'system',
        content: `⚠️ Tool execution failed: ${result.error}`,
        timestamp: new Date().toISOString(),
        isError: true
      }]);
    }
  };

  // ═══════════════════════════════════════════════════════════════════════
  // QUICK ACTIONS
  // ═══════════════════════════════════════════════════════════════════════

  const quickActions = [
    {
      icon: '🌐',
      label: 'Network Recon',
      action: 'Run a network reconnaissance on 192.168.1.0/24'
    },
    {
      icon: '🔍',
      label: 'OSINT Investigation',
      action: 'Perform an OSINT investigation on email: target@example.com'
    },
    {
      icon: '🎯',
      label: 'Threat Intel',
      action: 'Analyze this IP for threat intelligence: 8.8.8.8'
    },
    {
      icon: '🔬',
      label: 'Malware Analysis',
      action: 'Analyze this file hash for malware: d41d8cd98f00b204e9800998ecf8427e'
    },
    {
      icon: '⚔️',
      label: 'Purple Team',
      action: 'Run a purple team exercise for technique T1059.001'
    },
    {
      icon: '🌍',
      label: 'Domain Analysis',
      action: 'Analyze domain: example.com'
    }
  ];

  // ═══════════════════════════════════════════════════════════════════════
  // RENDER HELPERS
  // ═══════════════════════════════════════════════════════════════════════

  const renderMessage = (msg) => {
    const isUser = msg.role === 'user';
    const isSystem = msg.role === 'system';
    const isTool = msg.role === 'tool';

    return (
      <div
        key={msg.id}
        className={`chat-message ${isUser ? 'message-user' : ''} ${isSystem ? 'message-system' : ''} ${isTool ? 'message-tool' : ''} ${msg.isError ? 'message-error' : ''}`}
      >
        <div className="message-header">
          <span className="message-role">
            {isUser ? '👤 YOU' : isTool ? `🔧 ${msg.tool_name}` : isSystem ? '⚙️ SYSTEM' : '🤖 MAXIMUS AI'}
          </span>
          <span className="message-time">
            {new Date(msg.timestamp).toLocaleTimeString('pt-BR')}
          </span>
        </div>

        <div className="message-content">
          {isTool ? (
            <pre className="tool-output">{msg.content}</pre>
          ) : (
            <div className="message-text" dangerouslySetInnerHTML={{
              __html: escapeHTML(msg.content)
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br/>')
            }} />
          )}
        </div>

        {msg.tools_used && msg.tools_used.length > 0 && (
          <div className="tools-used">
            <span className="tools-label">🔧 Tools used:</span>
            {msg.tools_used.map((tool, idx) => (
              <span key={idx} className="tool-badge">{tool}</span>
            ))}
          </div>
        )}

        {msg.reasoning && (
          <details className="reasoning-details">
            <summary>💭 View reasoning process</summary>
            <pre className="reasoning-content">{JSON.stringify(msg.reasoning, null, 2)}</pre>
          </details>
        )}
      </div>
    );
  };

  const getToolsByCategory = () => {
    if (!toolCatalog) return [];

    const categories = {
      offensive: toolCatalog.offensive_arsenal?.tools || [],
      osint: toolCatalog.all_services?.categories?.osint || [],
      cyber: toolCatalog.all_services?.categories?.cyber || [],
      asa: toolCatalog.all_services?.categories?.asa || [],
      world_class: toolCatalog.world_class_tools?.tools || []
    };

    if (selectedCategory === 'all') {
      return Object.entries(categories).flatMap(([cat, tools]) =>
        tools.map(tool => ({ name: tool, category: cat }))
      );
    }

    return (categories[selectedCategory] || []).map(tool => ({ name: tool, category: selectedCategory }));
  };

  // ═══════════════════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════════════════

  return (
    <div className="maximus-core-panel">
      {/* ═════════════════════════════════════════════════════════════════ */}
      {/* HEADER BAR */}
      {/* ═════════════════════════════════════════════════════════════════ */}
      <div className="core-header">
        <div className="header-left">
          <h2 className="core-title">🤖 MAXIMUS AI CORE</h2>
          <span className="core-subtitle">
            {toolCatalog ? `${toolCatalog.total_tools} tools integrated` : 'Loading...'}
          </span>
        </div>

        <div className="header-actions">
          <button
            className={`action-btn ${showTools ? 'active' : ''}`}
            onClick={() => { setShowTools(!showTools); setShowMemory(false); }}
          >
            🔧 Tools ({toolCatalog?.total_tools || 0})
          </button>
          <button
            className={`action-btn ${showMemory ? 'active' : ''}`}
            onClick={() => { setShowMemory(!showMemory); setShowTools(false); }}
          >
            🧠 Memory ({aiMemory.length})
          </button>
          <button className="action-btn" onClick={loadMaximusHealth}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* ═════════════════════════════════════════════════════════════════ */}
      {/* MAIN LAYOUT */}
      {/* ═════════════════════════════════════════════════════════════════ */}
      <div className="core-content">
        {/* SIDEBAR - Tools or Memory */}
        {(showTools || showMemory) && (
          <div className="core-sidebar">
            {showTools && (
              <div className="tools-panel">
                <div className="panel-header">
                  <h3>🔧 Available Tools</h3>
                  <select
                    className="category-select"
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                  >
                    <option value="all">All Categories</option>
                    <option value="offensive">Offensive Arsenal</option>
                    <option value="osint">OSINT</option>
                    <option value="cyber">Cyber Security</option>
                    <option value="asa">ASA</option>
                    <option value="world_class">World-Class</option>
                  </select>
                </div>

                <div className="tools-grid">
                  {getToolsByCategory().map((tool, idx) => (
                    <button
                      key={idx}
                      className="tool-card"
                      onClick={() => handleQuickToolCall(tool.name)}
                      title={`Category: ${tool.category}`}
                    >
                      <span className="tool-name">{tool.name}</span>
                      <span className="tool-category">{tool.category}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {showMemory && (
              <div className="memory-panel">
                <div className="panel-header">
                  <h3>🧠 AI Memory</h3>
                </div>

                <div className="memory-list">
                  {aiMemory.length > 0 ? (
                    aiMemory.map((mem, idx) => (
                      <div key={idx} className="memory-card">
                        <div className="memory-type">{mem.type || 'semantic'}</div>
                        <div className="memory-content">{mem.content || JSON.stringify(mem)}</div>
                        <div className="memory-time">
                          {mem.timestamp ? new Date(mem.timestamp).toLocaleString('pt-BR') : 'N/A'}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="empty-state">
                      <p>No memories stored yet</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* MAIN CHAT AREA */}
        <div className="chat-container">
          {/* Messages */}
          <div className="chat-messages">
            {messages.map(renderMessage)}

            {/* Streaming message */}
            {isStreaming && currentStreamingMessage && (
              <div className="chat-message message-streaming">
                <div className="message-header">
                  <span className="message-role">🤖 MAXIMUS AI</span>
                  <span className="streaming-indicator">
                    <span className="pulse-dot"></span>
                    Thinking...
                  </span>
                </div>
                <div className="message-content">
                  <div className="message-text" dangerouslySetInnerHTML={{
                    __html: escapeHTML(currentStreamingMessage)
                      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      .replace(/\n/g, '<br/>')
                  }} />
                </div>
              </div>
            )}

            {/* Quick Actions (shown when no messages) */}
            {messages.length === 1 && (
              <div className="quick-actions">
                <h3>⚡ Quick Actions</h3>
                <div className="actions-grid">
                  {quickActions.map((qa, idx) => (
                    <button
                      key={idx}
                      className="quick-action-card"
                      onClick={() => setInputMessage(qa.action)}
                    >
                      <span className="qa-icon">{qa.icon}</span>
                      <span className="qa-label">{qa.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Suggestions Bar */}
          {suggestions.length > 0 && (
            <div className="suggestions-bar">
              <span className="sugg-label">💡 Suggestions:</span>
              {suggestions.map((sugg, idx) => (
                <button
                  key={idx}
                  className="suggestion-chip"
                  onClick={() => setInputMessage(sugg.text || sugg.action)}
                >
                  {sugg.text || sugg.action}
                </button>
              ))}
            </div>
          )}

          {/* Input Area */}
          <div className="chat-input-area">
            <input
              type="text"
              className="chat-input"
              placeholder="Ask Maximus AI anything... (e.g., 'Run network scan on 192.168.1.0/24')"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              disabled={isStreaming}
            />
            <button
              className="send-button"
              onClick={handleSendMessage}
              disabled={isStreaming || !inputMessage.trim()}
            >
              {isStreaming ? '⏳' : '📤'}
            </button>
          </div>
        </div>
      </div>

      {/* Active Tools Indicator */}
      {activeTools.length > 0 && (
        <div className="active-tools-bar">
          <span className="at-label">🔧 Active Tools:</span>
          {activeTools.slice(0, 5).map((tool, idx) => (
            <span key={idx} className="active-tool-badge">{tool}</span>
          ))}
          {activeTools.length > 5 && (
            <span className="more-tools">+{activeTools.length - 5} more</span>
          )}
        </div>
      )}
    </div>
  );
};

export default MaximusCore;
