import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const apiBase = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

  useEffect(() => {
    const fetchMapData = async () => {
      try {
        let token = localStorage.getItem('token');
        
        // Auto-login for testing if no token exists
        if (!token) {
          try {
            console.log('No token found, attempting auto-login as test officer...');
            const reqRes = await fetch(`${apiBase}/api/v1/auth/otp/request`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ phone: '+919001000001' })
            });
            const reqData = await reqRes.json();
            if (reqData.dev_code) {
              const verifyRes = await fetch(`${apiBase}/api/v1/auth/otp/verify`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: '+919001000001', code: reqData.dev_code })
              });
              const verifyData = await verifyRes.json();
              if (verifyData.access_token) {
                token = verifyData.access_token;
                localStorage.setItem('token', token!);
                console.log('Auto-login successful!');
                window.location.reload();
                return;
              }
            }
          } catch (e) {
            console.error('Auto login failed', e);
          }
        }

        if (!token) {
          setError('No auth token found. Auto-login failed. Please ensure the backend is running with DEV_RETURN_OTP=True.');
          setLoading(false);
          return;
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
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMapData();
  }, [apiBase]);

  if (loading) return <div>Loading Hotspots...</div>;
  if (error) return <div style={{ color: 'var(--color-danger)' }}>{error}</div>;

  // Default center of UP (Lucknow approx)
  const center: [number, number] = [26.8467, 80.9462];

  const getColorHex = (color: string) => {
    if (color === 'red') return '#ff4d4d';
    if (color === 'orange') return '#ffa64d';
    if (color === 'incoming_risk') return '#cc00ff';
    return '#4dff4d';
  };

  return (
    <div style={{ height: '500px', width: '100%', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
      <MapContainer center={center} zoom={7} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {features.map((f, i) => {
          const [lon, lat] = f.geometry.coordinates;
          const { name, color, score, report_count } = f.properties;
          
          return (
            <React.Fragment key={f.properties.id}>
              {/* Main marker */}
              <Circle
                center={[lat, lon]}
                pathOptions={{
                  fillColor: getColorHex(color),
                  fillOpacity: 0.7,
                  color: getColorHex(color),
                  weight: 2
                }}
                radius={3000} // 3km circle
              >
                <Popup>
                  <strong>{name}</strong><br />
                  Status: {color.toUpperCase()}<br />
                  Risk Score: {score.toFixed(1)}<br />
                  Reports: {report_count}
                </Popup>
              </Circle>

              {/* Show an incoming risk ring for red zones (simulating 10km spread) */}
              {color === 'red' && (
                <Circle
                  center={[lat, lon]}
                  pathOptions={{
                    fillColor: 'transparent',
                    color: '#ff4d4d',
                    weight: 1,
                    dashArray: '5, 5'
                  }}
                  radius={10000} // 10km spread radius
                />
              )}
            </React.Fragment>
          );
        })}
      </MapContainer>
    </div>
  );
}
