/**
 * ═══════════════════════════════════════════════════════════════════════════
 * CODE BLOCK COMPONENT - React Island
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Code block com:
 * - Syntax highlighting (simples mas funcional)
 * - Copy to clipboard
 * - Line numbers
 * - Language badge
 *
 * Zero dependencies externas (Prism.js seria overhead).
 * Highlighting básico mas profissional com RegEx.
 */

import { useState } from 'react';

interface CodeBlockProps {
  code: string;
  language?: string;
}

export default function CodeBlock({ code, language = 'bash' }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  // Simple syntax highlighting for bash/shell
  const highlightBash = (text: string): string => {
    return text
      // Comments
      .replace(/(#.*$)/gm, '<span class="comment">$1</span>')
      // Strings
      .replace(/(".*?")/g, '<span class="string">$1</span>')
      .replace(/('.*?')/g, '<span class="string">$1</span>')
      // Commands (at start of line or after &&, ||, |)
      .replace(/(^|&&|\|\||;|\|)\s*([a-z\-]+)/gm, '$1 <span class="command">$2</span>')
      // Flags
      .replace(/(\s)(-{1,2}[a-z\-]+)/g, '$1<span class="flag">$2</span>')
      // URLs
      .replace(/(https?:\/\/[^\s]+)/g, '<span class="url">$1</span>');
  };

  const lines = code.split('\n');
  const highlightedLines = lines.map(line => highlightBash(line));

  return (
    <div className="code-block-wrapper">
      {/* Header */}
      <div className="code-block-header">
        <span className="code-lang-badge">{language}</span>

        <button
          className="copy-button"
          onClick={handleCopy}
          aria-label="Copy code to clipboard"
        >
          {copied ? (
            <>
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              Copy
            </>
          )}
        </button>
      </div>

      {/* Code */}
      <div className="code-block-content">
        <pre className="code-pre">
          <code className="code-text">
            {highlightedLines.map((line, index) => (
              <div key={index} className="code-line">
                <span className="line-number">{index + 1}</span>
                <span
                  className="line-content"
                  dangerouslySetInnerHTML={{ __html: line || '&nbsp;' }}
                />
              </div>
            ))}
          </code>
        </pre>
      </div>
    </div>
  );
}
