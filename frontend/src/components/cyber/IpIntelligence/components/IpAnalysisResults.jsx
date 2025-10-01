import React from 'react';
import styles from './IpAnalysisResults.module.css';
import ThreatCategory from './ThreatCategory';
import OpenPort from './OpenPort';
import IdentifiedService from './IdentifiedService';

/**
 * Displays the detailed analysis results for an IP address.
 */
const IpAnalysisResults = ({ analysisResult, getThreatColor }) => {
  if (!analysisResult) return null;

  const getReputationScoreClass = (score) => {
    if (score < 30) return styles.low;
    if (score < 70) return styles.medium;
    return styles.high;
  };

  return (
    <div className={styles.resultsGrid}>
      {/* Column 1: Location and Infrastructure */}
      <div className={styles.column}>
        <div className={styles.sectionCard}>
          <h3 className={styles.sectionTitle}>GEOLOCALIZAÇÃO</h3>
          <div className={styles.infoGroup}>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>ENDEREÇO IP</span>
              <span className={styles.infoValue}>{analysisResult.ip}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>PAÍS</span>
              <span className={styles.infoValue}>{analysisResult.location.country}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>REGIÃO/ESTADO</span>
              <span className={styles.infoValue}>{analysisResult.location.region}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>CIDADE</span>
              <span className={styles.infoValue}>{analysisResult.location.city}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>COORDENADAS</span>
              <span className={styles.infoValue}>
                {analysisResult.location.latitude.toFixed(3)}, {analysisResult.location.longitude.toFixed(3)}
              </span>
            </div>
          </div>
        </div>

        <div className={styles.sectionCard}>
          <h3 className={styles.sectionTitle}>INFRAESTRUTURA</h3>
          <div className={styles.infoGroup}>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>ISP</span>
              <span className={styles.infoValue}>{analysisResult.isp}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>ASN</span>
              <span className={styles.infoValue}>{analysisResult.asn.number}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>ORG ASN</span>
              <span className={styles.infoValue}>{analysisResult.asn.name}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>PTR RECORD</span>
              <span className={styles.infoValue}>{analysisResult.ptr_record}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Column 2: Threat Analysis */}
      <div className={styles.column}>
        <div className={styles.sectionCard}>
          <h3 className={styles.sectionTitle}>ANÁLISE DE AMEAÇAS</h3>
          <div className={styles.infoGroup}>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>NÍVEL DE AMEAÇA</span>
              <div className={`${styles.threatLevelBadge} ${styles[getThreatColor(analysisResult.threat_level)]}`}>
                {analysisResult.threat_level.toUpperCase()}
              </div>
            </div>

            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>SCORE DE REPUTAÇÃO</span>
              <div className={styles.reputationScoreContainer}>
                <div className={`${styles.reputationScoreValue} ${getReputationScoreClass(analysisResult.reputation.score)}`}>
                  {analysisResult.reputation.score}/100
                </div>
                <div className={styles.progressBar}>
                  <div
                    className={`${styles.progressBarFill} ${getReputationScoreClass(analysisResult.reputation.score)}`}
                    style={{ width: `${analysisResult.reputation.score}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>CATEGORIAS DE AMEAÇA</span>
              <div className={styles.threatCategories}>
                {analysisResult.reputation.categories.map((category, index) => (
                  <ThreatCategory key={index} category={category} />
                ))}
              </div>
            </div>

            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>ÚLTIMA ATIVIDADE</span>
              <span className={styles.infoValue}>{analysisResult.reputation.last_seen}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Column 3: Services and Ports */}
      <div className={styles.column}>
        <div className={styles.sectionCard}>
          <h3 className={styles.sectionTitle}>SERVIÇOS DETECTADOS</h3>
          <div className={styles.infoGroup}>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>PORTAS ABERTAS</span>
              <div className={styles.openPortsList}>
                {analysisResult.open_ports.map((port, index) => (
                  <OpenPort key={index} port={port} />
                ))}
              </div>
            </div>

            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>SERVIÇOS IDENTIFICADOS</span>
              <div className={styles.servicesList}>
                {analysisResult.services.map((service, index) => (
                  <IdentifiedService key={index} service={service} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(IpAnalysisResults);
