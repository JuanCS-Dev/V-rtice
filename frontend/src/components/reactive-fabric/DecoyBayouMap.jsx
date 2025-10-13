/**
 * 🗺️ Decoy Bayou Map - Geospatial Honeypot Visualization
 * 
 * Interactive map displaying honeypot locations and threat origins.
 * Real-time attack flow visualization with threat level indicators.
 * 
 * @module DecoyBayouMap
 */

'use client';

import React, { useState, useEffect, useMemo } from 'react';
import styles from './DecoyBayouMap.module.css';

/**
 * Geographic coordinates for visualization
 */
const HONEYPOT_LOCATIONS = {
  'ssh-01': { lat: 37.7749, lon: -122.4194, city: 'San Francisco' },
  'http-01': { lat: 40.7128, lon: -74.0060, city: 'New York' },
  'ftp-01': { lat: 51.5074, lon: -0.1278, city: 'London' },
  'smtp-01': { lat: 35.6762, lon: 139.6503, city: 'Tokyo' },
};

const DecoyBayouMap = ({ honeypots = [], threats = [] }) => {
  const [selectedHoneypot, setSelectedHoneypot] = useState(null);
  const [timeWindow, setTimeWindow] = useState('1h');
  const [animationEnabled, setAnimationEnabled] = useState(true);

  /**
   * Filter threats by time window
   */
  const filteredThreats = useMemo(() => {
    const now = Date.now();
    const windows = {
      '1h': 3600000,
      '6h': 21600000,
      '24h': 86400000,
      '7d': 604800000
    };
    
    const cutoff = now - (windows[timeWindow] || windows['1h']);
    
    return threats.filter(t => 
      new Date(t.timestamp).getTime() > cutoff
    );
  }, [threats, timeWindow]);

  /**
   * Calculate threat density per honeypot
   */
  const honeypotStats = useMemo(() => {
    const stats = {};
    
    honeypots.forEach(hp => {
      const hpThreats = filteredThreats.filter(t => t.honeypot_id === hp.id);
      stats[hp.id] = {
        total: hpThreats.length,
        critical: hpThreats.filter(t => t.severity === 'critical').length,
        high: hpThreats.filter(t => t.severity === 'high').length,
        uniqueIPs: new Set(hpThreats.map(t => t.source_ip)).size
      };
    });
    
    return stats;
  }, [honeypots, filteredThreats]);

  /**
   * Get severity color
   */
  const getSeverityColor = (count) => {
    if (count >= 100) return '#ff0040';
    if (count >= 50) return '#ff4000';
    if (count >= 10) return '#ffaa00';
    return '#00aa00';
  };

  /**
   * Get honeypot marker size based on activity
   */
  const getMarkerSize = (honeypotId) => {
    const stats = honeypotStats[honeypotId] || { total: 0 };
    const base = 20;
    const scale = Math.log10(stats.total + 1) * 10;
    return Math.min(base + scale, 60);
  };

  return (
    <div className={styles.mapContainer}>
      {/* Controls */}
      <div className={styles.controls}>
        <div className={styles.controlGroup}>
          <label className={styles.controlLabel}>Time Window:</label>
          <select 
            className={styles.select}
            value={timeWindow}
            onChange={(e) => setTimeWindow(e.target.value)}
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
        </div>
        
        <div className={styles.controlGroup}>
          <label className={styles.controlLabel} htmlFor="animation-toggle">
            <input 
              id="animation-toggle"
              type="checkbox"
              checked={animationEnabled}
              onChange={(e) => setAnimationEnabled(e.target.checked)}
              className={styles.checkbox}
            />
            Animation
          </label>
        </div>

        <div className={styles.legend}>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: '#00aa00' }} />
            Low Activity
          </div>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: '#ffaa00' }} />
            Medium
          </div>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: '#ff4000' }} />
            High
          </div>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: '#ff0040' }} />
            Critical
          </div>
        </div>
      </div>

      {/* Map Visualization */}
      <div className={styles.map}>
        <svg 
          className={styles.mapSvg}
          viewBox="0 0 1000 500"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Background Grid */}
          <defs>
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path 
                d="M 50 0 L 0 0 0 50" 
                fill="none" 
                stroke="rgba(220, 38, 38, 0.1)" 
                strokeWidth="1"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Connection Lines (Threat Flows) */}
          {animationEnabled && filteredThreats.slice(0, 20).map((threat, idx) => {
            const target = HONEYPOT_LOCATIONS[threat.honeypot_id];
            if (!target) return null;
            
            // Mock source location (in real implementation, use GeoIP)
            const sourceX = Math.random() * 1000;
            const sourceY = Math.random() * 500;
            const targetX = (target.lon + 180) * (1000 / 360);
            const targetY = (90 - target.lat) * (500 / 180);
            
            return (
              <line
                key={`flow-${idx}`}
                x1={sourceX}
                y1={sourceY}
                x2={targetX}
                y2={targetY}
                stroke={threat.severity === 'critical' ? '#ff0040' : '#dc2626'}
                strokeWidth="1"
                strokeOpacity="0.3"
                className={styles.threatFlow}
              />
            );
          })}

          {/* Honeypot Markers */}
          {honeypots.map(honeypot => {
            const location = HONEYPOT_LOCATIONS[honeypot.id];
            if (!location) return null;
            
            const x = (location.lon + 180) * (1000 / 360);
            const y = (90 - location.lat) * (500 / 180);
            const stats = honeypotStats[honeypot.id] || { total: 0 };
            const size = getMarkerSize(honeypot.id);
            const color = getSeverityColor(stats.total);
            
            return (
              <g 
                key={honeypot.id}
                className={styles.honeypotMarker}
                onClick={() => setSelectedHoneypot(honeypot)}
              >
                {/* Pulse animation */}
                {animationEnabled && (
                  <circle
                    cx={x}
                    cy={y}
                    r={size}
                    fill={color}
                    opacity="0.3"
                    className={styles.pulse}
                  />
                )}
                
                {/* Main marker */}
                <circle
                  cx={x}
                  cy={y}
                  r={size / 2}
                  fill={color}
                  stroke="white"
                  strokeWidth="2"
                  opacity="0.9"
                />
                
                {/* Label */}
                <text
                  x={x}
                  y={y - size}
                  textAnchor="middle"
                  fill="white"
                  fontSize="12"
                  fontWeight="600"
                  className={styles.markerLabel}
                >
                  {honeypot.name}
                </text>
                
                {/* Activity count */}
                <text
                  x={x}
                  y={y + 5}
                  textAnchor="middle"
                  fill="white"
                  fontSize="10"
                  fontWeight="700"
                >
                  {stats.total}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Details Panel */}
      {selectedHoneypot && (
        <div className={styles.detailsPanel}>
          <div className={styles.detailsHeader}>
            <h3 className={styles.detailsTitle}>
              {selectedHoneypot.name}
            </h3>
            <button 
              className={styles.closeButton}
              onClick={() => setSelectedHoneypot(null)}
            >
              ✕
            </button>
          </div>
          
          <div className={styles.detailsContent}>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Type:</span>
              <span className={styles.detailValue}>{selectedHoneypot.type}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Status:</span>
              <span className={`${styles.detailValue} ${styles[selectedHoneypot.status]}`}>
                {selectedHoneypot.status}
              </span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Location:</span>
              <span className={styles.detailValue}>
                {HONEYPOT_LOCATIONS[selectedHoneypot.id]?.city || 'Unknown'}
              </span>
            </div>
            
            <div className={styles.statsGrid}>
              <div className={styles.statBox}>
                <span className={styles.statLabel}>Total Hits</span>
                <span className={styles.statValue}>
                  {honeypotStats[selectedHoneypot.id]?.total || 0}
                </span>
              </div>
              <div className={styles.statBox}>
                <span className={styles.statLabel}>Critical</span>
                <span className={`${styles.statValue} ${styles.critical}`}>
                  {honeypotStats[selectedHoneypot.id]?.critical || 0}
                </span>
              </div>
              <div className={styles.statBox}>
                <span className={styles.statLabel}>High</span>
                <span className={`${styles.statValue} ${styles.high}`}>
                  {honeypotStats[selectedHoneypot.id]?.high || 0}
                </span>
              </div>
              <div className={styles.statBox}>
                <span className={styles.statLabel}>Unique IPs</span>
                <span className={styles.statValue}>
                  {honeypotStats[selectedHoneypot.id]?.uniqueIPs || 0}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DecoyBayouMap;
