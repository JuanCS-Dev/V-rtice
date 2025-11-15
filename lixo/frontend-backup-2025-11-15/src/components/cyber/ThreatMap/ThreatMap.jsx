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

import React, { useState, useMemo, lazy, Suspense } from "react";
import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer } from "react-leaflet";
import {
  formatDateTime,
  formatDate,
  formatTime,
  getTimestamp,
} from "@/utils/dateHelpers";
import { Card, Badge, LoadingSpinner } from "../../shared";
import AskMaximusButton from "../../shared/AskMaximusButton";
import { ThreatFilters } from "./components/ThreatFilters";
import { useThreatData } from "./hooks/useThreatData";
import styles from "./ThreatMap.module.css";

// OTIMIZADO: Lazy load apenas dos componentes pesados
const ThreatMarkers = lazy(() => import("./components/ThreatMarkers"));

export const ThreatMap = () => {
  const { threats, loading, error, filters, setFilters, refresh } =
    useThreatData();
  const [selectedThreat, setSelectedThreat] = useState(null);

  // GAP #31 FIX: Use useMemo to cache filtered results
  // Boris Cherny Standard: Without memoization, filtering 1000 threats 4 times
  // per render = 4000 iterations. With useMemo, only recalculates when threats change
  const severityCounts = useMemo(() => {
    const counts = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      total: threats.length,
    };
    threats.forEach((t) => {
      if (counts[t.severity] !== undefined) {
        counts[t.severity]++;
      }
    });
    return counts;
  }, [threats]);

  const handleThreatClick = (threat) => {
    setSelectedThreat(threat);
  };

  return (
    <Card
      title="CYBER THREAT MAP"
      badge={`${severityCounts.total} THREATS`}
      variant="cyber"
      className={styles.widget}
      data-maximus-tool="threat-map"
      data-maximus-category="shared"
      data-maximus-status={loading ? "loading" : "ready"}
      headerActions={
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <AskMaximusButton
            context={{
              type: "threat_map",
              data: threats,
              count: severityCounts.total,
              filters,
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
            <i className={`fas fa-sync ${loading ? "fa-spin" : ""}`}></i>
          </button>
        </div>
      }
    >
      <div className={styles.container}>
        {/* Filters */}
        <section
          role="region"
          aria-label="Threat filters"
          data-maximus-section="filters"
        >
          <ThreatFilters filters={filters} onFiltersChange={setFilters} />
        </section>

        {/* Map Container */}
        <section
          className={styles.mapWrapper}
          role="region"
          aria-label="Threat map visualization"
          data-maximus-section="map"
        >
          {loading && (
            <div className={styles.loadingOverlay}>
              <LoadingSpinner
                variant="cyber"
                size="lg"
                text="Carregando ameaças..."
              />
            </div>
          )}

          {error && (
            <div className={styles.errorOverlay}>
              <i className="fas fa-exclamation-triangle" aria-hidden="true"></i>
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
              <ThreatMarkers
                threats={threats}
                onThreatClick={handleThreatClick}
              />
            </Suspense>
          </MapContainer>
        </section>

        {/* Stats Bar */}
        <section
          className={styles.statsBar}
          role="region"
          aria-label="Threat statistics"
          data-maximus-section="stats"
        >
          <div className={styles.stat}>
            <span className={styles.statLabel}>TOTAL:</span>
            <span className={styles.statValue}>{severityCounts.total}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>CRITICAL:</span>
            <Badge variant="critical" size="sm">
              {severityCounts.critical}
            </Badge>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>HIGH:</span>
            <Badge variant="high" size="sm">
              {severityCounts.high}
            </Badge>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>MEDIUM:</span>
            <Badge variant="medium" size="sm">
              {severityCounts.medium}
            </Badge>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>LOW:</span>
            <Badge variant="low" size="sm">
              {severityCounts.low}
            </Badge>
          </div>
        </section>

        {/* Selected Threat Details */}
        {selectedThreat && (
          <section
            className={styles.threatDetails}
            role="region"
            aria-label="Selected threat details"
            data-maximus-section="threat-details"
          >
            <div className={styles.detailsHeader}>
              <h6 className={styles.detailsTitle}>
                {selectedThreat.type.toUpperCase()}
              </h6>
              <button
                className={styles.closeButton}
                onClick={() => setSelectedThreat(null)}
              >
                <i className="fas fa-times" aria-hidden="true"></i>
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
                <span className={styles.detailValue}>
                  {selectedThreat.source}
                </span>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Location:</span>
                <span className={styles.detailValue}>
                  {selectedThreat.lat.toFixed(4)},{" "}
                  {selectedThreat.lng.toFixed(4)}
                </span>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Time:</span>
                <span className={styles.detailValue}>
                  {formatDateTime(selectedThreat.timestamp)}
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
