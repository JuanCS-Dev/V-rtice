import React, { useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';

/**
 * MapInitializer - Garante que o mapa inicializa corretamente
 */
const MapInitializer = ({ center, zoom }) => {
  const map = useMap();

  useEffect(() => {
    if (map) {
      // Force invalidate size para garantir renderização
      setTimeout(() => {
        map.invalidateSize();
        map.setView(center, zoom);
      }, 100);
    }
  }, [map, center, zoom]);

  return null;
};

/**
 * MapWrapper - Wrapper que garante tiles apareçam
 */
export const MapWrapper = ({
  children,
  center,
  zoom,
  className,
  ...props
}) => {
  return (
    <MapContainer
      center={center}
      zoom={zoom}
      className={className}
      scrollWheelZoom={true}
      zoomControl={false}
      whenCreated={(mapInstance) => {
        // Force tile load
        setTimeout(() => {
          mapInstance.invalidateSize();
        }, 100);
      }}
      {...props}
    >
      {/* TileLayer SEMPRE PRIMEIRO */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={19}
        minZoom={3}
      />

      <MapInitializer center={center} zoom={zoom} />

      {children}
    </MapContainer>
  );
};

export default MapWrapper;
