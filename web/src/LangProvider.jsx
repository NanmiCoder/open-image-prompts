import { useCallback, useEffect, useMemo, useState } from 'react'
import { dict, LangContext, STORAGE_KEY } from './i18n'

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try {
      const requested = new URLSearchParams(window.location.search).get('lang')
      if (requested === 'zh' || requested === 'en') return requested
    } catch {
      // URL unavailable during non-browser rendering — use the saved preference
    }
    try {
      return localStorage.getItem(STORAGE_KEY) === 'zh' ? 'zh' : 'en'
    } catch {
      return 'en'
    }
  })

  const setLang = useCallback((next) => {
    setLangState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // storage unavailable (private mode) — session-only language
    }
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en'
    document.title =
      lang === 'zh' ? 'Open Image Prompts — AI 图片与提示词' : 'Open Image Prompts — Discover and Copy AI Prompts'
  }, [lang])

  const value = useMemo(() => {
    const table = dict[lang] || dict.en
    const t = (key, vars) => {
      let str = table[key] ?? dict.en[key] ?? key
      if (vars) {
        Object.entries(vars).forEach(([name, val]) => {
          str = str.replaceAll(`{${name}}`, String(val))
        })
      }
      return str
    }
    return { lang, setLang, t, locale: lang === 'zh' ? 'zh-CN' : 'en-US' }
  }, [lang, setLang])

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>
}
