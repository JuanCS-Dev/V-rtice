/**
 * ⏱️ Threat Timeline Widget
 * 
 * Real-time chronological visualization of threat events.
 * Shows attack progression, severity escalation, and temporal patterns.
 * 
 * @module ThreatTimelineWidget
 */

'use client';

import React, { useState, useMemo } from 'react';
import { formatDateTime, formatDate, formatTime, getTimestamp } from '@/utils/dateHelpers';
import styles from './ThreatTimelineWidget.module.css';

const ThreatTimelineWidget = ({ events = [], compact = false }) => {
  const [filter, setFilter] = useState('all');
  const [expandedEvent, setExpandedEvent] = useState(null);

  /**
   * Filter and sort events
   */
  const filteredEvents = useMemo(() => {
    let filtered = [...events];
    
    if (filter !== 'all') {
      filtered = filtered.filter(e => e.severity === filter);
    }
    
    return filtered.sort((a, b) => 
      new Date(b.timestamp) - new Date(a.timestamp)
    );
  }, [events, filter]);

  /**
   * Group events by time buckets
   */
  const timeGroups = useMemo(() => {
    const groups = {
      'last-minute': [],
      'last-hour': [],
      'last-day': [],
      'older': []
    };

    const now = Date.now();

    filteredEvents.forEach(event => {
      const time = getTimestamp(event.timestamp);
      const diff = now - time;
      
      if (diff < 60000) {
        groups['last-minute'].push(event);
      } else if (diff < 3600000) {
        groups['last-hour'].push(event);
      } else if (diff < 86400000) {
        groups['last-day'].push(event);
      } else {
        groups['older'].push(event);
      }
    });
    
    return groups;
  }, [filteredEvents]);

  /**
   * Get severity info
   */
  const getSeverityInfo = (severity) => {
    const map = {
      critical: { color: '#ff0040', icon: '🔴', label: 'CRITICAL' },
      high: { color: '#ff4000', icon: '🟠', label: 'HIGH' },
      medium: { color: '#ffaa00', icon: '🟡', label: 'MEDIUM' },
      low: { color: '#00aa00', icon: '🟢', label: 'LOW' },
      info: { color: '#00aaff', icon: '🔵', label: 'INFO' }
    };
    return map[severity] || map.info;
  };

  /**
   * Format relative time
   */
  const getRelativeTime = (timestamp) => {
    const now = Date.now();
    const time = getTimestamp(timestamp);
    const diff = now - time;
    
    if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
  };

  /**
   * Render event card
   */
  const renderEvent = (event, index) => {
    const severityInfo = getSeverityInfo(event.severity);
    const isExpanded = expandedEvent === event.id;
    
    return (
      <div 
        key={event.id || index}
        className={`${styles.eventCard} ${compact ? styles.compact : ''}`}
        onClick={() => setExpandedEvent(isExpanded ? null : event.id)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setExpandedEvent(isExpanded ? null : event.id);
          }
        }}
        role="button"
        tabIndex={0}
      >
        <div className={styles.eventHeader}>
          <div className={styles.eventSeverity}>
            <span className={styles.severityIcon}>{severityInfo.icon}</span>
            <span 
              className={styles.severityLabel}
              style={{ color: severityInfo.color }}
            >
              {severityInfo.label}
            </span>
          </div>
          
          <span className={styles.eventTime}>
            {getRelativeTime(event.timestamp)}
          </span>
        </div>

        <div className={styles.eventBody}>
          <div className={styles.eventType}>
            {event.attack_type || 'Unknown Attack'}
          </div>
          
          <div className={styles.eventDetails}>
            <span className={styles.detail}>
              <span className={styles.detailLabel}>Source:</span>
              <span className={styles.detailValue}>{event.source_ip}</span>
            </span>
            <span className={styles.detail}>
              <span className={styles.detailLabel}>Target:</span>
              <span className={styles.detailValue}>{event.honeypot_id}</span>
            </span>
          </div>
        </div>

        {isExpanded && !compact && (
          <div className={styles.eventExpanded}>
            <div className={styles.expandedRow}>
              <span className={styles.expandedLabel}>Port:</span>
              <span className={styles.expandedValue}>{event.port || 'N/A'}</span>
            </div>
            <div className={styles.expandedRow}>
              <span className={styles.expandedLabel}>Protocol:</span>
              <span className={styles.expandedValue}>{event.protocol || 'N/A'}</span>
            </div>
            {event.payload && (
              <div className={styles.expandedRow}>
                <span className={styles.expandedLabel}>Payload:</span>
                <pre className={styles.payloadCode}>
                  {event.payload.substring(0, 200)}
                  {event.payload.length > 200 && '...'}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  /**
   * Render time group
   */
  const renderTimeGroup = (title, events) => {
    if (events.length === 0) return null;
    
    return (
      <div className={styles.timeGroup}>
        <div className={styles.groupHeader}>
          <h4 className={styles.groupTitle}>{title}</h4>
          <span className={styles.groupCount}>{events.length}</span>
        </div>
        <div className={styles.groupEvents}>
          {events.map((event, idx) => renderEvent(event, idx))}
        </div>
      </div>
    );
  };

  return (
    <div className={`${styles.container} ${compact ? styles.containerCompact : ''}`}>
      {!compact && (
        <div className={styles.header}>
          <h3 className={styles.title}>
            ⏱️ Threat Timeline
          </h3>
          
          <div className={styles.filters}>
            <button
              className={`${styles.filterButton} ${filter === 'all' ? styles.active : ''}`}
              onClick={() => setFilter('all')}
              aria-label={`Show all ${events.length} threat events`}
              aria-pressed={filter === 'all'}
            >
              All ({events.length})
            </button>
            <button
              className={`${styles.filterButton} ${filter === 'critical' ? styles.active : ''}`}
              onClick={() => setFilter('critical')}
              aria-label="Filter by critical severity threats"
              aria-pressed={filter === 'critical'}
            >
              Critical
            </button>
            <button
              className={`${styles.filterButton} ${filter === 'high' ? styles.active : ''}`}
              onClick={() => setFilter('high')}
              aria-label="Filter by high severity threats"
              aria-pressed={filter === 'high'}
            >
              High
            </button>
            <button
              className={`${styles.filterButton} ${filter === 'medium' ? styles.active : ''}`}
              onClick={() => setFilter('medium')}
              aria-label="Filter by medium severity threats"
              aria-pressed={filter === 'medium'}
            >
              Medium
            </button>
          </div>
        </div>
      )}

      <div className={styles.timeline}>
        {compact ? (
          <div className={styles.compactList}>
            {filteredEvents.slice(0, 10).map((event, idx) => renderEvent(event, idx))}
          </div>
        ) : (
          <>
            {renderTimeGroup('Last Minute', timeGroups['last-minute'])}
            {renderTimeGroup('Last Hour', timeGroups['last-hour'])}
            {renderTimeGroup('Last 24 Hours', timeGroups['last-day'])}
            {renderTimeGroup('Older', timeGroups['older'])}
          </>
        )}
        
        {filteredEvents.length === 0 && (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>🔍</div>
            <p className={styles.emptyText}>No threat events found</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ThreatTimelineWidget;
