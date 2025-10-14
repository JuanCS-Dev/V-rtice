// frontend/src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { AuthProvider } from './contexts/AuthContext.jsx'
import { ThemeProvider } from './contexts/ThemeContext.jsx'
import '@fortawesome/fontawesome-free/css/all.min.css';
import './index.css'
import './styles/accessibility.css'; // WCAG 2.1 AA compliance styles
import './styles/core-theme.css'; // CORE THEME: Preto + Vermelho único

// The only change is removing the <React.StrictMode> wrapper.
// This is often necessary for compatibility with libraries like Mapbox GL.
ReactDOM.createRoot(document.getElementById('root')).render(
  <ThemeProvider>
    <AuthProvider>
      <App />
    </AuthProvider>
  </ThemeProvider>
)
