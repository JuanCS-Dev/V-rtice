// frontend/src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { AuthProvider } from './contexts/AuthContext.jsx'
import { ThemeProvider } from './contexts/ThemeContext.jsx'
import { validateConfiguration } from './config/endpoints'
import '@fortawesome/fontawesome-free/css/all.min.css';
import './index.css'
import './styles/accessibility.css'; // WCAG 2.1 AA compliance styles
import './styles/core-theme.css'; // CORE THEME: Preto + Vermelho único

// ═══════════════════════════════════════════════════════════════════════════
// CONFIGURATION VALIDATION (Fail-fast)
// ═══════════════════════════════════════════════════════════════════════════
// Governed by: Constituição Vértice v2.5 - ADR-001
//
// Validates that all required environment variables are set.
// In production, missing vars will throw ConfigurationError and prevent app startup.
// This is intentional: better to fail immediately than run with broken config.
// ═══════════════════════════════════════════════════════════════════════════

try {
  validateConfiguration();
} catch (error) {
  // Show configuration error to user
  document.getElementById('root').innerHTML = `
    <div style="
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      background: #0a0a0a;
      color: #fff;
      font-family: 'Courier New', monospace;
      padding: 2rem;
    ">
      <div style="max-width: 800px; text-align: left;">
        <h1 style="color: #ff0000; margin-bottom: 1rem;">⚠️ Configuration Error</h1>
        <pre style="
          background: #1a1a1a;
          padding: 1.5rem;
          border-left: 4px solid #ff0000;
          overflow-x: auto;
          white-space: pre-wrap;
          word-wrap: break-word;
        ">${error.message}</pre>
        <p style="margin-top: 1rem; color: #888;">
          The application cannot start without proper configuration.
          Please contact your system administrator.
        </p>
      </div>
    </div>
  `;
  throw error; // Re-throw to prevent further execution
}

// The only change is removing the <React.StrictMode> wrapper.
// This is often necessary for compatibility with libraries like Mapbox GL.
ReactDOM.createRoot(document.getElementById('root')).render(
  <ThemeProvider>
    <AuthProvider>
      <App />
    </AuthProvider>
  </ThemeProvider>
)
