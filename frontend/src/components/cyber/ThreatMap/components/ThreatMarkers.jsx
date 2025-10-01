import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import { getThreatColor, getThreatIcon } from '../utils/threatUtils';

const createThreatIcon = (severity, type, pulse = false) => {
  const color = getThreatColor(severity);
  const icon = getThreatIcon(type);
  const pulseHtml = pulse ? `<div class="pulse-ring" style="border-color: ${color};"></div>` : '';

  return L.divIcon({
    html: `
      <div class="cyber-threat-marker" style="opacity: 1;">
        <div class="threat-icon" style="background-color: ${color}; border-color: ${color}; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid;">
          <span style="font-size: 12px;">${icon}</span>
        </div>
        ${pulseHtml}
      </div>
    `,
    className: 'custom-threat-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
  });
};

const ThreatMarkers = ({ threats, onThreatClick }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || threats.length === 0) return;

    const threatClusterGroup = L.markerClusterGroup({
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
            <div style="background: radial-gradient(circle, ${color}, transparent); width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 50%;">
              <span style="color: white; font-weight: bold; font-family: monospace;">${count}</span>
            </div>
          `,
          className: `marker-cluster marker-cluster-${size}`,
          iconSize: new L.Point(40, 40)
        });
      }
    });

    threats.forEach((threat) => {
      if (typeof threat.lat === 'number' && typeof threat.lng === 'number') {
        const icon = createThreatIcon(threat.severity, threat.type, threat.severity === 'critical');
        const marker = L.marker([threat.lat, threat.lng], { icon });

        // Popup com DADOS REAIS dos serviços
        const popupContent = `
          <div style="font-family: monospace; min-width: 250px; padding: 4px;">
            <strong style="color: ${getThreatColor(threat.severity)}; font-size: 14px;">${threat.type.toUpperCase()}</strong><br/>
            <hr style="margin: 4px 0; border-color: ${getThreatColor(threat.severity)}30;"/>

            <small style="display: block; margin-top: 4px;"><b>IP:</b> ${threat.source}</small>
            <small style="display: block;"><b>Severity:</b> <span style="color: ${getThreatColor(threat.severity)};">${threat.severity.toUpperCase()}</span></small>

            ${threat.country ? `<small style="display: block;"><b>Location:</b> ${threat.city || 'Unknown'}, ${threat.country}</small>` : ''}
            ${threat.isp ? `<small style="display: block;"><b>ISP:</b> ${threat.isp}</small>` : ''}
            ${threat.asn ? `<small style="display: block;"><b>ASN:</b> ${threat.asn}</small>` : ''}

            ${threat.threatScore !== undefined ? `
              <hr style="margin: 4px 0; border-color: #333;"/>
              <small style="display: block;"><b>Threat Score:</b> <span style="color: ${threat.threatScore > 60 ? '#ff3366' : '#00ff88'};">${threat.threatScore}/100</span></small>
              <small style="display: block;"><b>Status:</b> ${threat.isMalicious ? '<span style="color: #ff3366;">⚠️ MALICIOUS</span>' : '<span style="color: #00ff88;">✓ CLEAN</span>'}</small>
              <small style="display: block;"><b>Confidence:</b> ${threat.confidence?.toUpperCase() || 'UNKNOWN'}</small>
            ` : ''}

            <hr style="margin: 4px 0; border-color: #333;"/>
            <small style="display: block; color: #888;">${new Date(threat.timestamp).toLocaleString()}</small>
          </div>
        `;

        marker.bindPopup(popupContent);
        marker.on('click', () => onThreatClick && onThreatClick(threat));
        threatClusterGroup.addLayer(marker);
      }
    });

    map.addLayer(threatClusterGroup);

    return () => {
      map.removeLayer(threatClusterGroup);
    };
  }, [map, threats, onThreatClick]);

  return null;
};

export default React.memo(ThreatMarkers);
