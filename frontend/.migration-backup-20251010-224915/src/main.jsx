// frontend/src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { AuthProvider } from './contexts/AuthContext.jsx'
import '@fortawesome/fontawesome-free/css/all.min.css';
import './index.css'
import './styles/accessibility.css'; // WCAG 2.1 AA compliance styles
import { initializeTheme } from './themes';

// Initialize theme before rendering
initializeTheme();

// The only change is removing the <React.StrictMode> wrapper.
// This is often necessary for compatibility with libraries like Mapbox GL.
ReactDOM.createRoot(document.getElementById('root')).render(
  <AuthProvider>
    <App />
  </AuthProvider>
)
