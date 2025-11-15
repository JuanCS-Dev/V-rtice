/**
import logger from '@/utils/logger';
 * MapPanel - NOVO - Simples, Direto, Funcional
 *
 * Usa Leaflet puro (sem React-Leaflet) para máximo controle
 * Focado em FUNCIONAR, não em ser "elegante"
 */

import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix ícone padrão Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
});

const MapPanel = ({ dossierData }) => {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const [loading, setLoading] = useState(true);

  // Criar mapa na montagem
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    logger.debug("[MAP] 🗺️ Criando mapa...");

    try {
      // Criar instância do mapa
      const map = L.map(mapContainerRef.current, {
        center: [-15.7801, -47.9292], // Brasília - Centro do Brasil
        zoom: 4,
        zoomControl: true,
        scrollWheelZoom: true,
        attributionControl: true,
      });

      // Adicionar tiles - OpenStreetMap (mais confiável)
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19,
        minZoom: 3,
      }).addTo(map);

      // Aguardar mapa ficar pronto
      map.whenReady(() => {
        logger.debug("[MAP] ✅ Mapa pronto!");
        setTimeout(() => {
          map.invalidateSize();
          setLoading(false);
        }, 200);
      });

      mapRef.current = map;

      // Eventos de debug
      map.on("load", () => logger.debug("[MAP] 📍 Tiles carregados"));
      map.on("zoomend", () => logger.debug("[MAP] 🔍 Zoom:", map.getZoom()));
    } catch (error) {
      logger.error("[MAP] ❌ Erro ao criar mapa:", error);
      setLoading(false);
    }

    // Cleanup
    return () => {
      logger.debug("[MAP] 🧹 Limpando mapa...");
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Atualizar marcador quando dossier mudar
  useEffect(() => {
    if (!mapRef.current || !dossierData?.lastKnownLocation) return;

    const { lat, lng } = dossierData.lastKnownLocation;

    logger.debug("[MAP] 📍 Movendo para:", lat, lng);

    // Remover marcador antigo
    if (markerRef.current) {
      mapRef.current.removeLayer(markerRef.current);
    }

    // Criar marcador customizado
    const carIcon = L.divIcon({
      html: `
        <div style="
          position: relative;
          width: 40px;
          height: 40px;
        ">
          <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #00ff41;
            border: 3px solid #000;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            box-shadow: 0 0 20px rgba(0, 255, 65, 0.6);
            animation: pulse 2s infinite;
          ">🚗</div>
          <style>
            @keyframes pulse {
              0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 65, 0.6); }
              50% { box-shadow: 0 0 30px rgba(0, 255, 65, 0.9); }
            }
          </style>
        </div>
      `,
      className: "",
      iconSize: [40, 40],
      iconAnchor: [20, 20],
    });

    // Adicionar novo marcador
    const marker = L.marker([lat, lng], { icon: carIcon }).addTo(
      mapRef.current,
    );

    // Popup
    marker
      .bindPopup(
        `
      <div style="font-family: monospace; min-width: 200px;">
        <h3 style="margin: 0 0 10px; color: #00ff41; border-bottom: 2px solid #00ff41; padding-bottom: 5px;">
          🚗 VEÍCULO LOCALIZADO
        </h3>
        <div style="color: #333;">
          <p style="margin: 5px 0;"><strong>Placa:</strong> ${dossierData.placa || "N/A"}</p>
          <p style="margin: 5px 0;"><strong>Modelo:</strong> ${dossierData.modelo || "N/A"}</p>
          <p style="margin: 5px 0;"><strong>Cor:</strong> ${dossierData.cor || "N/A"}</p>
          <p style="margin: 5px 0;"><strong>Lat:</strong> ${lat.toFixed(6)}</p>
          <p style="margin: 5px 0;"><strong>Lng:</strong> ${lng.toFixed(6)}</p>
        </div>
      </div>
    `,
      )
      .openPopup();

    markerRef.current = marker;

    // Mover mapa com animação
    mapRef.current.flyTo([lat, lng], 15, {
      duration: 1.5,
      easeLinearity: 0.5,
    });
  }, [dossierData]);

  return (
    <div className="flex-1 relative">
      {/* Container do Mapa */}
      <div
        ref={mapContainerRef}
        className="absolute inset-0"
        style={{
          backgroundColor: "#1a1a1a",
          minHeight: "100%",
        }}
      />

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[1000]">
          <div className="text-center">
            <div className="w-20 h-20 border-4 border-green-400 border-t-transparent rounded-full animate-spin mb-4"></div>
            <p className="text-green-400 font-bold text-lg tracking-wider">
              CARREGANDO MAPA...
            </p>
            <p className="text-green-400/60 text-sm mt-2">
              Inicializando Leaflet
            </p>
          </div>
        </div>
      )}

      {/* Info Overlay - Top Left */}
      <div className="absolute top-4 left-4 z-[999] bg-black/80 backdrop-blur-sm border border-green-400/30 rounded-lg p-3 max-w-xs">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-green-400 font-bold text-sm tracking-wider">
            MAPA TÁTICO
          </span>
        </div>
        <p className="text-green-400/70 text-xs">
          {dossierData
            ? `Rastreando: ${dossierData.placa || "N/A"}`
            : "Aguardando consulta..."}
        </p>
      </div>

      {/* Instruções - Bottom Left */}
      {!dossierData && (
        <div className="absolute bottom-4 left-4 z-[999] bg-black/80 backdrop-blur-sm border border-green-400/30 rounded-lg p-3 max-w-xs">
          <p className="text-green-400/70 text-xs">
            💡 <strong>Dica:</strong> Digite uma placa e clique em "EXECUTAR
            CONSULTA" para localizar o veículo no mapa.
          </p>
        </div>
      )}
    </div>
  );
};

export default MapPanel;
