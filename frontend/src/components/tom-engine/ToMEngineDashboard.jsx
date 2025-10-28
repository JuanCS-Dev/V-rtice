/**
 * ToM Engine Dashboard - Theory of Mind Engine
 * Threat Actor Profiling & Behavioral Prediction
 */

import React from 'react';

export const ToMEngineDashboard = ({ setCurrentView }) => {
  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
      color: '#fff',
      padding: '40px'
    }}>
      <header style={{ marginBottom: '40px' }}>
        <button 
          onClick={() => setCurrentView('main')}
          style={{
            background: 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.2)',
            color: '#fff',
            padding: '10px 20px',
            cursor: 'pointer',
            marginBottom: '20px'
          }}
        >
          ← Back to Home
        </button>
        <h1 style={{ fontSize: '3rem', marginBottom: '10px' }}>🧠 ToM Engine</h1>
        <p style={{ fontSize: '1.2rem', opacity: 0.8 }}>
          Theory of Mind - Threat Actor Profiling & Behavioral Prediction
        </p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
        {/* Threat Map */}
        <div 
          data-testid="tom-threat-map"
          style={{
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
            padding: '30px'
          }}
        >
          <h2 style={{ marginBottom: '20px' }}>🗺️ Threat Actor Map</h2>
          <div style={{ 
            height: '300px', 
            background: 'rgba(139, 0, 0, 0.2)',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2rem'
          }}>
            🌐 Global Threat Landscape
          </div>
          <div style={{ marginTop: '20px', fontSize: '0.9rem', opacity: 0.7 }}>
            Real-time visualization of threat actor behaviors and attack patterns
          </div>
        </div>

        {/* Behavioral Analysis */}
        <div style={{
          background: 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '8px',
          padding: '30px'
        }}>
          <h2 style={{ marginBottom: '20px' }}>📊 Behavioral Analysis</h2>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {[
              { type: 'APT Group', pattern: 'Lateral Movement', risk: 'CRITICAL' },
              { type: 'Script Kiddie', pattern: 'Port Scanning', risk: 'LOW' },
              { type: 'Insider Threat', pattern: 'Data Exfiltration', risk: 'HIGH' }
            ].map((actor, i) => (
              <li key={i} style={{ 
                background: 'rgba(255,255,255,0.03)',
                padding: '15px',
                marginBottom: '10px',
                borderRadius: '4px',
                borderLeft: `4px solid ${actor.risk === 'CRITICAL' ? '#ff0000' : actor.risk === 'HIGH' ? '#ff6600' : '#00ff00'}`
              }}>
                <strong>{actor.type}</strong> - {actor.pattern}
                <span style={{ 
                  float: 'right', 
                  fontWeight: 'bold',
                  color: actor.risk === 'CRITICAL' ? '#ff0000' : actor.risk === 'HIGH' ? '#ff6600' : '#00ff00'
                }}>
                  {actor.risk}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Prediction Model */}
        <div style={{
          background: 'rgba(255,255,255,0.05)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '8px',
          padding: '30px'
        }}>
          <h2 style={{ marginBottom: '20px' }}>🔮 Predictive Modeling</h2>
          <div style={{ fontSize: '0.9rem' }}>
            <p style={{ marginBottom: '15px' }}>
              <strong>Next Attack Vector Predictions:</strong>
            </p>
            <ul style={{ paddingLeft: '20px' }}>
              <li>RDP Brute Force - 87% probability (next 24h)</li>
              <li>Phishing Campaign - 72% probability (next 48h)</li>
              <li>SQL Injection Attempt - 45% probability (next 72h)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ToMEngineDashboard;
