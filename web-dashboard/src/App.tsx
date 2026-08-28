import React from 'react'

// MVP Module Map reference: PRODUCTION_WORKFLOW.md § MVP Module Map
// M1 AI Crop Doctor | M2 Crop Risk Radar | M3 Smart Advisory
// M4 Geo Disease Hotspot Maps | M5 Expert Validation Loop
const PHASES = [
  { id: 1,  label: 'Schema + Seed Data',              module: '' },
  { id: 2,  label: 'Auth + Jurisdiction Access',       module: '' },
  { id: 3,  label: 'Farmer App Shell',                 module: 'M1' },
  { id: 4,  label: 'Image Capture + Offline Queue',    module: 'M1' },
  { id: 5,  label: 'ML Inference Service',             module: 'M1' },
  { id: 6,  label: 'Pathogen-Branched Advisory',       module: 'M3' },
  { id: 7,  label: 'Expert Validation Queue',          module: 'M5' },
  { id: 8,  label: 'Zone Scoring Service',             module: 'M2 · M4' },
  { id: 9,  label: 'Officer Hotspot Map',              module: 'M4' },
  { id: 10, label: 'Weather + Flood Risk',             module: 'M2' },
  { id: 11, label: 'Subsidy + Drone Booking',          module: '' },
  { id: 12, label: 'AgriStack Sync',                   module: '' },
  { id: 13, label: 'Polish + Full Test Pass',          module: '' },
]

export default function App() {
  const apiBase = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
  const [health, setHealth] = React.useState<string>('checking…')

  React.useEffect(() => {
    fetch(`${apiBase}/health`)
      .then((r) => r.json())
      .then((d) => setHealth(`✅ API ${d.status} — v${d.version} (${d.env})`))
      .catch(() => setHealth('⚠️ API unreachable — start the backend'))
  }, [apiBase])

  return (
    <>
      {/* ── Header ───────────────────────────────────────────────────── */}
      <header className="shell-header">
        <span className="shell-logo">🌾 Kisan Saathi</span>
        <span style={{ fontSize: '0.8rem', color: 'var(--color-muted)' }}>
          Phase 0 — Scaffold
        </span>
        <span
          id="api-health-badge"
          style={{ fontSize: '0.75rem', color: 'var(--color-muted)' }}
        >
          {health}
        </span>
      </header>

      {/* ── Main ─────────────────────────────────────────────────────── */}
      <main className="shell-main">
        <section className="shell-hero animate-fadeInUp">
          <h1>Fasal Rakshak</h1>
          <p>
            AI-powered crop-disease surveillance, advisory, and subsidy
            management for UP districts.
          </p>
          <div
            className="badge badge-green pulse"
            style={{ display: 'inline-block' }}
          >
            Phase 0 — Shell Live
          </div>
        </section>

        {/* ── Phase road-map cards ──────────────────────────────────── */}
        <div className="phase-grid">
          {PHASES.map((p, i) => (
            <div
              key={p.id}
              className="phase-card-stub animate-fadeInUp"
              style={{ animationDelay: `${i * 40}ms` }}
              id={`phase-card-${p.id}`}
            >
              <strong style={{ color: 'var(--color-text)' }}>
                Phase {p.id}
              </strong>
              {p.module && (
                <span className="module-badge">{p.module}</span>
              )}
              <br />
              {p.label}
            </div>
          ))}
        </div>
      </main>
    </>
  )
}
