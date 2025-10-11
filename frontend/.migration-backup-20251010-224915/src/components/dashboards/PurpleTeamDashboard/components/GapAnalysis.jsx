/**
 * GapAnalysis - Detection Gap Analysis
 * Identifies attacks that were NOT detected, showing blind spots in defenses
 */

import React from 'react';
import styles from './GapAnalysis.module.css';

export const GapAnalysis = ({ gaps, attackData, defenseData, loading }) => {
  return (
    <div className={styles.analysisContainer}>
      <div className={styles.header}>
        <h2 className={styles.title}>
          <span className={styles.icon}>📊</span>
          DETECTION GAP ANALYSIS
        </h2>
        <div className={styles.coverageBadge}>
          <span className={styles.coverageValue}>{gaps.coveragePercentage || 0}%</span>
          <span className={styles.coverageLabel}>COVERAGE</span>
        </div>
      </div>

      <div className={styles.content}>
        {loading ? (
          <div className={styles.loading}>
            <div className={styles.spinner}></div>
            <p>Analyzing detection gaps...</p>
          </div>
        ) : (
          <>
            {/* Summary Cards */}
            <div className={styles.summaryGrid}>
              <div className={`${styles.summaryCard} ${styles.totalAttacks}`}>
                <div className={styles.summaryIcon}>⚔️</div>
                <div className={styles.summaryValue}>{attackData.total || 0}</div>
                <div className={styles.summaryLabel}>TOTAL ATTACKS</div>
              </div>

              <div className={`${styles.summaryCard} ${styles.detected}`}>
                <div className={styles.summaryIcon}>✓</div>
                <div className={styles.summaryValue}>{gaps.detected || 0}</div>
                <div className={styles.summaryLabel}>DETECTED</div>
              </div>

              <div className={`${styles.summaryCard} ${styles.undetected}`}>
                <div className={styles.summaryIcon}>⚠️</div>
                <div className={styles.summaryValue}>{gaps.undetected || 0}</div>
                <div className={styles.summaryLabel}>MISSED</div>
              </div>

              <div className={`${styles.summaryCard} ${styles.falsePositives}`}>
                <div className={styles.summaryIcon}>⚡</div>
                <div className={styles.summaryValue}>{gaps.falsePositives || 0}</div>
                <div className={styles.summaryLabel}>FALSE POSITIVES</div>
              </div>
            </div>

            {/* Gap Details */}
            <div className={styles.gapSection}>
              <h3 className={styles.sectionTitle}>
                <span className={styles.warningIcon}>⚠️</span>
                UNDETECTED ATTACKS (CRITICAL GAPS)
              </h3>

              {gaps.undetectedAttacks && gaps.undetectedAttacks.length > 0 ? (
                <div className={styles.gapList}>
                  {gaps.undetectedAttacks.map((attack, index) => (
                    <div key={attack.id || index} className={styles.gapCard}>
                      <div className={styles.gapHeader}>
                        <span className={styles.gapType}>{attack.type}</span>
                        <span className={styles.gapSeverity}>CRITICAL</span>
                      </div>

                      <div className={styles.gapBody}>
                        <div className={styles.gapField}>
                          <span className={styles.gapLabel}>Target:</span>
                          <span className={styles.gapValue}>{attack.target}</span>
                        </div>
                        <div className={styles.gapField}>
                          <span className={styles.gapLabel}>Technique:</span>
                          <span className={styles.gapValue}>{attack.technique}</span>
                        </div>
                        <div className={styles.gapField}>
                          <span className={styles.gapLabel}>MITRE ATT&CK:</span>
                          <span className={styles.gapValue}>{attack.mitreId || 'N/A'}</span>
                        </div>
                      </div>

                      <div className={styles.recommendation}>
                        <div className={styles.recommendationIcon}>💡</div>
                        <div className={styles.recommendationText}>
                          {attack.recommendation ||
                            'Review detection rules for this attack technique'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={styles.noGaps}>
                  <div className={styles.noGapsIcon}>✅</div>
                  <p>All attacks were detected!</p>
                  <span>Your defensive coverage is excellent</span>
                </div>
              )}
            </div>

            {/* Coverage by Technique */}
            {gaps.coverageByTechnique && (
              <div className={styles.techniqueSection}>
                <h3 className={styles.sectionTitle}>
                  <span className={styles.chartIcon}>📈</span>
                  COVERAGE BY ATTACK TECHNIQUE
                </h3>

                <div className={styles.techniqueList}>
                  {Object.entries(gaps.coverageByTechnique).map(
                    ([technique, coverage], index) => (
                      <div key={index} className={styles.techniqueCard}>
                        <div className={styles.techniqueName}>{technique}</div>
                        <div className={styles.coverageBar}>
                          <div
                            className={`${styles.coverageFill} ${
                              coverage >= 80
                                ? styles.good
                                : coverage >= 50
                                ? styles.medium
                                : styles.poor
                            }`}
                            style={{ width: `${coverage}%` }}
                          />
                          <span className={styles.coverageText}>{coverage}%</span>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
