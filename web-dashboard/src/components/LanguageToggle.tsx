/**
 * LanguageToggle — EN / हिं pill toggle.
 * Reads/writes i18n language. Also stops any ongoing TTS.
 */
import { useTranslation } from 'react-i18next'

interface Props {
  onToggle?: () => void
}

export default function LanguageToggle({ onToggle }: Props) {
  const { i18n } = useTranslation()
  const isHindi = i18n.language === 'hi'

  const toggle = () => {
    const next = isHindi ? 'en' : 'hi'
    i18n.changeLanguage(next)
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
    onToggle?.()
  }

  return (
    <button
      id="language-toggle"
      className="lang-toggle"
      onClick={toggle}
      aria-label={isHindi ? 'Switch to English' : 'हिंदी में बदलें'}
      title={isHindi ? 'Switch to English' : 'हिंदी में बदलें'}
    >
      <span className={`lang-pill ${!isHindi ? 'active' : ''}`}>EN</span>
      <span className={`lang-pill ${isHindi ? 'active' : ''}`}>हिं</span>
    </button>
  )
}
