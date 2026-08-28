/**
 * i18next setup for Kisan Saathi.
 *
 * Languages: English (en), Hindi (hi)
 * Storage:   localStorage key "ks_lang" — persists across sessions
 * Fallback:  en → if a key is missing in hi, English is shown rather than crashing
 */
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './locales/en.json'
import hi from './locales/hi.json'

const savedLang = localStorage.getItem('ks_lang') ?? 'hi'

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      hi: { translation: hi },
    },
    lng: savedLang,
    fallbackLng: 'en',

    // Never throw on missing key — return key path instead (safe for TTS too)
    missingKeyHandler: (_lngs, _ns, key) => {
      console.warn('[i18n] Missing key:', key)
    },
    saveMissing: false,
    interpolation: {
      escapeValue: false, // React already escapes
    },
  })

// Persist language choice whenever it changes
i18n.on('languageChanged', (lang) => {
  localStorage.setItem('ks_lang', lang)
  document.documentElement.lang = lang
})

export default i18n
