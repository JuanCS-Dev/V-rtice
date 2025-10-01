import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.markercluster';
import HeatmapLayer from '../HeatmapLayer'; // Assuming HeatmapLayer is in the parent directory
import styles from './MapLayers.module.css';

// --- Helper Functions and Icons ---
const getRiskColor = (riskLevel) => {
  const colors = {
    'Crítico': '#ff0040',
    'Alto': '#ff4000',
    'Médio': '#ffaa00',
    'Baixo': '#00aa00',
    'Mínimo': '#00aaff'
  };
  return colors[riskLevel] || '#00aaff';
};

const createIcon = (color, pulse = false, opacity = 1, size = 16) => {
  const pulseHtml = pulse ? `<div class="pulse-ring" style="border-color: ${color};"></div>` : '';
  return L.divIcon({
    html: `
      <div class="cyber-marker" style="opacity: ${opacity};">
        <div class="marker-core" style="background-color: ${color}; width: ${size-4}px; height: ${size-4}px;"></div>
        ${pulseHtml}
      </div>
    `,
    className: 'custom-cyber-marker',
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
    popupAnchor: [0, -size/2]
  });
};

const createHotspotIcon = (riskLevel) => createIcon(getRiskColor(riskLevel), true, 1, 20);

// --- ClusteredOccurrenceMarkers Component ---
const ClusteredOccurrenceMarkers = React.memo(({ data }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || data.length === 0) return;

    const markerClusterGroup = L.markerClusterGroup({
      chunkedLoading: true,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      maxClusterRadius: 50,
      disableClusteringAtZoom: 16,
      iconCreateFunction: function(cluster) {
        const count = cluster.getChildCount();
        let size = count < 10 ? 'small' : count < 100 ? 'medium' : 'large';
        let color = count < 10 ? '#00aaff' : count < 100 ? '#ffaa00' : '#ff4000';

        return new L.DivIcon({
          html: `
            <div class="cluster-inner cyber-cluster-${size}" style="background: radial-gradient(circle, ${color}, transparent);">
              <span class="cluster-count">${count}</span>
            </div>
          `,
          className: `marker-cluster marker-cluster-${size}`,
          iconSize: new L.Point(40, 40)
        });
      }
    });

    const occurrenceIcon = createIcon('rgba(255, 0, 0, 0.8)', false, 1);

    data.forEach((point) => {
      if (typeof point.lat === 'number' && typeof point.lng === 'number') {
        const marker = L.marker([point.lat, point.lng], { icon: occurrenceIcon });
        marker.bindPopup(`
          <div class="${styles.popupContent}">
            <div class="${styles.popupHeader}">OCORRÊNCIA</div>
            <div class="${styles.coordLine}"><span class="${styles.label}">TIPO:</span><span class="${styles.value}">${point.tipo || 'N/A'}</span></div>
            <div class="${styles.coordLine}"><span class="${styles.label}">DATA:</span><span class="${styles.value}">${point.timestamp ? new Date(point.timestamp).toLocaleDateString('pt-BR') : 'N/A'}</span></div>
          </div>
        `);
        markerClusterGroup.addLayer(marker);
      }
    });

    map.addLayer(markerClusterGroup);

    return () => map.removeLayer(markerClusterGroup);
  }, [map, data]);

  return null;
});

// --- PredictiveHotspots Component ---
const PredictiveHotspots = React.memo(({ hotspots }) => {
  const map = useMap();

  useEffect(() => {
    const hotspotsGroup = L.layerGroup();

    hotspots.forEach((hotspot, index) => {
      const { center_lat: lat, center_lng: lng } = hotspot;
      if (typeof lat === 'number' && typeof lng === 'number') {
        const icon = createHotspotIcon(hotspot.risk_level);
        const marker = L.marker([lat, lng], { icon });
        hotspotsGroup.addLayer(marker);
      }
    });

    map.addLayer(hotspotsGroup);

    return () => map.removeLayer(hotspotsGroup);
  }, [map, hotspots]);

  return null;
});

// --- VehicleMarker Component ---
const VehicleMarker = React.memo(({ dossierData }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || !dossierData || !dossierData.lastKnownLocation) return;

    const { lat, lng } = dossierData.lastKnownLocation;
    const riskColor = dossierData.riskLevel === 'HIGH' ? '#ff0040' : '#ffaa00';

    const vehicleIcon = L.divIcon({
      html: `<div class="vehicle-marker" style="background-color: ${riskColor};">🚗</div>`,
      className: 'custom-vehicle-marker',
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    });

    const marker = L.marker([lat, lng], { icon: vehicleIcon });
    marker.addTo(map);

    return () => map.removeLayer(marker);
  }, [map, dossierData]);

  return null;
});

// --- MapUpdater Component ---
const MapUpdater = ({ dossierData }) => {
    const map = useMap();
  
    useEffect(() => {
      if (dossierData && dossierData.lastKnownLocation) {
        const { lat, lng } = dossierData.lastKnownLocation;
        map.flyTo([lat, lng], 15, { duration: 1.5 });
      }
    }, [dossierData, map]);
  
    return null;
  };

/**
 * Renders all map layers based on visibility flags and data.
 */
const MapLayers = ({
  heatmapVisible,
  occurrenceData,
  showOccurrenceMarkers,
  showPredictiveHotspots,
  predictedHotspots,
  dossierData
}) => {
  return (
    <>
      {heatmapVisible && <HeatmapLayer points={occurrenceData} />}
      {showOccurrenceMarkers && <ClusteredOccurrenceMarkers data={occurrenceData} />}
      {showPredictiveHotspots && <PredictiveHotspots hotspots={predictedHotspots} />}
      <MapUpdater dossierData={dossierData} />
      <VehicleMarker dossierData={dossierData} />
    </>
  );
};

export default React.memo(MapLayers);
