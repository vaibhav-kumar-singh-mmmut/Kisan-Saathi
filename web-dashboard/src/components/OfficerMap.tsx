import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Popup, CircleMarker, Circle, LayersControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icons in React Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface ZoneFeature {
  type: string;
  geometry: { type: string; coordinates: [number, number] };
  properties: {
    id: string;
    name: string;
    color: string;
    score: number;
    report_count: number;
  };
}

export default function OfficerMap() {
  const [features, setFeatures] = useState<ZoneFeature[]>([]);
  const [cropFeatures, setCropFeatures] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const apiBase = import.meta.env.VITE_API_URL ?? '';

  useEffect(() => {
    const fetchMapData = async () => {
      try {
        // Request fresh auth token seamlessly
        const reqRes = await fetch(`${apiBase}/api/v1/auth/otp/request`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone: '+919001000001' })
        });
        const reqData = await reqRes.json();
        
        let token = localStorage.getItem('officer_token');
        if (reqData.dev_code) {
          const verifyRes = await fetch(`${apiBase}/api/v1/auth/otp/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: '+919001000001', code: reqData.dev_code })
          });
          const verifyData = await verifyRes.json();
          if (verifyData.access_token) {
            token = verifyData.access_token;
            localStorage.setItem('officer_token', token!);
          }
        }

        const res = await fetch(`${apiBase}/api/v1/map/hotspots`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        if (!res.ok) {
          throw new Error('Failed to fetch map data');
        }

        const data = await res.json();
        setFeatures(data.features || []);

        // Also fetch crops if available
        const cropRes = await fetch(`${apiBase}/api/v1/agristack/catalogue?synced_only=true`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        if (cropRes.ok) {
          const cropData = await cropRes.json();
          setCropFeatures(cropData || []);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMapData();
  }, [apiBase]);

  if (loading) return <div style={{ color: '#38bdf8', padding: '20px' }}>Loading Hotspots...</div>;
  if (error) return <div style={{ color: '#f43f5e', padding: '20px' }}>⚠️ {error}</div>;

  const center: [number, number] = [26.8106, 83.5232];

  const getColorHex = (color: string) => {
    if (color === 'red') return '#f43f5e';
    if (color === 'orange') return '#f59e0b';
    if (color === 'incoming_risk') return '#a855f7';
    return '#10b981';
  };

  return (
    <div style={{ height: '500px', width: '100%', borderRadius: '12px', overflow: 'hidden', border: '1px solid #1e293b' }}>
      <MapContainer center={center} zoom={8} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />
        <LayersControl position="topright">
          <LayersControl.Overlay name="Disease Hotspots" checked>
            <React.Fragment>
              {features.map((f) => {
                const [lon, lat] = f.geometry.coordinates;
                const { name, color, score, report_count } = f.properties;
                const colorHex = getColorHex(color);
                
                return (
                  <React.Fragment key={f.properties.id}>
                    <CircleMarker
                      center={[lat, lon]}
                      radius={color === 'red' ? 12 : 9}
                      pathOptions={{
                        fillColor: colorHex,
                        fillOpacity: 0.85,
                        color: '#ffffff',
                        weight: 2
                      }}
                    >
                      <Popup>
                        <strong style={{ fontSize: '0.95rem' }}>{name}</strong><br />
                        Status: <strong>{color.toUpperCase()}</strong><br />
                        Risk Score: <strong>{score.toFixed(1)}/100</strong><br />
                        Reports: {report_count}
                      </Popup>
                    </CircleMarker>

                    {color === 'red' && (
                      <Circle
                        center={[lat, lon]}
                        pathOptions={{
                          fillColor: colorHex,
                          fillOpacity: 0.08,
                          color: colorHex,
                          weight: 1.5,
                          dashArray: '6, 6'
                        }}
                        radius={10000}
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </React.Fragment>
          </LayersControl.Overlay>

          <LayersControl.Overlay name="AgriStack Crop Catalogue" checked>
            <React.Fragment>
              {cropFeatures.map((c) => {
                if (!c.lat || !c.lon) return null;
                const lat = parseFloat(c.lat);
                const lon = parseFloat(c.lon);
                // A distinct green color for crops
                const cropColor = '#84cc16';
                return (
                  <CircleMarker
                    key={c.id}
                    center={[lat, lon]}
                    radius={7}
                    pathOptions={{
                      fillColor: cropColor,
                      fillOpacity: 0.9,
                      color: '#ffffff',
                      weight: 1.5
                    }}
                  >
                    <Popup>
                      <strong style={{ fontSize: '0.95rem', color: '#16a34a' }}>🌾 {c.crop_name}</strong><br />
                      Farmer: {c.farmer_name}<br />
                      Area: {c.acreage_ha} ha<br />
                      Village: {c.village_name}<br />
                      <small style={{ color: '#64748b' }}>Synced from UP-AgriStack</small>
                    </Popup>
                  </CircleMarker>
                );
              })}
            </React.Fragment>
          </LayersControl.Overlay>
        </LayersControl>
      </MapContainer>
    </div>
  );
}
