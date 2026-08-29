import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Popup, Circle, CircleMarker, useMap } from 'react-leaflet';
import { useAuth } from '../contexts/AuthContext';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default Leaflet marker assets
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

interface VillageData {
  id: string;
  name: string;
  jurisdiction_type: string;
  parent_id?: string;
  lat?: number;
  lon?: number;
}

interface ExpertItem {
  id: string;
  disease_id: string;
  confidence_score: number;
  image_url?: string;
  status: string;
  reported_at: string;
  jurisdiction_id: string;
}

interface WeatherDetail {
  temperature_c: number;
  humidity_pct: number;
  rainfall_mm: number;
  alerts: string[];
}

function MapFlyTo({ center }: { center: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, 12, { duration: 1.2 });
    }
  }, [center, map]);
  return null;
}

export default function OfficerDashboard() {
  const { user, token, logout } = useAuth();
  const apiBase = import.meta.env.VITE_API_URL ?? '';
  const [activeTab, setActiveTab] = useState<'map' | 'villages' | 'expert' | 'drone' | 'subsidy' | 'agristack'>('map');
  const [features, setFeatures] = useState<ZoneFeature[]>([]);
  const [villages, setVillages] = useState<VillageData[]>([]);
  const [expertQueue, setExpertQueue] = useState<ExpertItem[]>([]);
  const [subsidyFlags, setSubsidyFlags] = useState<any[]>([]);
  const [cropCatalogue, setCropCatalogue] = useState<any[]>([]);
  const [cropDiscrepancies, setCropDiscrepancies] = useState<any[]>([]);
  const [subsidyLoading, setSubsidyLoading] = useState(false);
  const [agriStackLoading, setAgriStackLoading] = useState(false);
  
  // Discrepancy Form State
  const [discVillage, setDiscVillage] = useState<string>('');
  const [discFarmer, setDiscFarmer] = useState<string>('');
  const [discSurvey, setDiscSurvey] = useState<string>('');
  const [discReportedCrop, setDiscReportedCrop] = useState<string>('Wheat');
  const [discActualCrop, setDiscActualCrop] = useState<string>('Mustard');
  const [discReportedArea, setDiscReportedArea] = useState<number>(2.5);
  const [discActualArea, setDiscActualArea] = useState<number>(2.0);
  const [discType, setDiscType] = useState<string>('crop_mismatch');
  const [discNotes, setDiscNotes] = useState<string>('');

  // WDRA Post-Harvest Storage State
  const [storageVillageId, setStorageVillageId] = useState<string>('');
  const [storageData, setStorageData] = useState<any | null>(null);
  const [storageLoading, setStorageLoading] = useState<boolean>(false);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedVillage, setSelectedVillage] = useState<ZoneFeature['properties'] | null>(null);
  const [villageWeather, setVillageWeather] = useState<WeatherDetail | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [flyCenter, setFlyCenter] = useState<[number, number] | null>(null);

  const [zoneFilter, setZoneFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [syncStatus, setSyncStatus] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [mapProvider, setMapProvider] = useState<'carto' | 'satellite' | 'osm' | 'mappls'>('carto');
  const mapplsApiKey = import.meta.env.VITE_MAPPLS_API_KEY || 'pymtuxcnlbhriijumnxhvytnknzbodsyqjvd';

  // Authenticate and fetch data
  const loadDashboardData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (!token) {
        throw new Error('Authentication token is missing.');
      }

      // 2. Fetch Map Hotspots
      const mapRes = await fetch(`${apiBase}/api/v1/map/hotspots`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (mapRes.ok) {
        const mapData = await mapRes.json();
        setFeatures(mapData.features || []);
      } else {
        throw new Error('Map service responded with an error.');
      }

      // 3. Fetch Scoped Villages
      const vilRes = await fetch(`${apiBase}/api/v1/dashboard/villages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (vilRes.ok) {
        const vilData = await vilRes.json();
        setVillages(vilData || []);
      }

      // 4. Fetch Expert Validation Queue
      const expRes = await fetch(`${apiBase}/api/v1/expert-queue`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (expRes.ok) {
        const expData = await expRes.json();
        setExpertQueue(expData || []);
      }

      // 5. Fetch AgriStack Crop Catalogue
      const catRes = await fetch(`${apiBase}/api/v1/agristack/catalogue`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (catRes.ok) {
        const catData = await catRes.json();
        setCropCatalogue(catData || []);
      }

      // 6. Fetch Statutory Crop Discrepancies
      const discRes = await fetch(`${apiBase}/api/v1/agristack/discrepancies`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (discRes.ok) {
        const discData = await discRes.json();
        setCropDiscrepancies(discData || []);
      }
    } catch (err: any) {
      console.error('Officer Dashboard load error:', err);
      setError(err.message || 'Failed to load surveillance data');
    } finally {
      setLoading(false);
    }
  }, [apiBase, token]);

  useEffect(() => {
    if (token) {
      loadDashboardData();
    }
  }, [loadDashboardData, token]);

  // Load weather when village selected
  const handleSelectVillage = async (props: ZoneFeature['properties'], coords?: [number, number]) => {
    setSelectedVillage(props);
    if (coords) {
      setFlyCenter([coords[1], coords[0]]);
    }
    setWeatherLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/weather/${props.id}`);
      if (res.ok) {
        const data = await res.json();
        setVillageWeather(data);
      } else {
        setVillageWeather(null);
      }
    } catch {
      setVillageWeather(null);
    } finally {
      setWeatherLoading(false);
    }
  };

  const handleSyncWeather = async () => {
    setSyncStatus('Syncing Open-Meteo feeds…');
    try {
      const res = await fetch(`${apiBase}/api/v1/weather/sync`, { method: 'POST' });
      if (res.ok) {
        setSyncStatus('Weather data synchronized & risk recalculated!');
        setTimeout(() => setSyncStatus(null), 4000);
        await loadDashboardData();
      }
    } catch (err) {
      console.error('Weather sync error:', err);
      setSyncStatus('Sync failed.');
      setTimeout(() => setSyncStatus(null), 3000);
    }
  };

  const handleRecalculateZones = async () => {
    setSyncStatus('Running Phase 8/10 Zone Scoring Engine…');
    try {
      const res = await fetch(`${apiBase}/api/v1/zones/calculate`, { method: 'POST' });
      if (res.ok) {
        setSyncStatus('Zone risk classification updated!');
        setTimeout(() => setSyncStatus(null), 4000);
        await loadDashboardData();
      }
    } catch (err) {
      console.error('Zone calculate error:', err);
      setSyncStatus('Calculation failed.');
      setTimeout(() => setSyncStatus(null), 3000);
    }
  };

  const handleValidateReport = async (reportId: string, correctedDisease?: string) => {
    try {
      const res = await fetch(`${apiBase}/api/v1/expert-queue/${reportId}/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          corrected_disease_id: correctedDisease || null,
          notes: 'Validated and approved via Officer Portal'
        })
      });
      if (res.ok) {
        setActionNotice(`Report ${reportId.slice(0, 8)} successfully validated!`);
        setTimeout(() => setActionNotice(null), 4000);
        setExpertQueue((prev) => prev.filter((item) => item.id !== reportId));
      }
    } catch (e) {
      console.error('Validation error:', e);
    }
  };

  // Filtered features
  const filteredFeatures = useMemo(() => {
    return features.filter((f) => {
      const matchesZone = zoneFilter === 'all' || f.properties.color === zoneFilter;
      const matchesSearch = searchQuery === '' || f.properties.name.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesZone && matchesSearch;
    });
  }, [features, zoneFilter, searchQuery]);

  // Statistics
  const stats = useMemo(() => {
    const red = features.filter((f) => f.properties.color === 'red').length;
    const orange = features.filter((f) => f.properties.color === 'orange').length;
    const incoming = features.filter((f) => f.properties.color === 'incoming_risk').length;
    const green = features.filter((f) => f.properties.color === 'green').length;
    return { red, orange, incoming, green, totalVillages: features.length };
  }, [features]);

  const getColorHex = (color: string) => {
    switch (color) {
      case 'red': return '#f43f5e';
      case 'orange': return '#f59e0b';
      case 'incoming_risk': return '#a855f7';
      default: return '#10b981';
    }
  };

  const center: [number, number] = [27.5683, 80.6698]; // Sitapur

  return (
    <div className="officer-portal-root" style={{ background: '#0a0d14', minHeight: '100vh', color: '#f1f5f9' }}>
      {/* Top Officer Command Header */}
      <header style={{
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid #1e293b',
        padding: '14px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        position: 'sticky',
        top: 0,
        zIndex: 1000
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.6rem' }}>🛰️</span>
            <div>
              <h1 style={{ fontSize: '1.15rem', fontWeight: 700, letterSpacing: '-0.02em', margin: 0, color: '#f8fafc' }}>
                Kisan Saathi Command Center
              </h1>
              <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600 }}>
                ● {user?.role} • {user?.name}
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={handleSyncWeather}
            style={{
              background: '#0284c7',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 14px',
              fontSize: '0.8rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer'
            }}
          >
            <span>🌦️</span> Sync Open-Meteo
          </button>

          <button
            onClick={handleRecalculateZones}
            style={{
              background: '#7c3aed',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 14px',
              fontSize: '0.8rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer'
            }}
          >
            <span>⚡</span> Recalculate Risk
          </button>

          <button
            onClick={logout}
            style={{
              background: 'transparent',
              color: '#f8fafc',
              border: '1px solid #334155',
              borderRadius: '6px',
              padding: '6px 14px',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Log out
          </button>
        </div>
      </header>

      {/* Notifications / Alerts Bar */}
      {syncStatus && (
        <div style={{ background: '#0369a1', color: '#e0f2fe', padding: '8px 24px', fontSize: '0.82rem', textAlign: 'center', fontWeight: 600 }}>
          ℹ️ {syncStatus}
        </div>
      )}
      {actionNotice && (
        <div style={{ background: '#059669', color: '#ecfdf5', padding: '8px 24px', fontSize: '0.82rem', textAlign: 'center', fontWeight: 600 }}>
          ✅ {actionNotice}
        </div>
      )}

      {/* Main Container */}
      <main style={{ padding: '24px 28px', maxWidth: '1600px', margin: '0 auto' }}>
        {/* KPI Summary Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
          gap: '16px',
          marginBottom: '24px'
        }}>
          <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '12px', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600 }}>ACTIVE RED ZONES</span>
              <span style={{ fontSize: '1.2rem' }}>🔴</span>
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f43f5e', marginTop: '6px' }}>{stats.red}</div>
            <span style={{ fontSize: '0.72rem', color: '#fda4af' }}>Critical Disease Outbreak / Flood Risk</span>
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(168, 85, 247, 0.3)', borderRadius: '12px', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600 }}>INCOMING SPREAD RISKS</span>
              <span style={{ fontSize: '1.2rem' }}>🟣</span>
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#c084fc', marginTop: '6px' }}>{stats.incoming}</div>
            <span style={{ fontSize: '0.72rem', color: '#e9d5ff' }}>Within 10-50km Pathogen Spread Buffer</span>
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '12px', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600 }}>WEATHER RISK (ORANGE)</span>
              <span style={{ fontSize: '1.2rem' }}>🟠</span>
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f59e0b', marginTop: '6px' }}>{stats.orange}</div>
            <span style={{ fontSize: '0.72rem', color: '#fde68a' }}>Open-Meteo Trigger Fired (Preventive)</span>
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '12px', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600 }}>HEALTHY / GREEN</span>
              <span style={{ fontSize: '1.2rem' }}>🟢</span>
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#10b981', marginTop: '6px' }}>{stats.green}</div>
            <span style={{ fontSize: '0.72rem', color: '#a7f3d0' }}>Total Villages Monitored: {stats.totalVillages}</span>
          </div>

          <div style={{ background: 'rgba(30, 41, 59, 0.7)', border: '1px solid #334155', borderRadius: '12px', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600 }}>EXPERT VALIDATION QUEUE</span>
              <span style={{ fontSize: '1.2rem' }}>🔬</span>
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#38bdf8', marginTop: '6px' }}>{expertQueue.length}</div>
            <span style={{ fontSize: '0.72rem', color: '#bae6fd' }}>Scans Requiring Human In Loop</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid #334155',
          marginBottom: '20px'
        }}>
          {[
            { id: 'map', label: '🗺️ Geo Hotspot Radar (Phase 9/10)', count: features.length },
            { id: 'villages', label: '📋 Village Surveillance Matrix', count: villages.length },
            { id: 'expert', label: '🔬 Expert Validation Queue (M5)', count: expertQueue.length },
            { id: 'drone', label: '🚁 Drone Spray Dispatch', count: 3 },
            { id: 'subsidy', label: '🏛️ PMFBY Subsidy Flags', count: subsidyFlags.length },
            { id: 'agristack', label: '🌾 AgriStack & WDRA Storage (Phase 12)', count: cropCatalogue.length },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                background: activeTab === tab.id ? '#1e293b' : 'transparent',
                color: activeTab === tab.id ? '#38bdf8' : '#94a3b8',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid #38bdf8' : '2px solid transparent',
                padding: '10px 20px',
                fontSize: '0.88rem',
                fontWeight: 600,
                cursor: 'pointer',
                borderRadius: '8px 8px 0 0',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span style={{
                  background: activeTab === tab.id ? 'rgba(56, 189, 248, 0.2)' : '#334155',
                  color: activeTab === tab.id ? '#38bdf8' : '#cbd5e1',
                  borderRadius: '999px',
                  padding: '2px 8px',
                  fontSize: '0.72rem'
                }}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* ── TAB 1: GEO HOTSPOT MAP ────────────────────────────────────── */}
        {activeTab === 'map' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '20px' }}>
            {/* Left: Map Container with Filters */}
            <div style={{ background: '#131b2e', borderRadius: '14px', border: '1px solid #1e293b', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              {/* Map Filter Controls Bar */}
              <div style={{ padding: '12px 18px', background: '#1e293b', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>Filter Zone:</span>
                  {(['all', 'red', 'orange', 'incoming_risk', 'green'] as const).map((z) => (
                    <button
                      key={z}
                      onClick={() => setZoneFilter(z)}
                      style={{
                        background: zoneFilter === z ? getColorHex(z === 'all' ? 'green' : z) : '#0f172a',
                        color: zoneFilter === z ? '#000' : '#cbd5e1',
                        border: '1px solid #334155',
                        borderRadius: '6px',
                        padding: '3px 10px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        textTransform: 'uppercase'
                      }}
                    >
                      {z === 'all' ? 'All Zones' : z.replace('_', ' ')}
                    </button>
                  ))}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Map Base:</span>
                  <select
                    value={mapProvider}
                    onChange={(e) => setMapProvider(e.target.value as any)}
                    style={{
                      background: '#0f172a',
                      color: '#38bdf8',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      padding: '4px 8px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="carto">🗺️ CARTO Voyager (Clean HD)</option>
                    <option value="satellite">🛰️ Satellite (Farm Imagery)</option>
                    <option value="osm">🌐 OpenStreetMap</option>
                    <option value="mappls">🇮🇳 Mappls (MapmyIndia)</option>
                  </select>

                  <input
                    type="text"
                    placeholder="Search village name…"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{
                      background: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      padding: '4px 10px',
                      fontSize: '0.78rem',
                      outline: 'none',
                      width: '160px'
                    }}
                  />
                  <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                    Showing {filteredFeatures.length} / {features.length}
                  </span>
                </div>
              </div>

              {/* Map Canvas */}
              <div style={{ height: '620px', width: '100%', position: 'relative' }}>
                {loading ? (
                  <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#38bdf8' }}>
                    🛰️ Loading geospatial surveillance telemetry…
                  </div>
                ) : error ? (
                  <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f43f5e' }}>
                    ⚠️ {error}
                  </div>
                ) : (
                  <MapContainer center={center} zoom={8} style={{ height: '100%', width: '100%' }}>
                    <MapFlyTo center={flyCenter} />
                    {mapProvider === 'satellite' ? (
                      <TileLayer
                        key="satellite-tiles"
                        attribution='&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                        maxZoom={19}
                      />
                    ) : mapProvider === 'osm' ? (
                      <TileLayer
                        key="osm-tiles"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        maxZoom={19}
                      />
                    ) : mapProvider === 'mappls' ? (
                      <TileLayer
                        key="mappls-tiles"
                        attribution='&copy; <a href="https://www.mappls.com" target="_blank" rel="noopener noreferrer">Mappls MapmyIndia</a>'
                        url={`https://apis.mappls.com/advancedmaps/v1/${mapplsApiKey}/map_tile/{z}/{x}/{y}.png`}
                        maxZoom={19}
                      />
                    ) : (
                      <TileLayer
                        key="carto-tiles"
                        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                        maxZoom={19}
                      />
                    )}

                    {filteredFeatures.map((f) => {
                      const [lon, lat] = f.geometry.coordinates;
                      const { id, name, color, score, report_count } = f.properties;
                      const colorHex = getColorHex(color);

                      return (
                        <React.Fragment key={id}>
                          {/* Main village hotspot point */}
                          <CircleMarker
                            center={[lat, lon]}
                            radius={color === 'red' ? 12 : 9}
                            pathOptions={{
                              fillColor: colorHex,
                              fillOpacity: 0.85,
                              color: '#ffffff',
                              weight: 2
                            }}
                            eventHandlers={{
                              click: () => handleSelectVillage(f.properties, [lon, lat]),
                              popupopen: () => handleSelectVillage(f.properties, [lon, lat])
                            }}
                          >
                            <Popup>
                              <div style={{ color: '#0f172a', minWidth: '180px' }}>
                                <strong style={{ fontSize: '0.95rem' }}>{name}</strong>
                                <div style={{ marginTop: '4px', fontSize: '0.78rem' }}>
                                  <span style={{
                                    display: 'inline-block',
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    background: colorHex,
                                    color: '#fff',
                                    fontWeight: 700,
                                    fontSize: '0.68rem',
                                    marginRight: '6px'
                                  }}>
                                    {color.toUpperCase()}
                                  </span>
                                  Risk Score: <strong>{score.toFixed(1)}/100</strong>
                                </div>
                                <div style={{ marginTop: '4px', fontSize: '0.75rem', color: '#64748b' }}>
                                  Confirmed Reports: {report_count}
                                </div>
                                <button
                                  onClick={() => handleSelectVillage(f.properties, [lon, lat])}
                                  style={{
                                    marginTop: '8px',
                                    width: '100%',
                                    background: '#0284c7',
                                    color: '#fff',
                                    border: 'none',
                                    padding: '4px 8px',
                                    borderRadius: '4px',
                                    fontSize: '0.72rem',
                                    cursor: 'pointer',
                                    fontWeight: 600
                                  }}
                                >
                                  Inspect Village Telemetry →
                                </button>
                              </div>
                            </Popup>
                          </CircleMarker>

                          {/* 2km spread buffer circle for Red zones */}
                          {color === 'red' && (
                            <Circle
                              center={[lat, lon]}
                              radius={2000}
                              pathOptions={{
                                fillColor: colorHex,
                                fillOpacity: 0.08,
                                color: colorHex,
                                weight: 1.5,
                                dashArray: '6, 6'
                              }}
                            />
                          )}
                        </React.Fragment>
                      );
                    })}
                  </MapContainer>
                )}
              </div>
            </div>

            {/* Right Side: Village Inspection Panel */}
            <div style={{ background: '#131b2e', borderRadius: '14px', border: '1px solid #1e293b', padding: '20px', display: 'flex', flexDirection: 'column', height: '100%' }}>
              {selectedVillage ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid #1e293b', paddingBottom: '12px' }}>
                    <div>
                      <span style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>VILLAGE TELEMETRY</span>
                      <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', margin: '2px 0 0 0' }}>{selectedVillage.name}</h2>
                    </div>
                    <span style={{
                      padding: '4px 10px',
                      borderRadius: '999px',
                      background: getColorHex(selectedVillage.color) + '22',
                      color: getColorHex(selectedVillage.color),
                      border: `1px solid ${getColorHex(selectedVillage.color)}`,
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      textTransform: 'uppercase'
                    }}>
                      {selectedVillage.color.replace('_', ' ')}
                    </span>
                  </div>

                  {/* Risk Score Meter */}
                  <div style={{ marginTop: '16px', background: '#1e293b', padding: '14px', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px' }}>
                      <span style={{ color: '#94a3b8' }}>Epidemic Risk Index</span>
                      <strong style={{ color: getColorHex(selectedVillage.color), fontSize: '0.95rem' }}>
                        {selectedVillage.score.toFixed(1)} / 100
                      </strong>
                    </div>
                    <div style={{ width: '100%', height: '8px', background: '#0f172a', borderRadius: '999px', overflow: 'hidden' }}>
                      <div style={{
                        width: `${Math.min(100, selectedVillage.score)}%`,
                        height: '100%',
                        background: getColorHex(selectedVillage.color),
                        transition: 'width 0.4s ease'
                      }} />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b', marginTop: '4px' }}>
                      <span>0 (Safe)</span>
                      <span>50 (Risk Alert)</span>
                      <span>100 (Outbreak)</span>
                    </div>
                  </div>

                  {/* Real-Time Open-Meteo Weather Box */}
                  <div style={{ marginTop: '16px', background: '#1e293b', padding: '14px', borderRadius: '10px' }}>
                    <div style={{ fontSize: '0.78rem', color: '#94a3b8', fontWeight: 600, marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span>🌦️</span> Open-Meteo Climate Sensors
                    </div>

                    {weatherLoading ? (
                      <div style={{ fontSize: '0.8rem', color: '#38bdf8' }}>Fetching live climate telemetry…</div>
                    ) : villageWeather ? (
                      <>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', textAlign: 'center' }}>
                          <div style={{ background: '#0f172a', padding: '8px', borderRadius: '6px' }}>
                            <span style={{ fontSize: '0.7rem', color: '#64748b' }}>TEMP</span>
                            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>{villageWeather.temperature_c.toFixed(1)}°C</div>
                          </div>
                          <div style={{ background: '#0f172a', padding: '8px', borderRadius: '6px' }}>
                            <span style={{ fontSize: '0.7rem', color: '#64748b' }}>HUMIDITY</span>
                            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#38bdf8' }}>{villageWeather.humidity_pct.toFixed(0)}%</div>
                          </div>
                          <div style={{ background: '#0f172a', padding: '8px', borderRadius: '6px' }}>
                            <span style={{ fontSize: '0.7rem', color: '#64748b' }}>RAIN</span>
                            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#a78bfa' }}>{villageWeather.rainfall_mm.toFixed(1)}mm</div>
                          </div>
                        </div>

                        {villageWeather.alerts && villageWeather.alerts.length > 0 && (
                          <div style={{ marginTop: '10px' }}>
                            {villageWeather.alerts.map((alt, i) => (
                              <div key={i} style={{ background: 'rgba(244, 63, 94, 0.15)', border: '1px solid #f43f5e', color: '#fda4af', padding: '6px 10px', borderRadius: '6px', fontSize: '0.72rem', fontWeight: 600, marginTop: '4px' }}>
                                ⚠️ {alt}
                              </div>
                            ))}
                          </div>
                        )}
                      </>
                    ) : (
                      <div style={{ fontSize: '0.78rem', color: '#64748b' }}>No live weather records found.</div>
                    )}
                  </div>

                  {/* Immediate Action Buttons */}
                  <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 700, letterSpacing: '0.04em' }}>RAPID CONTAINMENT ACTIONS</span>
                    <button
                      onClick={() => {
                        setActionNotice(`Emergency drone chemical dispatch assigned for ${selectedVillage.name}!`);
                        setTimeout(() => setActionNotice(null), 4000);
                      }}
                      style={{
                        background: '#e11d48',
                        color: '#fff',
                        border: 'none',
                        padding: '10px',
                        borderRadius: '8px',
                        fontWeight: 700,
                        fontSize: '0.82rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px'
                      }}
                    >
                      🚁 Dispatch Drone Ring Spray
                    </button>

                    <button
                      onClick={() => {
                        setActionNotice(`SMS advisory broadcasted to all registered farmers in ${selectedVillage.name}!`);
                        setTimeout(() => setActionNotice(null), 4000);
                      }}
                      style={{
                        background: '#0284c7',
                        color: '#fff',
                        border: 'none',
                        padding: '10px',
                        borderRadius: '8px',
                        fontWeight: 700,
                        fontSize: '0.82rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px'
                      }}
                    >
                      📢 Broadcast Push Advisory
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b', textAlign: 'center' }}>
                  <span style={{ fontSize: '2.5rem', marginBottom: '12px' }}>📍</span>
                  <strong style={{ color: '#94a3b8', fontSize: '0.95rem' }}>No Village Selected</strong>
                  <p style={{ fontSize: '0.78rem', marginTop: '6px' }}>
                    Click any marker on the map or select from the surveillance list to inspect real-time disease telemetry and weather.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── TAB 2: VILLAGE SURVEILLANCE MATRIX ─────────────────────────── */}
        {activeTab === 'villages' && (
          <div style={{ background: '#131b2e', borderRadius: '14px', border: '1px solid #1e293b', padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>Village Risk Registry</h2>
                <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                  Jurisdiction Scoped: {user?.jurisdiction_name || user?.jurisdiction_type} ({villages.length} Villages)
                </span>
              </div>
              <input
                type="text"
                placeholder="Search village name…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  background: '#0f172a',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  padding: '6px 14px',
                  fontSize: '0.82rem',
                  outline: 'none',
                  width: '240px'
                }}
              />
            </div>

            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                  <th style={{ padding: '10px 14px' }}>VILLAGE NAME</th>
                  <th style={{ padding: '10px 14px' }}>STATUS</th>
                  <th style={{ padding: '10px 14px' }}>RISK SCORE</th>
                  <th style={{ padding: '10px 14px' }}>ACTIVE REPORTS</th>
                  <th style={{ padding: '10px 14px' }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {features
                  .filter((f) => searchQuery === '' || f.properties.name.toLowerCase().includes(searchQuery.toLowerCase()))
                  .map((f) => {
                    const { id, name, color, score, report_count } = f.properties;
                    const colorHex = getColorHex(color);
                    return (
                      <tr key={id} style={{ borderBottom: '1px solid #1e293b' }}>
                        <td style={{ padding: '12px 14px', fontWeight: 600, color: '#f8fafc' }}>{name}</td>
                        <td style={{ padding: '12px 14px' }}>
                          <span style={{
                            padding: '3px 8px',
                            borderRadius: '999px',
                            background: colorHex + '22',
                            color: colorHex,
                            border: `1px solid ${colorHex}`,
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            textTransform: 'uppercase'
                          }}>
                            {color.replace('_', ' ')}
                          </span>
                        </td>
                        <td style={{ padding: '12px 14px' }}>
                          <strong style={{ color: colorHex }}>{score.toFixed(1)}</strong> / 100
                        </td>
                        <td style={{ padding: '12px 14px', color: '#cbd5e1' }}>{report_count} Confirmed</td>
                        <td style={{ padding: '12px 14px' }}>
                          <button
                            onClick={() => {
                              handleSelectVillage(f.properties, f.geometry.coordinates);
                              setActiveTab('map');
                            }}
                            style={{
                              background: '#0284c7',
                              color: '#fff',
                              border: 'none',
                              borderRadius: '4px',
                              padding: '4px 10px',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              cursor: 'pointer'
                            }}
                          >
                            Locate on Map ↗
                          </button>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        )}

        {/* ── TAB 3: EXPERT VALIDATION QUEUE ────────────────────────────── */}
        {activeTab === 'expert' && (
          <div style={{ background: '#131b2e', borderRadius: '14px', border: '1px solid #1e293b', padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
                  Expert Validation &amp; Retraining Loop (Module M5)
                </h2>
                <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                  Low-confidence (&lt;70%) farmer scans queued for specialist confirmation
                </span>
              </div>
            </div>

            {expertQueue.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#10b981' }}>
                <span style={{ fontSize: '2rem' }}>🎉</span>
                <p style={{ marginTop: '8px', fontWeight: 600 }}>Validation queue is clear! All farmer scans processed.</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
                {expertQueue.map((item) => (
                  <div key={item.id} style={{ background: '#1e293b', borderRadius: '10px', border: '1px solid #334155', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>ID: {item.id.slice(0, 8)}</span>
                      <span style={{
                        background: 'rgba(245, 158, 11, 0.2)',
                        color: '#f59e0b',
                        border: '1px solid #f59e0b',
                        padding: '2px 8px',
                        borderRadius: '999px',
                        fontSize: '0.7rem',
                        fontWeight: 700
                      }}>
                        CONFIDENCE: {(item.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div style={{ margin: '12px 0' }}>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>PREDICTED PATHOGEN:</span>
                      <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#38bdf8', margin: '2px 0 0 0' }}>
                        {item.disease_id.replace(/_/g, ' ').toUpperCase()}
                      </h4>
                    </div>

                    <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
                      <button
                        onClick={() => handleValidateReport(item.id)}
                        style={{
                          flex: 1,
                          background: '#10b981',
                          color: '#064e3b',
                          border: 'none',
                          padding: '8px',
                          borderRadius: '6px',
                          fontWeight: 700,
                          fontSize: '0.78rem',
                          cursor: 'pointer'
                        }}
                      >
                        ✓ Confirm Diagnosis
                      </button>
                      <button
                        onClick={() => handleValidateReport(item.id, 'solanaceous_late_blight')}
                        style={{
                          flex: 1,
                          background: '#f59e0b',
                          color: '#451a03',
                          border: 'none',
                          padding: '8px',
                          borderRadius: '6px',
                          fontWeight: 700,
                          fontSize: '0.78rem',
                          cursor: 'pointer'
                        }}
                      >
                        ✎ Correct to Late Blight
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── TAB 4: DRONE SPRAY DISPATCH ────────────────────────────────── */}
        {activeTab === 'drone' && (
          <div style={{ background: '#131b2e', borderRadius: '14px', border: '1px solid #1e293b', padding: '20px' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', margin: '0 0 16px 0' }}>
              Drone Fleet &amp; Spray Operations (Module M4/M5)
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
              {[
                { id: 'DRN-2026-0819', village: 'Rampur Khurd', crop: 'Wheat (गेहूं)', acres: 3, cost: '₹1,200', status: 'Approved', pilot: 'Pilot Unit #4 (Sitapur Hub)' },
                { id: 'DRN-2026-0820', village: 'Sonbarsa', crop: 'Potato (आलू)', acres: 5, cost: '₹2,000', status: 'Pending Review', pilot: 'Unassigned' },
                { id: 'DRN-2026-0821', village: 'Gajraula', crop: 'Mustard (सरसों)', acres: 2, cost: '₹800', status: 'In Transit', pilot: 'Pilot Unit #2 (Maholi)' },
              ].map((b) => (
                <div key={b.id} style={{ background: '#1e293b', borderRadius: '10px', border: '1px solid #334155', padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <strong style={{ color: '#38bdf8', fontSize: '0.9rem' }}>{b.id}</strong>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '999px',
                      background: b.status === 'Approved' ? 'rgba(16,185,129,0.2)' : 'rgba(245,158,11,0.2)',
                      color: b.status === 'Approved' ? '#10b981' : '#f59e0b',
                      fontSize: '0.72rem',
                      fontWeight: 700
                    }}>
                      {b.status}
                    </span>
                  </div>

                  <div style={{ marginTop: '10px', fontSize: '0.8rem', color: '#cbd5e1' }}>
                    <div>📍 Village: <strong>{b.village}</strong></div>
                    <div>🌾 Crop: <strong>{b.crop}</strong> ({b.acres} Acres)</div>
                    <div>💰 Cost: <strong>{b.cost}</strong></div>
                    <div>🚁 Pilot: <span style={{ color: '#94a3b8' }}>{b.pilot}</span></div>
                  </div>

                  {b.status === 'Pending Review' && (
                    <button
                      onClick={() => {
                        setActionNotice(`Drone booking ${b.id} approved and dispatched!`);
                        setTimeout(() => setActionNotice(null), 4000);
                      }}
                      style={{
                        marginTop: '12px',
                        width: '100%',
                        background: '#10b981',
                        color: '#064e3b',
                        border: 'none',
                        padding: '8px',
                        borderRadius: '6px',
                        fontWeight: 700,
                        fontSize: '0.78rem',
                        cursor: 'pointer'
                      }}
                    >
                      Approve &amp; Assign Pilot Unit →
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── TAB 5: PMFBY SUBSIDY FLAG PANEL ────────────────────────────── */}
        {activeTab === 'subsidy' && (
          <div style={{ background: '#131b2e', borderRadius: '14px', border: '1px solid #1e293b', padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>🏛️ PMFBY Subsidy Flag Panel (Phase 11)</h2>
                <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '4px 0 0 0' }}>Raise and approve PMFBY insurance claim flags. Audit trail is immutable once approved.</p>
              </div>
              <button
                onClick={async () => {
                  setSubsidyLoading(true);
                  try {
                    const res = await fetch(`${apiBase}/api/v1/subsidy/flags`);
                    if (res.ok) setSubsidyFlags(await res.json());
                  } catch { /* offline demo */ }
                  setSubsidyLoading(false);
                }}
                style={{ background: '#1e293b', color: '#38bdf8', border: '1px solid #334155', borderRadius: '6px', padding: '6px 14px', fontSize: '0.78rem', fontWeight: 600, cursor: 'pointer' }}
              >
                🔄 Refresh Flags
              </button>
            </div>

            {/* Demo Flag — Raise a new flag */}
            <div style={{ background: '#1e293b', borderRadius: '10px', border: '1px solid rgba(245,158,11,0.3)', padding: '16px', marginBottom: '16px' }}>
              <div style={{ fontSize: '0.8rem', color: '#f59e0b', fontWeight: 700, marginBottom: '10px' }}>⚡ RAISE NEW PMFBY FLAG</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 120px', gap: '10px', alignItems: 'end' }}>
                <div>
                  <label style={{ fontSize: '0.72rem', color: '#64748b', display: 'block', marginBottom: '4px' }}>VILLAGE / JURISDICTION</label>
                  <select
                    id="subsidy-jurisdiction-select"
                    style={{ width: '100%', background: '#0f172a', color: '#f8fafc', border: '1px solid #334155', borderRadius: '6px', padding: '6px 10px', fontSize: '0.82rem', outline: 'none' }}
                  >
                    <option value="VIL-1">Rampur Khurd</option>
                    <option value="VIL-2">Sonbarsa</option>
                    <option value="VIL-3">Gajraula</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.72rem', color: '#64748b', display: 'block', marginBottom: '4px' }}>DISEASE</label>
                  <select
                    id="subsidy-disease-select"
                    style={{ width: '100%', background: '#0f172a', color: '#f8fafc', border: '1px solid #334155', borderRadius: '6px', padding: '6px 10px', fontSize: '0.82rem', outline: 'none' }}
                  >
                    <option value="wheat_yellow_rust">Wheat Yellow Rust</option>
                    <option value="potato_early_blight">Potato Early Blight</option>
                    <option value="tomato_late_blight">Tomato Late Blight</option>
                  </select>
                </div>
                <button
                  id="btn-raise-subsidy-flag"
                  onClick={async () => {
                    const jur = (document.getElementById('subsidy-jurisdiction-select') as HTMLSelectElement)?.value;
                    const dis = (document.getElementById('subsidy-disease-select') as HTMLSelectElement)?.value;
                    try {
                      const res = await fetch(`${apiBase}/api/v1/subsidy/flag`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ officer_id: 'OFF-DEMO', jurisdiction_id: jur, disease_id: dis, acreage_ha: 4.5 }),
                      });
                      if (res.ok) {
                        setActionNotice('PMFBY flag raised successfully!');
                        const flagsRes = await fetch(`${apiBase}/api/v1/subsidy/flags`);
                        if (flagsRes.ok) setSubsidyFlags(await flagsRes.json());
                      } else {
                        const err = await res.json();
                        setActionNotice(`Cannot raise flag: ${err.detail}`);
                      }
                    } catch {
                      setActionNotice('Backend offline — flag cannot be raised in demo mode.');
                    }
                    setTimeout(() => setActionNotice(null), 5000);
                  }}
                  style={{ background: '#7c3aed', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 14px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' }}
                >
                  ⚑ Raise Flag
                </button>
              </div>
            </div>

            {/* Flags List */}
            {subsidyLoading ? (
              <div style={{ textAlign: 'center', color: '#38bdf8', padding: '20px' }}>Loading flags…</div>
            ) : subsidyFlags.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#64748b', padding: '30px', fontSize: '0.88rem' }}>
                No PMFBY flags raised yet. Use the form above to raise one, or ensure the backend is running with seeded disease reports.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '14px' }}>
                {subsidyFlags.map((flag: any) => (
                  <div key={flag.id} style={{ background: '#1e293b', borderRadius: '10px', border: `1px solid ${flag.status === 'approved' ? 'rgba(16,185,129,0.4)' : flag.status === 'rejected' ? 'rgba(244,63,94,0.4)' : 'rgba(245,158,11,0.3)'}`, padding: '14px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b' }}>FLAG ID</div>
                        <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#38bdf8' }}>{flag.id?.slice(0, 12)}…</div>
                      </div>
                      <span style={{
                        padding: '3px 10px', borderRadius: '999px', fontSize: '0.7rem', fontWeight: 700,
                        background: flag.status === 'approved' ? 'rgba(16,185,129,0.2)' : flag.status === 'rejected' ? 'rgba(244,63,94,0.2)' : 'rgba(245,158,11,0.2)',
                        color: flag.status === 'approved' ? '#10b981' : flag.status === 'rejected' ? '#f43f5e' : '#f59e0b',
                      }}>{flag.status?.toUpperCase()}</span>
                    </div>

                    <div style={{ marginTop: '10px', fontSize: '0.78rem', color: '#cbd5e1', lineHeight: 1.6 }}>
                      <div>🏘️ Jurisdiction: <strong>{flag.jurisdiction_id}</strong></div>
                      <div>🦠 Disease: <strong>{flag.disease_id?.replace(/_/g, ' ')}</strong></div>
                      <div>👨‍🌾 Farmers: <strong>{flag.farmer_count}</strong> | Reports: <strong>{flag.report_count}</strong></div>
                      {flag.pmfby_window_expires_at && (
                        <div>⏰ PMFBY Window: <strong style={{ color: '#f59e0b' }}>{new Date(flag.pmfby_window_expires_at).toLocaleString('en-IN')}</strong></div>
                      )}
                    </div>

                    {flag.status === 'pending' && (
                      <button
                        onClick={async () => {
                          try {
                            const res = await fetch(`${apiBase}/api/v1/subsidy/flags/${flag.id}/approve`, {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ approver_id: 'BDO-DEMO' }),
                            });
                            if (res.ok) {
                              setActionNotice(`Flag ${flag.id.slice(0, 8)} approved! Audit trail locked.`);
                              const flagsRes = await fetch(`${apiBase}/api/v1/subsidy/flags`);
                              if (flagsRes.ok) setSubsidyFlags(await flagsRes.json());
                            } else {
                              const err = await res.json();
                              setActionNotice(`Approval error: ${err.detail}`);
                            }
                          } catch {
                            setActionNotice('Backend offline.');
                          }
                          setTimeout(() => setActionNotice(null), 5000);
                        }}
                        style={{ marginTop: '10px', width: '100%', background: '#10b981', color: '#064e3b', border: 'none', padding: '8px', borderRadius: '6px', fontWeight: 700, fontSize: '0.78rem', cursor: 'pointer' }}
                      >
                        ✓ Approve Flag (BDO)
                      </button>
                    )}

                    {flag.status === 'approved' && (
                      <div style={{ marginTop: '10px', fontSize: '0.72rem', color: '#10b981', fontWeight: 600 }}>🔒 Audit trail locked — immutable</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── TAB 6: AGRISTACK & WDRA STORAGE (PHASE 12) ─────────────────── */}
        {activeTab === 'agristack' && (
          <div>
            {/* Header / Actions Bar */}
            <div style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid #334155', padding: '16px 20px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.05rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>🌾</span> AgriStack Crop Sown Registry & WDRA Storage Engine
                </h3>
                <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
                  UFSI gateway sync, Lekhpal/Kanungo statutory crop discrepancy auditing, and e-NWR warehouse pledge routing.
                </p>
              </div>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <button
                  disabled={agriStackLoading}
                  onClick={async () => {
                    setAgriStackLoading(true);
                    setActionNotice('Connecting to AgriStack UFSI Gateway…');
                    try {
                      const token = localStorage.getItem('officer_token');
                      const res = await fetch(`${apiBase}/api/v1/agristack/sync`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                          Authorization: `Bearer ${token}`
                        },
                        body: JSON.stringify({ season: 'rabi' })
                      });
                      if (res.ok) {
                        const data = await res.json();
                        setActionNotice(`✓ ${data.message}`);
                        // Reload catalogue
                        const catRes = await fetch(`${apiBase}/api/v1/agristack/catalogue`, {
                          headers: { Authorization: `Bearer ${token}` }
                        });
                        if (catRes.ok) setCropCatalogue(await catRes.json());
                      } else {
                        const err = await res.json();
                        setActionNotice(`Sync error: ${err.detail || 'UFSI Gateway error'}`);
                      }
                    } catch {
                      setActionNotice('Backend offline or AgriStack gateway timeout.');
                    } finally {
                      setAgriStackLoading(false);
                      setTimeout(() => setActionNotice(null), 5000);
                    }
                  }}
                  style={{
                    background: agriStackLoading ? '#475569' : '#0284c7',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '9px 16px',
                    fontSize: '0.82rem',
                    fontWeight: 700,
                    cursor: agriStackLoading ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <span>🔄</span> {agriStackLoading ? 'Synchronizing UFSI…' : 'Sync AgriStack Registry'}
                </button>
              </div>
            </div>

            {/* Metrics Ribbon */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '20px' }}>
              <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', padding: '14px' }}>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600 }}>REGISTERED PARCELS</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#38bdf8', marginTop: '4px' }}>{cropCatalogue.length}</div>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Synced via UFSI Gateway</div>
              </div>

              <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', padding: '14px' }}>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600 }}>TOTAL SYNCED ACREAGE</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#10b981', marginTop: '4px' }}>
                  {cropCatalogue.reduce((sum, c) => sum + (c.acreage_ha || 0), 0).toFixed(1)} ha
                </div>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Verified Land Parcels</div>
              </div>

              <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', padding: '14px' }}>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600 }}>STATUTORY DISCREPANCIES</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: cropDiscrepancies.length > 0 ? '#f59e0b' : '#38bdf8', marginTop: '4px' }}>
                  {cropDiscrepancies.length}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Filed by Lekhpal/Kanungo</div>
              </div>

              <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '10px', padding: '14px' }}>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600 }}>WDRA PLEDGE LOAN RATE</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#a855f7', marginTop: '4px' }}>4.0% p.a.</div>
                <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Subsidized e-NWR Credit</div>
              </div>
            </div>

            {/* 2-Column Main Workspace */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>

              {/* Left Column: Live Crop Catalogue Table */}
              <div style={{ background: '#131b2e', borderRadius: '12px', border: '1px solid #1e293b', padding: '18px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <h4 style={{ margin: 0, fontSize: '0.95rem', color: '#f8fafc' }}>
                    📋 Dynamic Crop Catalogue (AgriStack Synced)
                  </h4>
                  <span style={{ fontSize: '0.75rem', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '2px 8px', borderRadius: '6px' }}>
                    {cropCatalogue.length} Crops in Scope
                  </span>
                </div>

                {cropCatalogue.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748b' }}>
                    <div style={{ fontSize: '2rem', marginBottom: '10px' }}>🌾</div>
                    No synced crops found yet. Click <strong>"Sync AgriStack Registry"</strong> above to load live registry parcels.
                  </div>
                ) : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                      <thead>
                        <tr style={{ background: '#1e293b', color: '#94a3b8', textAlign: 'left' }}>
                          <th style={{ padding: '8px 10px', borderRadius: '6px 0 0 6px' }}>Village / Parcel</th>
                          <th style={{ padding: '8px 10px' }}>Crop</th>
                          <th style={{ padding: '8px 10px' }}>Area</th>
                          <th style={{ padding: '8px 10px' }}>Stage / Season</th>
                          <th style={{ padding: '8px 10px' }}>Farmer</th>
                          <th style={{ padding: '8px 10px', borderRadius: '0 6px 6px 0' }}>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {cropCatalogue.map((crop: any) => (
                          <tr key={crop.id} style={{ borderBottom: '1px solid #1e293b', color: '#cbd5e1' }}>
                            <td style={{ padding: '10px 10px' }}>
                              <div style={{ fontWeight: 600, color: '#f8fafc' }}>{crop.village_name}</div>
                              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>ID: {crop.id.slice(0, 8)}…</div>
                            </td>
                            <td style={{ padding: '10px 10px' }}>
                              <span style={{ fontWeight: 700, color: '#38bdf8' }}>{crop.crop_name}</span>
                            </td>
                            <td style={{ padding: '10px 10px' }}>
                              <strong>{crop.acreage_ha}</strong> ha
                            </td>
                            <td style={{ padding: '10px 10px' }}>
                              <div style={{ textTransform: 'capitalize' }}>{crop.growth_stage?.replace('_', ' ') || 'Growing'}</div>
                              <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase' }}>{crop.season}</div>
                            </td>
                            <td style={{ padding: '10px 10px' }}>
                              <div>{crop.farmer_name || 'Registered Farmer'}</div>
                              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>{crop.farmer_phone}</div>
                            </td>
                            <td style={{ padding: '10px 10px' }}>
                              {crop.synced_from_agristack ? (
                                <span style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', padding: '2px 8px', borderRadius: '999px', fontSize: '0.68rem', fontWeight: 700 }}>
                                  ✓ UFSI Synced
                                </span>
                              ) : (
                                <span style={{ background: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', padding: '2px 8px', borderRadius: '999px', fontSize: '0.68rem' }}>
                                  Manual
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Right Column: Lekhpal Discrepancy & WDRA Storage Engine */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

                {/* Statutory Discrepancy Reporting Form (Lekhpal/Kanungo) */}
                <div style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid #334155', padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <h4 style={{ margin: 0, fontSize: '0.9rem', color: '#f8fafc' }}>
                      ⚖️ Statutory Discrepancy Filing (Revenue Wing)
                    </h4>
                    <span style={{ fontSize: '0.7rem', color: '#f59e0b', background: 'rgba(245, 158, 11, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                      Lekhpal / Kanungo / Tehsildar / DM
                    </span>
                  </div>
                  <p style={{ fontSize: '0.74rem', color: '#94a3b8', margin: '0 0 12px' }}>
                    Log ground verification discrepancies against AgriStack survey entries with immutable audit logging.
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.78rem' }}>
                    <div>
                      <label style={{ display: 'block', color: '#94a3b8', marginBottom: '3px' }}>Village Jurisdiction</label>
                      <select
                        value={discVillage}
                        onChange={(e) => setDiscVillage(e.target.value)}
                        style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', padding: '6px', fontSize: '0.78rem' }}
                      >
                        <option value="">Select Village…</option>
                        {villages.map((v) => (
                          <option key={v.id} value={v.id}>{v.name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label style={{ display: 'block', color: '#94a3b8', marginBottom: '3px' }}>Khasra / Survey No.</label>
                      <input
                        type="text"
                        placeholder="e.g. KH-102/4"
                        value={discSurvey}
                        onChange={(e) => setDiscSurvey(e.target.value)}
                        style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', padding: '6px', fontSize: '0.78rem' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', color: '#94a3b8', marginBottom: '3px' }}>Reported Crop (Registry)</label>
                      <input
                        type="text"
                        value={discReportedCrop}
                        onChange={(e) => setDiscReportedCrop(e.target.value)}
                        style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', padding: '6px', fontSize: '0.78rem' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', color: '#94a3b8', marginBottom: '3px' }}>Actual Crop Observed</label>
                      <input
                        type="text"
                        value={discActualCrop}
                        onChange={(e) => setDiscActualCrop(e.target.value)}
                        style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#10b981', padding: '6px', fontSize: '0.78rem', fontWeight: 600 }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', color: '#94a3b8', marginBottom: '3px' }}>Reported Area (ha)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={discReportedArea}
                        onChange={(e) => setDiscReportedArea(parseFloat(e.target.value) || 0)}
                        style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', padding: '6px', fontSize: '0.78rem' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', color: '#94a3b8', marginBottom: '3px' }}>Actual Area (ha)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={discActualArea}
                        onChange={(e) => setDiscActualArea(parseFloat(e.target.value) || 0)}
                        style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', padding: '6px', fontSize: '0.78rem' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', color: '#94a3b8', marginBottom: '3px' }}>Farmer Name (Optional)</label>
                      <input
                        type="text"
                        placeholder="e.g. Ram Prasad"
                        value={discFarmer}
                        onChange={(e) => setDiscFarmer(e.target.value)}
                        style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', padding: '6px', fontSize: '0.78rem' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', color: '#94a3b8', marginBottom: '3px' }}>Discrepancy Category</label>
                      <select
                        value={discType}
                        onChange={(e) => setDiscType(e.target.value)}
                        style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', padding: '6px', fontSize: '0.78rem' }}
                      >
                        <option value="crop_mismatch">Crop Mismatch (Different Crop Sown)</option>
                        <option value="area_mismatch">Area Mismatch (Acreage Variance)</option>
                        <option value="stage_mismatch">Growth Stage Discrepancy</option>
                        <option value="unrecorded_plot">Unrecorded Plot / Encroachment</option>
                      </select>
                    </div>
                  </div>

                  <div style={{ marginTop: '10px' }}>
                    <label style={{ display: 'block', color: '#94a3b8', fontSize: '0.75rem', marginBottom: '3px' }}>Lekhpal Inspection Notes</label>
                    <input
                      type="text"
                      placeholder="Ground inspection remarks..."
                      value={discNotes}
                      onChange={(e) => setDiscNotes(e.target.value)}
                      style={{ width: '100%', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', padding: '6px', fontSize: '0.78rem' }}
                    />
                  </div>

                  <button
                    onClick={async () => {
                      if (!discVillage) {
                        setActionNotice('Please select a village.');
                        setTimeout(() => setActionNotice(null), 3000);
                        return;
                      }
                      try {
                        const token = localStorage.getItem('officer_token');
                        const res = await fetch(`${apiBase}/api/v1/agristack/discrepancies`, {
                          method: 'POST',
                          headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${token}`
                          },
                          body: JSON.stringify({
                            jurisdiction_id: discVillage,
                            survey_number: discSurvey || 'KH-102/4',
                            reported_crop: discReportedCrop,
                            actual_crop_observed: discActualCrop,
                            reported_acreage_ha: discReportedArea,
                            actual_acreage_ha: discActualArea,
                            discrepancy_type: discType,
                            notes: discNotes || 'Ground inspection identified crop/acreage variance.'
                          })
                        });
                        if (res.ok) {
                          const data = await res.json();
                          setActionNotice(`✓ Discrepancy logged for ${data.survey_number}!`);
                          // Reload discrepancies
                          const dRes = await fetch(`${apiBase}/api/v1/agristack/discrepancies`, {
                            headers: { Authorization: `Bearer ${token}` }
                          });
                          if (dRes.ok) setCropDiscrepancies(await dRes.json());
                        } else {
                          const err = await res.json();
                          setActionNotice(`Cannot file discrepancy: ${err.detail}`);
                        }
                      } catch {
                        setActionNotice('Backend offline or submission failed.');
                      }
                      setTimeout(() => setActionNotice(null), 5000);
                    }}
                    style={{
                      marginTop: '12px',
                      width: '100%',
                      background: '#f59e0b',
                      color: '#000',
                      border: 'none',
                      padding: '8px',
                      borderRadius: '6px',
                      fontWeight: 700,
                      fontSize: '0.78rem',
                      cursor: 'pointer'
                    }}
                  >
                    📝 Submit Statutory Discrepancy (Lekhpal)
                  </button>

                  {/* Discrepancy Audit Log */}
                  {cropDiscrepancies.length > 0 && (
                    <div style={{ marginTop: '14px', borderTop: '1px solid #334155', paddingTop: '10px' }}>
                      <div style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600, marginBottom: '6px' }}>
                        RECENTLY FILED DISCREPANCIES ({cropDiscrepancies.length})
                      </div>
                      <div style={{ maxHeight: '120px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {cropDiscrepancies.slice(0, 3).map((d: any) => (
                          <div key={d.id} style={{ background: '#0f172a', padding: '6px 8px', borderRadius: '4px', fontSize: '0.72rem', color: '#cbd5e1' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                              <span style={{ fontWeight: 700, color: '#f59e0b' }}>{d.survey_number}</span>
                              <span style={{ color: '#94a3b8' }}>{d.village_name}</span>
                            </div>
                            <div>{d.reported_crop} → <strong style={{ color: '#10b981' }}>{d.actual_crop_observed}</strong> ({d.actual_acreage_ha}ha)</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* WDRA Post-Harvest Storage & e-NWR Loan Suggestion Simulator */}
                <div style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid #334155', padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <h4 style={{ margin: 0, fontSize: '0.9rem', color: '#f8fafc' }}>
                      🏢 WDRA Storage & e-NWR Loan Engine
                    </h4>
                    <span style={{ fontSize: '0.7rem', color: '#10b981', background: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                      Green Zone Pulses & Oilseeds
                    </span>
                  </div>
                  <p style={{ fontSize: '0.74rem', color: '#94a3b8', margin: '0 0 10px' }}>
                    Surfaces WDRA warehouse holding recommendations and ~70% e-NWR pledge credit @ 4% p.a. to protect farmers from post-harvest price slumps.
                  </p>

                  <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                    <select
                      value={storageVillageId}
                      onChange={(e) => setStorageVillageId(e.target.value)}
                      style={{ flex: 1, background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', padding: '6px', fontSize: '0.78rem' }}
                    >
                      <option value="">Select Village to Check…</option>
                      {villages.map((v) => (
                        <option key={v.id} value={v.id}>{v.name}</option>
                      ))}
                    </select>

                    <button
                      disabled={storageLoading}
                      onClick={async () => {
                        if (!storageVillageId) {
                          setActionNotice('Please select a village.');
                          setTimeout(() => setActionNotice(null), 3000);
                          return;
                        }
                        setStorageLoading(true);
                        try {
                          const token = localStorage.getItem('officer_token');
                          const res = await fetch(`${apiBase}/api/v1/post-harvest/storage-suggestions?village_id=${storageVillageId}`, {
                            headers: { Authorization: `Bearer ${token}` }
                          });
                          if (res.ok) {
                            const data = await res.json();
                            setStorageData(data);
                          } else {
                            setStorageData(null);
                          }
                        } catch {
                          setStorageData(null);
                        } finally {
                          setStorageLoading(false);
                        }
                      }}
                      style={{
                        background: '#10b981',
                        color: '#064e3b',
                        border: 'none',
                        borderRadius: '6px',
                        padding: '6px 14px',
                        fontWeight: 700,
                        fontSize: '0.78rem',
                        cursor: 'pointer'
                      }}
                    >
                      {storageLoading ? 'Evaluating…' : 'Check WDRA Advice'}
                    </button>
                  </div>

                  {/* Storage Advice Results */}
                  {storageData && storageData.advisories && storageData.advisories.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {storageData.advisories.map((adv: any, idx: number) => (
                        <div key={idx} style={{ background: '#0f172a', border: `1px solid ${adv.recommendation === 'STORE_WDRA' ? 'rgba(16, 185, 129, 0.4)' : '#334155'}`, borderRadius: '8px', padding: '10px', fontSize: '0.75rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontWeight: 700, color: '#38bdf8' }}>{adv.crop_name} ({adv.crop_category})</span>
                            <span style={{
                              padding: '2px 8px', borderRadius: '999px', fontSize: '0.68rem', fontWeight: 700,
                              background: adv.recommendation === 'STORE_WDRA' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                              color: adv.recommendation === 'STORE_WDRA' ? '#10b981' : '#f59e0b'
                            }}>
                              {adv.recommendation === 'STORE_WDRA' ? '✓ WDRA HOLD RECOMMENDED' : 'STANDARD MANDI SALE'}
                            </span>
                          </div>

                          <p style={{ margin: '6px 0', color: '#cbd5e1', lineHeight: 1.5 }}>{adv.rationale}</p>

                          {adv.enwr_pledge_loan_eligible && (
                            <div style={{ background: 'rgba(56, 189, 248, 0.08)', borderRadius: '6px', padding: '6px 8px', marginTop: '6px', display: 'flex', justifyContent: 'space-between' }}>
                              <span>💰 e-NWR Pledge Credit: <strong>Up to {adv.max_pledge_loan_pct}%</strong></span>
                              <span style={{ color: '#10b981', fontWeight: 700 }}>Rate: {adv.effective_interest_rate_pct}% p.a.</span>
                            </div>
                          )}

                          {adv.nearest_warehouses && adv.nearest_warehouses.length > 0 && (
                            <div style={{ marginTop: '6px', fontSize: '0.7rem', color: '#94a3b8' }}>
                              📍 Nearest Warehouse: <strong>{adv.nearest_warehouses[0].name}</strong> ({adv.nearest_warehouses[0].distance_km} km away, Capacity: {adv.nearest_warehouses[0].available_mt} MT free)
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : storageData ? (
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', textAlign: 'center', padding: '10px' }}>
                      No pulse/oilseed crop records found for {storageData.village_name}.
                    </div>
                  ) : null}
                </div>

              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
