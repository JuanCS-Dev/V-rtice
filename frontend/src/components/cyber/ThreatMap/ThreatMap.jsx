/**
 * THREAT MAP - Real-time Global Cyber Threat Visualization
 *
 * Visualização geográfica de ameaças cyber em tempo real
 * Integração com Leaflet + clustering
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="threat-map"
 * - <header> for tool header via Card wrapper
 * - <section> for filters
 * - <section> for map container
 * - <section> for stats bar
 * - <section> for threat details (conditional)
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="threat-map"
 * - Monitor threats via data-maximus-status
 * - Access filters via data-maximus-section="filters"
 * - Interpret threat distribution via semantic structure
 *
 * REFATORAÇÃO:
 * - Lógica de dados isolada (useThreatData)
 * - Marcadores em componente separado
 * - Filtros em componente separado
 * - Utils isolados
 * - CSS Modules + Design tokens
 *
 * Antes: 621 linhas | Depois: ~150 linhas
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React, { useState, lazy, Suspense } from 'react';
import 'leaflet/dist/leaflet.css';
import { MapContainer, TileLayer } from 'react-leaflet';
import { Card, Badge, LoadingSpinner } from '../../shared';
import AskMaximusButton from '../../shared/AskMaximusButton';
import { ThreatFilters } from './components/ThreatFilters';
import { useThreatData } from './hooks/useThreatData';
import styles from './ThreatMap.module.css';

// OTIMIZADO: Lazy load apenas dos componentes pesados
const ThreatMarkers = lazy(() => import('./components/ThreatMarkers'));

export const ThreatMap = () => {
  const { threats, loading, error, filters, setFilters, refresh } = useThreatData();
  const [selectedThreat, setSelectedThreat] = useState(null);

  const handleThreatClick = (threat) => {
    setSelectedThreat(threat);
  };

  return (
    <Card
      title="CYBER THREAT MAP"
      badge={`${threats.length} THREATS`}
      variant="cyber"
      className={styles.widget}
      data-maximus-tool="threat-map"
      data-maximus-category="shared"
      data-maximus-status={loading ? 'loading' : 'ready'}
      headerActions={
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <AskMaximusButton
            context={{
              type: 'threat_map',
              data: threats,
              count: threats.length,
              filters
            }}
            prompt="Analyze these global cyber threats and identify patterns, high-risk regions, and threat trends"
            size="small"
            variant="secondary"
          />
          <button
            className={styles.refreshButton}
            onClick={refresh}
            disabled={loading}
            title="Atualizar"
          >
            <i className={`fas fa-sync ${loading ? 'fa-spin' : ''}`}></i>
          </button>
        </div>
      }
    >
      <div className={styles.container}>
        {/* Filters */}
        <section
          role="region"
          aria-label="Threat filters"
          data-maximus-section="filters">
          <ThreatFilters filters={filters} onFiltersChange={setFilters} />
        </section>

        {/* Map Container */}
        <section
          className={styles.mapWrapper}
          role="region"
          aria-label="Threat map visualization"
          data-maximus-section="map">
          {loading && (
            <div className={styles.loadingOverlay}>
              <LoadingSpinner variant="cyber" size="lg" text="Carregando ameaças..." />
            </div>
          )}

          {error && (
            <div className={styles.errorOverlay}>
              <i className="fas fa-exclamation-triangle"></i>
              <p>{error}</p>
            </div>
          )}

          <MapContainer
            center={[-23.5505, -46.6333]}
            zoom={10}
            className={styles.map}
            zoomControl={true}
            preferCanvas={true}
            key="threat-map"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              maxZoom={19}
              subdomains="abcd"
              errorTileUrl="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            />
            <Suspense fallback={null}>
              <ThreatMarkers threats={threats} onThreatClick={handleThreatClick} />
            </Suspense>
          </MapContainer>
        </section>

        {/* Stats Bar */}
        <section
          className={styles.statsBar}
          role="region"
          aria-label="Threat statistics"
          data-maximus-section="stats">
          <div className={styles.stat}>
            <span className={styles.statLabel}>TOTAL:</span>
            <span className={styles.statValue}>{threats.length}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>CRITICAL:</span>
            <Badge variant="critical" size="sm">
              {threats.filter(t => t.severity === 'critical').length}
            </Badge>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>HIGH:</span>
            <Badge variant="high" size="sm">
              {threats.filter(t => t.severity === 'high').length}
            </Badge>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>MEDIUM:</span>
            <Badge variant="medium" size="sm">
              {threats.filter(t => t.severity === 'medium').length}
            </Badge>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>LOW:</span>
            <Badge variant="low" size="sm">
              {threats.filter(t => t.severity === 'low').length}
            </Badge>
          </div>
        </section>

        {/* Selected Threat Details */}
        {selectedThreat && (
          <section
            className={styles.threatDetails}
            role="region"
            aria-label="Selected threat details"
            data-maximus-section="threat-details">
            <div className={styles.detailsHeader}>
              <h6 className={styles.detailsTitle}>
                {selectedThreat.type.toUpperCase()}
              </h6>
              <button
                className={styles.closeButton}
                onClick={() => setSelectedThreat(null)}
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
            <div className={styles.detailsBody}>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Severity:</span>
                <Badge variant={selectedThreat.severity} size="sm">
                  {selectedThreat.severity}
                </Badge>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Source:</span>
                <span className={styles.detailValue}>{selectedThreat.source}</span>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Location:</span>
                <span className={styles.detailValue}>
                  {selectedThreat.lat.toFixed(4)}, {selectedThreat.lng.toFixed(4)}
                </span>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Time:</span>
                <span className={styles.detailValue}>
                  {new Date(selectedThreat.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          </section>
        )}
      </div>
    </Card>
  );
};

export default ThreatMap;
