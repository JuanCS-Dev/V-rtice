/**
 * ═══════════════════════════════════════════════════════════════════════════
 * ASK MAXIMUS BUTTON - Universal AI Assistant
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Componente reutilizável para integrar "Ask Maximus" em qualquer widget.
 * Permite que usuários peçam análise AI sobre qualquer dado/contexto.
 *
 * Features:
 * - Rate limiting (5 requests per minute)
 * - Error handling
 * - Loading states
 * - Response caching
 *
 * Usage:
 * <AskMaximusButton
 *   context={{ data: scanResults, type: 'network_scan' }}
 *   prompt="Analyze these scan results"
 * />
 */

import React, { useState } from 'react';
import { analyzeWithAI, chatWithMaximus } from '../../api/maximusAI';
import { useRateLimit } from '../../hooks/useRateLimit';
import './AskMaximusButton.css';

export const AskMaximusButton = ({
  context = {},
  prompt = null,
  onResponse = null,
  buttonText = '🤖 Ask Maximus AI',
  size = 'medium', // 'small', 'medium', 'large'
  variant = 'primary' // 'primary', 'secondary', 'ghost'
}) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [aiResponse, setAiResponse] = useState(null);
  const [customPrompt, setCustomPrompt] = useState(prompt || '');

  // Rate limiting: 5 AI requests per minute
  const { execute: executeWithRateLimit, remaining, resetIn } = useRateLimit('ask-maximus-ai', {
    maxRequests: 5,
    windowMs: 60000, // 1 minute
    onLimitExceeded: ({ resetIn: reset }) => {
      alert(`Rate limit exceeded. Please wait ${Math.ceil(reset / 1000)} seconds before asking again.`);
    }
  });

  // Handle AI analysis
  const handleAskMaximus = async () => {
    if (!customPrompt && !context) {
      alert('Please provide context or a question for Maximus AI');
      return;
    }

    setIsAnalyzing(true);
    setAiResponse(null);

    try {
      // Execute with rate limiting
      await executeWithRateLimit(async () => {
        let response;

        if (customPrompt) {
          // Use chat if there's a specific prompt
          response = await chatWithMaximus(customPrompt, { ...context, mode: 'deep_analysis' });
        } else {
          // Use analyze if only context provided
          response = await analyzeWithAI(context, { type: context.type || 'general' });
        }

        if (response.success) {
          const result = {
            response: response.response || response.analysis,
            suggestions: response.suggestions || [],
            tools_used: response.tools_used || [],
            timestamp: new Date().toISOString()
          };

          setAiResponse(result);

          if (onResponse) {
            onResponse(result);
          }
        } else {
          throw new Error(response.error || 'AI analysis failed');
        }
      });
    } catch (error) {
      console.error('Ask Maximus error:', error);
      setAiResponse({
        response: `Error: ${error.message}`,
        isError: true,
        timestamp: new Date().toISOString()
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClose = () => {
    setShowModal(false);
    setAiResponse(null);
    if (!prompt) setCustomPrompt('');
  };

  return (
    <>
      {/* Trigger Button */}
      <button
        className={`ask-maximus-btn ask-maximus-${size} ask-maximus-${variant}`}
        onClick={() => setShowModal(true)}
        disabled={isAnalyzing}
      >
        {isAnalyzing ? '⏳ Analyzing...' : buttonText}
      </button>

      {/* Modal */}
      {showModal && (
        <div className="ask-maximus-modal-overlay" onClick={handleClose}>
          <div className="ask-maximus-modal" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="modal-header">
              <h3>🤖 Ask Maximus AI</h3>
              <button className="modal-close" onClick={handleClose}>×</button>
            </div>

            {/* Content */}
            <div className="modal-content">
              {/* Prompt Input */}
              {!prompt && (
                <div className="prompt-section">
                  <label>What would you like to know?</label>
                  <textarea
                    className="prompt-input"
                    placeholder="E.g., 'Analyze this data for threats', 'What should I do next?', 'Explain these results'..."
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    rows={3}
                    disabled={isAnalyzing}
                  />
                </div>
              )}

              {prompt && (
                <div className="prompt-section">
                  <label>Question:</label>
                  <div className="prompt-display">{prompt}</div>
                </div>
              )}

              {/* Context Display */}
              {Object.keys(context).length > 0 && (
                <div className="context-section">
                  <label>Context provided:</label>
                  <div className="context-display">
                    <pre>{JSON.stringify(context, null, 2).slice(0, 300)}...</pre>
                  </div>
                </div>
              )}

              {/* AI Response */}
              {aiResponse && (
                <div className={`response-section ${aiResponse.isError ? 'response-error' : ''}`}>
                  <label>
                    {aiResponse.isError ? '⚠️ Error' : '🤖 Maximus AI Response'}
                  </label>
                  <div className="response-content">
                    <p>{aiResponse.response}</p>

                    {aiResponse.tools_used && aiResponse.tools_used.length > 0 && (
                      <div className="tools-used">
                        <span className="tools-label">🔧 Tools used:</span>
                        {aiResponse.tools_used.map((tool, idx) => (
                          <span key={idx} className="tool-badge">{tool}</span>
                        ))}
                      </div>
                    )}

                    {aiResponse.suggestions && aiResponse.suggestions.length > 0 && (
                      <div className="suggestions">
                        <span className="sugg-label">💡 Suggestions:</span>
                        <ul>
                          {aiResponse.suggestions.map((sugg, idx) => (
                            <li key={idx}>{sugg.text || sugg}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Loading State */}
              {isAnalyzing && (
                <div className="loading-section">
                  <div className="loading-spinner"></div>
                  <p>Maximus AI is analyzing...</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="modal-footer">
              {!aiResponse && (
                <button
                  className="btn-analyze"
                  onClick={handleAskMaximus}
                  disabled={isAnalyzing || (!customPrompt && !prompt)}
                >
                  {isAnalyzing ? '⏳ Analyzing...' : '🚀 Analyze with AI'}
                </button>
              )}
              <button className="btn-close" onClick={handleClose}>
                {aiResponse ? 'Close' : 'Cancel'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AskMaximusButton;
