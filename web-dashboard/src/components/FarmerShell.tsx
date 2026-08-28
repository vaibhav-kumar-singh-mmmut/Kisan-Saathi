/**
 * FarmerShell — Phase 3: Farmer App Shell
 *
 * 5 screens (icon nav tabs):
 *   [Scan Crop] [My Reports] [Weather Alert] [Ask Expert] [Book Drone]
 *
 * Every visible string comes from i18n. No hardcoded UI text.
 * Each screen auto-narrates on mount via TTS hook.
 */
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useTTS } from '../hooks/useTTS'
import LanguageToggle from './LanguageToggle'

// ── Types ────────────────────────────────────────────────────────────────────
type Tab = 'scan' | 'reports' | 'weather' | 'expert' | 'drone'

interface NavItem {
  id: Tab
  icon: string
  labelKey: string
}

const NAV_ITEMS: NavItem[] = [
  { id: 'scan',    icon: '🔬', labelKey: 'nav.scan_crop' },
  { id: 'reports', icon: '📋', labelKey: 'nav.my_reports' },
  { id: 'weather', icon: '🌦️', labelKey: 'nav.weather_alert' },
  { id: 'expert',  icon: '👨‍🌾', labelKey: 'nav.ask_expert' },
  { id: 'drone',   icon: '🚁', labelKey: 'nav.book_drone' },
]

// ── Screens ──────────────────────────────────────────────────────────────────

function ScanScreen() {
  const { t } = useTranslation()
  const { speak, stop, supported } = useTTS()
  const { i18n } = useTranslation()
  const [scanning, setScanning] = useState(false)

  useEffect(() => {
    speak(t('scan.narration'), i18n.language)
    return () => stop()
  }, [i18n.language])

  return (
    <div className="farmer-screen animate-fadeInUp" id="screen-scan">
      <h2 className="screen-title">{t('scan.title')}</h2>
      <p className="screen-sub">{t('scan.subtitle')}</p>

      <div className="scan-zone" id="scan-zone">
        <div className="scan-circle" onClick={() => setScanning(true)}>
          <span className="scan-icon">📷</span>
          <span className="scan-label">
            {scanning ? t('scan.uploading') : t('scan.tap_to_scan')}
          </span>
          {scanning && <div className="scan-spinner" />}
        </div>
      </div>

      {supported && (
        <div className="tts-controls">
          <button
            id="btn-listen-scan"
            className="tts-btn"
            onClick={() => speak(t('scan.narration'), i18n.language)}
          >
            🔊 {t('common.listen')}
          </button>
          <button className="tts-btn tts-btn-stop" onClick={stop}>
            ⏹ {t('common.stop')}
          </button>
        </div>
      )}

      {/* Phase 4 stub — image capture will plug in here */}
      <p className="coming-soon-note">{t('common.coming_soon')}</p>
    </div>
  )
}

function ReportsScreen() {
  const { t, i18n } = useTranslation()
  const { speak, stop, supported } = useTTS()

  useEffect(() => {
    speak(t('reports.narration'), i18n.language)
    return () => stop()
  }, [i18n.language])

  return (
    <div className="farmer-screen animate-fadeInUp" id="screen-reports">
      <h2 className="screen-title">{t('reports.title')}</h2>
      <p className="screen-sub">{t('reports.subtitle')}</p>

      <div className="empty-state" id="reports-empty">
        <span className="empty-icon">📭</span>
        <p>{t('reports.empty')}</p>
      </div>

      {supported && (
        <div className="tts-controls">
          <button
            id="btn-listen-reports"
            className="tts-btn"
            onClick={() => speak(t('reports.narration'), i18n.language)}
          >
            🔊 {t('common.listen')}
          </button>
          <button className="tts-btn tts-btn-stop" onClick={stop}>
            ⏹ {t('common.stop')}
          </button>
        </div>
      )}
    </div>
  )
}

function WeatherScreen() {
  const { t, i18n } = useTranslation()
  const { speak, stop, supported } = useTTS()

  useEffect(() => {
    speak(t('weather.narration'), i18n.language)
    return () => stop()
  }, [i18n.language])

  const DEMO_ZONES = [
    { nameKey: 'Rampur Khurd', zoneKey: 'zone.red', color: 'red' },
    { nameKey: 'Sonbarsa',     zoneKey: 'zone.red', color: 'red' },
    { nameKey: 'Fatehpur Mafi',zoneKey: 'zone.orange', color: 'orange' },
    { nameKey: 'Gajraula',     zoneKey: 'zone.incoming_risk', color: 'incoming' },
    { nameKey: 'Mahmoodpur',   zoneKey: 'zone.green', color: 'green' },
  ]

  return (
    <div className="farmer-screen animate-fadeInUp" id="screen-weather">
      <h2 className="screen-title">{t('weather.title')}</h2>
      <p className="screen-sub">{t('weather.subtitle')}</p>

      <div className="zone-list" id="weather-zone-list">
        {DEMO_ZONES.map((z) => (
          <div key={z.nameKey} className={`zone-row zone-row--${z.color}`}>
            <span className="zone-village">{z.nameKey}</span>
            <span className={`badge badge-${z.color === 'incoming' ? 'incoming' : z.color}`}>
              {t(z.zoneKey)}
            </span>
          </div>
        ))}
      </div>

      {supported && (
        <div className="tts-controls">
          <button
            id="btn-listen-weather"
            className="tts-btn"
            onClick={() => speak(t('weather.narration'), i18n.language)}
          >
            🔊 {t('common.listen')}
          </button>
          <button className="tts-btn tts-btn-stop" onClick={stop}>
            ⏹ {t('common.stop')}
          </button>
        </div>
      )}
    </div>
  )
}

function ExpertScreen() {
  const { t, i18n } = useTranslation()
  const { speak, stop, supported } = useTTS()
  const [question, setQuestion] = useState('')

  useEffect(() => {
    speak(t('expert.narration'), i18n.language)
    return () => stop()
  }, [i18n.language])

  return (
    <div className="farmer-screen animate-fadeInUp" id="screen-expert">
      <h2 className="screen-title">{t('expert.title')}</h2>
      <p className="screen-sub">{t('expert.subtitle')}</p>

      <div className="expert-form" id="expert-form">
        <textarea
          id="expert-question-input"
          className="expert-textarea"
          placeholder={t('expert.placeholder')}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={5}
        />
        <button
          id="btn-send-expert"
          className="primary-btn"
          disabled={!question.trim()}
          onClick={() => {
            speak(t('common.coming_soon'), i18n.language)
          }}
        >
          {t('expert.send_question')}
        </button>
      </div>

      {supported && (
        <div className="tts-controls">
          <button
            id="btn-listen-expert"
            className="tts-btn"
            onClick={() => speak(t('expert.narration'), i18n.language)}
          >
            🔊 {t('common.listen')}
          </button>
          <button className="tts-btn tts-btn-stop" onClick={stop}>
            ⏹ {t('common.stop')}
          </button>
        </div>
      )}

      <p className="coming-soon-note">{t('common.coming_soon')}</p>
    </div>
  )
}

function DroneScreen() {
  const { t, i18n } = useTranslation()
  const { speak, stop, supported } = useTTS()

  useEffect(() => {
    speak(t('drone.narration'), i18n.language)
    return () => stop()
  }, [i18n.language])

  return (
    <div className="farmer-screen animate-fadeInUp" id="screen-drone">
      <h2 className="screen-title">{t('drone.title')}</h2>
      <p className="screen-sub">{t('drone.subtitle')}</p>

      <div className="drone-card" id="drone-booking-card">
        <div className="drone-hero">🚁</div>
        <div className="drone-cost">
          <span className="cost-label">{t('drone.estimated_cost')}</span>
          <span className="cost-amount">₹400</span>
          <span className="cost-per">{t('drone.per_acre')}</span>
        </div>
        <button
          id="btn-book-drone"
          className="primary-btn primary-btn--full"
          onClick={() => speak(t('common.coming_soon'), i18n.language)}
        >
          {t('drone.book_now')}
        </button>
      </div>

      {supported && (
        <div className="tts-controls">
          <button
            id="btn-listen-drone"
            className="tts-btn"
            onClick={() => speak(t('drone.narration'), i18n.language)}
          >
            🔊 {t('common.listen')}
          </button>
          <button className="tts-btn tts-btn-stop" onClick={stop}>
            ⏹ {t('common.stop')}
          </button>
        </div>
      )}

      <p className="coming-soon-note">{t('common.coming_soon')}</p>
    </div>
  )
}

// ── Main Shell ───────────────────────────────────────────────────────────────

export default function FarmerShell() {
  const { t, i18n } = useTranslation()
  const [activeTab, setActiveTab] = useState<Tab>('scan')

  const SCREEN_MAP: Record<Tab, React.ReactElement> = {
    scan:    <ScanScreen />,
    reports: <ReportsScreen />,
    weather: <WeatherScreen />,
    expert:  <ExpertScreen />,
    drone:   <DroneScreen />,
  }

  return (
    <div className="farmer-shell" id="farmer-shell">
      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className="farmer-header" id="farmer-header">
        <div className="farmer-logo">
          <span className="logo-leaf">🌾</span>
          <span className="logo-text">{t('app_name')}</span>
        </div>
        <LanguageToggle />
      </header>

      {/* ── Screen Content ─────────────────────────────────────────── */}
      <main className="farmer-main" role="main" lang={i18n.language}>
        {SCREEN_MAP[activeTab]}
      </main>

      {/* ── Bottom Icon Nav ────────────────────────────────────────── */}
      <nav className="farmer-nav" id="farmer-nav" role="navigation" aria-label="Main navigation">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            id={`nav-btn-${item.id}`}
            className={`farmer-nav-btn ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
            aria-label={t(item.labelKey)}
            aria-current={activeTab === item.id ? 'page' : undefined}
          >
            <span className="nav-icon" aria-hidden="true">{item.icon}</span>
            <span className="nav-label">{t(item.labelKey)}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}
