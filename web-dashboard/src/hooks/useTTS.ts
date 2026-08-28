/**
 * useTTS — Web Speech API TTS hook.
 *
 * Uses the browser's built-in SpeechSynthesis API.
 * - No API key needed
 * - Works on Chrome Android (and Chrome desktop)
 * - Automatically selects the best voice for the current language
 * - Safe: gracefully no-ops if SpeechSynthesis is unavailable
 *
 * Phase 6 upgrade path: swap the synth.speak() call with a Bhashini / Google TTS
 * API call here without touching any component.
 */
import { useCallback, useEffect, useRef } from 'react'

const LANG_TO_BCP47: Record<string, string> = {
  en: 'en-IN',
  hi: 'hi-IN',
}

export function useTTS() {
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window

  // Pre-load voices (Chrome requires a trigger)
  useEffect(() => {
    if (!supported) return
    window.speechSynthesis.getVoices()
  }, [supported])

  const speak = useCallback(
    (text: string, lang: string) => {
      if (!supported || !text) return

      // Cancel any ongoing speech first
      window.speechSynthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = LANG_TO_BCP47[lang] ?? 'en-IN'
      utterance.rate = 0.9
      utterance.pitch = 1.05

      // Pick the best available voice for the language
      const voices = window.speechSynthesis.getVoices()
      const preferred = voices.find(
        (v) => v.lang.startsWith(utterance.lang.split('-')[0]) && v.localService
      ) ?? voices.find(
        (v) => v.lang.startsWith(utterance.lang.split('-')[0])
      )
      if (preferred) utterance.voice = preferred

      utteranceRef.current = utterance
      window.speechSynthesis.speak(utterance)
    },
    [supported]
  )

  const stop = useCallback(() => {
    if (!supported) return
    window.speechSynthesis.cancel()
  }, [supported])

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (supported) window.speechSynthesis.cancel()
    }
  }, [supported])

  return { speak, stop, supported }
}
