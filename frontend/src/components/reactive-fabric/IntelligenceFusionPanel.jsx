/**
 * 🧠 Intelligence Fusion Panel
 * 
 * Correlates threat data across multiple honeypots to identify:
 * - Coordinated attack campaigns
 * - APT TTPs (Tactics, Techniques, Procedures)
 * - Emerging threat patterns
 * 
 * @module IntelligenceFusionPanel
 */

'use client';

import React, { useMemo } from 'react';
import { formatDateTime, formatDate, formatTime, getTimestamp } from '@/utils/dateHelpers';
import styles from './IntelligenceFusionPanel.module.css';

const IntelligenceFusionPanel = ({ fusionData: _fusionData, events = [] }) => {
  /**
   * Analyze attack patterns
   */
  const patterns = useMemo(() => {
    const ipGroups = {};
    
    events.forEach(event => {
      if (!ipGroups[event.source_ip]) {
        ipGroups[event.source_ip] = {
          ip: event.source_ip,
          targets: new Set(),
          techniques: new Set(),
          count: 0,
          firstSeen: event.timestamp,
          lastSeen: event.timestamp
        };
      }
      
      const group = ipGroups[event.source_ip];
      group.targets.add(event.honeypot_id);
      group.techniques.add(event.attack_type || 'unknown');
      group.count++;
      group.lastSeen = event.timestamp;
    });
    
    // Identify coordinated attacks (same IP, multiple targets)
    const coordinated = Object.values(ipGroups)
      .filter(g => g.targets.size > 1)
      .sort((a, b) => b.count - a.count);
    
    return {
      coordinated,
      totalIPs: Object.keys(ipGroups).length,
      multiTarget: coordinated.length
    };
  }, [events]);

  /**
   * TTP (Tactics, Techniques, Procedures) frequency
   */
  const ttpStats = useMemo(() => {
    const ttps = {};
    
    events.forEach(event => {
      const type = event.attack_type || 'unknown';
      if (!ttps[type]) {
        ttps[type] = 0;
      }
      ttps[type]++;
    });
    
    return Object.entries(ttps)
      .map(([type, count]) => ({ type, count }))
      .sort((a, b) => b.count - a.count);
  }, [events]);

  /**
   * Time-based clustering (attacks within 5 minute windows)
   */
  const clusters = useMemo(() => {
    const sorted = [...events].sort((a, b) => 
      new Date(a.timestamp) - new Date(b.timestamp)
    );
    
    const clusters = [];
    let currentCluster = null;
    const CLUSTER_WINDOW = 5 * 60 * 1000; // 5 minutes
    
    sorted.forEach(event => {
      const time = getTimestamp(event.timestamp);
      
      if (!currentCluster || time - currentCluster.end > CLUSTER_WINDOW) {
        currentCluster = {
          start: time,
          end: time,
          events: [event],
          ips: new Set([event.source_ip])
        };
        clusters.push(currentCluster);
      } else {
        currentCluster.end = time;
        currentCluster.events.push(event);
        currentCluster.ips.add(event.source_ip);
      }
    });
    
    return clusters
      .filter(c => c.events.length >= 5) // Minimum 5 events to be significant
      .sort((a, b) => b.events.length - a.events.length);
  }, [events]);

  /**
   * Get confidence level for pattern
   */
  const getConfidenceLevel = (count) => {
    if (count >= 50) return { level: 'Very High', color: '#00ff00' };
    if (count >= 20) return { level: 'High', color: '#00ffff' };
    if (count >= 10) return { level: 'Medium', color: '#ffaa00' };
    if (count >= 5) return { level: 'Low', color: '#ff4000' };
    return { level: 'Very Low', color: '#ff0040' };
  };

  return (
    <div className={styles.container}>
      {/* Overview Cards */}
      <div className={styles.overviewGrid}>
        <div className={styles.card}>
          <div className={styles.cardIcon}>🎯</div>
          <div className={styles.cardContent}>
            <span className={styles.cardLabel}>Total Threat Actors</span>
            <span className={styles.cardValue}>{patterns.totalIPs}</span>
          </div>
        </div>
        
        <div className={styles.card}>
          <div className={styles.cardIcon}>⚡</div>
          <div className={styles.cardContent}>
            <span className={styles.cardLabel}>Coordinated Attacks</span>
            <span className={`${styles.cardValue} ${styles.warning}`}>
              {patterns.multiTarget}
            </span>
          </div>
        </div>
        
        <div className={styles.card}>
          <div className={styles.cardIcon}>🔬</div>
          <div className={styles.cardContent}>
            <span className={styles.cardLabel}>Attack Clusters</span>
            <span className={styles.cardValue}>{clusters.length}</span>
          </div>
        </div>
        
        <div className={styles.card}>
          <div className={styles.cardIcon}>📊</div>
          <div className={styles.cardContent}>
            <span className={styles.cardLabel}>Unique TTPs</span>
            <span className={styles.cardValue}>{ttpStats.length}</span>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className={styles.contentGrid}>
        {/* Coordinated Attacks */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <h3 className={styles.panelTitle}>
              🎯 Coordinated Attack Campaigns
            </h3>
            <span className={styles.badge}>{patterns.coordinated.length}</span>
          </div>
          
          <div className={styles.panelContent}>
            {patterns.coordinated.length === 0 ? (
              <div className={styles.emptyState}>
                No coordinated attacks detected
              </div>
            ) : (
              <div className={styles.list}>
                {patterns.coordinated.slice(0, 10).map((attack, idx) => {
                  const confidence = getConfidenceLevel(attack.count);
                  
                  return (
                    <div key={idx} className={styles.listItem}>
                      <div className={styles.itemHeader}>
                        <span className={styles.itemIP}>{attack.ip}</span>
                        <span 
                          className={styles.itemConfidence}
                          style={{ color: confidence.color }}
                        >
                          {confidence.level}
                        </span>
                      </div>
                      
                      <div className={styles.itemStats}>
                        <span className={styles.itemStat}>
                          <span className={styles.itemStatLabel}>Targets:</span>
                          <span className={styles.itemStatValue}>{attack.targets.size}</span>
                        </span>
                        <span className={styles.itemStat}>
                          <span className={styles.itemStatLabel}>Attempts:</span>
                          <span className={styles.itemStatValue}>{attack.count}</span>
                        </span>
                        <span className={styles.itemStat}>
                          <span className={styles.itemStatLabel}>TTPs:</span>
                          <span className={styles.itemStatValue}>{attack.techniques.size}</span>
                        </span>
                      </div>
                      
                      <div className={styles.itemTechniques}>
                        {Array.from(attack.techniques).map((tech, i) => (
                          <span key={i} className={styles.tag}>{tech}</span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* TTP Analysis */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <h3 className={styles.panelTitle}>
              📊 TTP Distribution
            </h3>
            <span className={styles.badge}>{ttpStats.length}</span>
          </div>
          
          <div className={styles.panelContent}>
            <div className={styles.chartContainer}>
              {ttpStats.map((ttp, idx) => {
                const maxCount = ttpStats[0]?.count || 1;
                const percentage = (ttp.count / maxCount) * 100;
                
                return (
                  <div key={idx} className={styles.barItem}>
                    <div className={styles.barLabel}>
                      <span className={styles.barName}>{ttp.type}</span>
                      <span className={styles.barCount}>{ttp.count}</span>
                    </div>
                    <div className={styles.barTrack}>
                      <div 
                        className={styles.barFill}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Attack Clusters */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <h3 className={styles.panelTitle}>
              🔬 Attack Clusters
            </h3>
            <span className={styles.badge}>{clusters.length}</span>
          </div>
          
          <div className={styles.panelContent}>
            {clusters.length === 0 ? (
              <div className={styles.emptyState}>
                No significant clusters detected
              </div>
            ) : (
              <div className={styles.list}>
                {clusters.slice(0, 5).map((cluster, idx) => {
                  const duration = (cluster.end - cluster.start) / 1000;
                  const startTime = formatTime(cluster.start);
                  
                  return (
                    <div key={idx} className={styles.clusterItem}>
                      <div className={styles.clusterHeader}>
                        <span className={styles.clusterTime}>
                          {startTime}
                        </span>
                        <span className={styles.clusterDuration}>
                          {Math.round(duration)}s
                        </span>
                      </div>
                      
                      <div className={styles.clusterStats}>
                        <span className={styles.clusterStat}>
                          <strong>{cluster.events.length}</strong> events
                        </span>
                        <span className={styles.clusterStat}>
                          <strong>{cluster.ips.size}</strong> source IPs
                        </span>
                      </div>
                      
                      <div className={styles.clusterBar}>
                        <div 
                          className={styles.clusterBarFill}
                          style={{ 
                            width: `${Math.min((cluster.events.length / 50) * 100, 100)}%` 
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntelligenceFusionPanel;
