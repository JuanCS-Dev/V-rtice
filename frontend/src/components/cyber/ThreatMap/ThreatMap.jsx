/**
 * Threat Map - REFATORADO
 *
 * Visualização geográfica de ameaças cyber em tempo real
 * Integração com Leaflet + clustering
 *
 * REFATORAÇÃO:
 * - Lógica de dados isolada (useThreatData)
 * - Marcadores em componente separado
 * - Filtros em componente separado
 * - Utils isolados
 * - CSS Modules
 * - Design tokens
 *
 * Antes: 621 linhas | Depois: ~150 linhas
 */

import React, { useState, lazy, Suspense } from 'react';
import 'leaflet/dist/leaflet.css';
import { MapContainer, TileLayer } from 'react-leaflet';
import { Card, Badge, LoadingSpinner } from '../../shared';
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
      headerActions={
        <button
          className={styles.refreshButton}
          onClick={refresh}
          disabled={loading}
          title="Atualizar"
        >
          <i className={`fas fa-sync ${loading ? 'fa-spin' : ''}`}></i>
        </button>
      }
    >
      <div className={styles.container}>
        {/* Filters */}
        <ThreatFilters filters={filters} onFiltersChange={setFilters} />

        {/* Map Container */}
        <div className={styles.mapWrapper}>
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
        </div>

        {/* Stats Bar */}
        <div className={styles.statsBar}>
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
        </div>

        {/* Selected Threat Details */}
        {selectedThreat && (
          <div className={styles.threatDetails}>
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
          </div>
        )}
      </div>
    </Card>
  );
};

export default ThreatMap;
