// /home/juan/vertice-dev/frontend/src/App.jsx

import React, { useState, useEffect } from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import { LandingPage } from './components/LandingPage';
import AdminDashboard from './components/AdminDashboard';
import CyberDashboard from './components/CyberDashboard';
import OSINTDashboard from './components/OSINTDashboard';
import TerminalDashboard from './components/terminal/TerminalDashboard';

function App() {
  const [currentView, setCurrentView] = useState('main'); // 'main', 'admin', 'cyber', 'osint', 'terminal'

  if (currentView === 'admin') {
    return (
      <ErrorBoundary>
        <AdminDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    );
  }

  if (currentView === 'cyber') {
    return (
      <ErrorBoundary>
        <CyberDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    );
  }

  if (currentView === 'osint') {
    return (
      <ErrorBoundary>
        <OSINTDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    );
  }

  if (currentView === 'terminal') {
    return (
      <ErrorBoundary>
        <TerminalDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    );
  }

  // Landing Page principal
  return (
    <ErrorBoundary>
      <LandingPage setCurrentView={setCurrentView} />
    </ErrorBoundary>
  );
}

export default App;
