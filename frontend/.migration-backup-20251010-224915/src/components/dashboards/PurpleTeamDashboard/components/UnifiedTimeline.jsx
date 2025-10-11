/**
 * UnifiedTimeline - Chronological view of red & blue team activities
 * Shows attacks and detections on a unified timeline with correlations
 */

import React from 'react';
import styles from './UnifiedTimeline.module.css';

export const UnifiedTimeline = ({ events, correlations, loading }) => {
  // Sort events by timestamp
  const sortedEvents = [...events].sort((a, b) =>
    new Date(b.timestamp) - new Date(a.timestamp)
  );

  const getEventType = (event) => {
    return event.eventType || (event.technique ? 'attack' : 'detection');
  };

  const getCorrelation = (event) => {
    const type = getEventType(event);
    if (type === 'attack') {
      return correlations.find(c => c.attackId === event.id);
    } else {
      return correlations.find(c => c.detectionId === event.id);
    }
  };

  return (
    <div className={styles.timelineContainer}>
      <div className={styles.timelineHeader}>
        <h2 className={styles.timelineTitle}>
          <span className={styles.timelineIcon}>⏱️</span>
          UNIFIED TIMELINE
        </h2>
        <div className={styles.timelineStats}>
          <div className={styles.stat}>
            <span className={styles.statValue}>{events.length}</span>
            <span className={styles.statLabel}>TOTAL EVENTS</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statValue}>{correlations.length}</span>
            <span className={styles.statLabel}>CORRELATIONS</span>
          </div>
        </div>
      </div>

      <div className={styles.timeline}>
        {loading ? (
          <div className={styles.loading}>
            <div className={styles.spinner}></div>
            <p>Loading timeline data...</p>
          </div>
        ) : sortedEvents.length === 0 ? (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>📅</div>
            <p>No events yet</p>
            <span>Timeline will populate as operations occur</span>
          </div>
        ) : (
          sortedEvents.map((event, index) => {
            const eventType = getEventType(event);
            const correlation = getCorrelation(event);
            const isAttack = eventType === 'attack';

            return (
              <div
                key={event.id || index}
                className={`${styles.timelineEvent} ${
                  isAttack ? styles.attackEvent : styles.detectionEvent
                } ${correlation ? styles.correlated : ''}`}
              >
                <div className={styles.eventTimestamp}>
                  {new Date(event.timestamp).toLocaleString()}
                </div>

                <div className={styles.eventMarker}>
                  <div className={styles.markerDot}></div>
                  <div className={styles.markerLine}></div>
                </div>

                <div className={styles.eventCard}>
                  <div className={styles.eventHeader}>
                    <div className={styles.eventType}>
                      <span className={styles.eventIcon}>
                        {isAttack ? '⚔️' : '🛡️'}
                      </span>
                      <span className={styles.eventLabel}>
                        {isAttack ? 'RED TEAM' : 'BLUE TEAM'}
                      </span>
                    </div>
                    <span className={styles.eventBadge}>
                      {event.type || event.technique}
                    </span>
                  </div>

                  <div className={styles.eventBody}>
                    {isAttack ? (
                      <>
                        <div className={styles.eventField}>
                          <span className={styles.fieldLabel}>Target:</span>
                          <span className={styles.fieldValue}>{event.target}</span>
                        </div>
                        <div className={styles.eventField}>
                          <span className={styles.fieldLabel}>Technique:</span>
                          <span className={styles.fieldValue}>{event.technique}</span>
                        </div>
                        <div className={styles.eventField}>
                          <span className={styles.fieldLabel}>Status:</span>
                          <span className={styles.fieldValue}>{event.status}</span>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className={styles.eventField}>
                          <span className={styles.fieldLabel}>Source:</span>
                          <span className={styles.fieldValue}>{event.source}</span>
                        </div>
                        <div className={styles.eventField}>
                          <span className={styles.fieldLabel}>Rule:</span>
                          <span className={styles.fieldValue}>{event.rule}</span>
                        </div>
                        <div className={styles.eventField}>
                          <span className={styles.fieldLabel}>Severity:</span>
                          <span className={`${styles.severity} ${styles[event.severity]}`}>
                            {event.severity}
                          </span>
                        </div>
                      </>
                    )}
                  </div>

                  {correlation && (
                    <div className={styles.correlationBanner}>
                      🟣 CORRELATED EVENT
                      {isAttack ? ' - DETECTED BY BLUE TEAM' : ' - LINKED TO RED TEAM ATTACK'}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
