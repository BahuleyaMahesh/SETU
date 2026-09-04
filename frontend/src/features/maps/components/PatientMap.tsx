import React, { useEffect, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useTheme } from '../../../app/theme/ThemeProvider';

export interface MapMarker {
  id: string;
  lat: number;
  lng: number;
  label: string;
  sublabel?: string;
  color?: string; // e.g. '#ef4444' for critical, '#3b82f6' for a hospital
}

interface PatientMapProps {
  markers: MapMarker[];
  height?: string;
  zoom?: number;
  /** Called with (lat, lng) when the map is clicked — used for "click to pin a location" flows. */
  onMapClick?: (lat: number, lng: number) => void;
  className?: string;
}

const LIGHT_STYLE = 'https://tiles.openfreemap.org/styles/liberty';
const DARK_STYLE = 'https://tiles.openfreemap.org/styles/dark';
const DEFAULT_CENTER: [number, number] = [77.5946, 12.9716]; // Bangalore fallback

export const PatientMap: React.FC<PatientMapProps> = ({
  markers,
  height = '500px',
  zoom = 10,
  onMapClick,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerObjsRef = useRef<maplibregl.Marker[]>([]);
  const onMapClickRef = useRef(onMapClick);
  onMapClickRef.current = onMapClick;
  const { theme } = useTheme();

  // Create the map once.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const first = markers.find((m) => m.lat && m.lng);
    const center: [number, number] = first ? [first.lng, first.lat] : DEFAULT_CENTER;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: theme === 'dark' ? DARK_STYLE : LIGHT_STYLE,
      center,
      zoom,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.on('click', (e) => {
      onMapClickRef.current?.(e.lngLat.lat, e.lngLat.lng);
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Swap the base style when the app's light/dark theme changes.
  useEffect(() => {
    if (!mapRef.current) return;
    mapRef.current.setStyle(theme === 'dark' ? DARK_STYLE : LIGHT_STYLE);
  }, [theme]);

  // Redraw markers whenever the marker list changes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    markerObjsRef.current.forEach((m) => m.remove());
    markerObjsRef.current = [];

    const valid = markers.filter((m) => m.lat != null && m.lng != null);

    valid.forEach((m) => {
      const popup = new maplibregl.Popup({ offset: 20 }).setHTML(
        `<div style="font-size:13px;font-weight:600;">${escapeHtml(m.label)}</div>` +
          (m.sublabel ? `<div style="font-size:12px;color:#64748b;">${escapeHtml(m.sublabel)}</div>` : '')
      );
      const marker = new maplibregl.Marker({ color: m.color || '#0284c7' })
        .setLngLat([m.lng, m.lat])
        .setPopup(popup)
        .addTo(map);
      markerObjsRef.current.push(marker);
    });

    if (valid.length > 1) {
      const bounds = new maplibregl.LngLatBounds();
      valid.forEach((m) => bounds.extend([m.lng, m.lat]));
      map.fitBounds(bounds, { padding: 60, maxZoom: 14 });
    } else if (valid.length === 1) {
      map.flyTo({ center: [valid[0].lng, valid[0].lat], zoom });
    }
  }, [markers]);

  return <div ref={containerRef} className={`w-full rounded-lg overflow-hidden ${className}`} style={{ height }} />;
};

function escapeHtml(s: string): string {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

export default PatientMap;
