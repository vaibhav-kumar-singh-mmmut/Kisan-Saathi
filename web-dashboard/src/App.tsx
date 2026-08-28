import React from 'react'
import { useTranslation } from 'react-i18next'
import FarmerShell from './components/FarmerShell'

// MVP Module Map reference: PRODUCTION_WORKFLOW.md § MVP Module Map
// M1 AI Crop Doctor | M2 Crop Risk Radar | M3 Smart Advisory
// M4 Geo Disease Hotspot Maps | M5 Expert Validation Loop
const PHASES = [
  { id: 1,  label: 'Schema + Seed Data',              module: '',         done: true  },
  { id: 2,  label: 'Auth + Jurisdiction Access',       module: '',         done: true  },
  { id: 3,  label: 'Farmer App Shell',                 module: 'M1',       done: true  },
  { id: 4,  label: 'Image Capture + Offline Queue',    module: 'M1',       done: false },
  { id: 5,  label: 'ML Inference Service',             module: 'M1',       done: false },
  { id: 6,  label: 'Pathogen-Branched Advisory',       module: 'M3',       done: false },
  { id: 7,  label: 'Expert Validation Queue',          module: 'M5',       done: false },
  { id: 8,  label: 'Zone Scoring Service',             module: 'M2 · M4',  done: false },
  { id: 9,  label: 'Officer Hotspot Map',              module: 'M4',       done: false },
  { id: 10, label: 'Weather + Flood Risk',             module: 'M2',       done: false },
  { id: 11, label: 'Subsidy + Drone Booking',          module: '',         done: false },
  { id: 12, label: 'AgriStack Sync',                   module: '',         done: false },
  { id: 13, label: 'Polish + Full Test Pass',          module: '',         done: false },
]

// Phase 2 routing stub — in Phase 4 this reads from JWT stored in localStorage
type ViewMode = 'farmer' | 'officer'

function OfficerGrid({ onSwitch }: { onSwitch: () => void }) {
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
      <header className="shell-header">
        <span className="shell-logo">🌾 Kisan Saathi</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span id="api-health-badge" style={{ fontSize: '0.75rem', color: 'var(--text-2)' }}>
            {health}
          </span>
          <button
            id="switch-to-farmer"
            onClick={onSwitch}
            className="tts-btn"
          >
            Farmer View
          </button>
        </div>
      </header>

      <main className="shell-main">
        <section className="shell-hero animate-fadeInUp">
          <h1>Fasal Rakshak</h1>
          <p>
            AI-powered crop-disease surveillance, advisory, and subsidy
            management for UP districts.
          </p>
          <div className="badge badge-green pulse" style={{ display: 'inline-block' }}>
            Phases 1–3 Complete
          </div>
        </section>

        <div className="phase-grid">
          {PHASES.map((p, i) => (
            <div
              key={p.id}
              className={`phase-card-stub animate-fadeInUp${p.done ? ' phase-card-done' : ''}`}
              style={{ animationDelay: `${i * 40}ms` }}
              id={`phase-card-${p.id}`}
            >
              <strong style={{ color: p.done ? 'var(--color-primary)' : 'var(--color-text)' }}>
                {p.done ? '✅ ' : ''}Phase {p.id}
              </strong>
              {p.module && <span className="module-badge">{p.module}</span>}
              <br />
              {p.label}
            </div>
          ))}
        </div>
      </main>
    </>
  )
}

export default function App() {
  // Default to farmer view — Phase 4 will replace with JWT role routing
  const [view, setView] = React.useState<ViewMode>('farmer')
  // i18n is already initialised in main.tsx; useTranslation here just to satisfy TS
  useTranslation()

  if (view === 'farmer') {
    return (
      <div className="shell-container">
        <FarmerShell />
        <button
          id="switch-to-officer"
          className="dev-toggle-btn"
          onClick={() => setView('officer')}
        >
          Officer View
        </button>
      </div>
    )
  }

  return <OfficerGrid onSwitch={() => setView('farmer')} />
}
