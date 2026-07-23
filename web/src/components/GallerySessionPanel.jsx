import { Check, Copy, Sparkle, WarningCircle } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { writeClipboard } from '../clipboard'
import { localizedDerivedPrompt } from '../gallerySession'
import { useLang } from '../i18n'

export default function GallerySessionPanel({ session, missingReferences = [], onCopied }) {
  const { lang, t } = useLang()
  const [copyState, setCopyState] = useState('idle')
  const prompt = localizedDerivedPrompt(session, lang)

  useEffect(() => setCopyState('idle'), [session?.session_id, prompt])

  async function copyDerivedPrompt() {
    try {
      await writeClipboard(prompt)
      setCopyState('copied')
      onCopied?.(t('session.copied'))
    } catch {
      setCopyState('error')
    }
  }

  if (!session) return null

  return (
    <section className="mx-5 mt-5 rounded-3xl border border-brass/25 bg-[linear-gradient(135deg,rgba(210,168,92,0.12),rgba(255,255,255,0.02))] p-5 md:mx-10 md:mt-8 md:p-7" aria-label={t('session.label')}>
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 max-w-4xl">
          <p className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.22em] text-brass">
            <Sparkle size={14} weight="fill" />
            {t('session.eyebrow')}
          </p>
          <h2 className="display-serif mt-3 text-2xl font-semibold text-ink">{session.intent || t('session.untitled')}</h2>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            {t('session.references', { n: session.references.length })}
          </p>
          {missingReferences.length > 0 && (
            <p className="mt-2 text-xs text-error">
              {t('session.missing', { n: missingReferences.length })}
            </p>
          )}
        </div>

        {prompt && (
          <button
            type="button"
            onClick={copyDerivedPrompt}
            className={`focus-ring inline-flex shrink-0 items-center justify-center gap-2 rounded-full px-5 py-3 text-xs font-semibold transition-colors active:scale-[0.97] ${
              copyState === 'error'
                ? 'bg-error-soft text-error'
                : copyState === 'copied'
                  ? 'bg-brass-soft text-brass-strong'
                  : 'bg-brass text-abyss hover:bg-brass-strong'
            }`}
          >
            {copyState === 'copied' ? <Check size={15} /> : copyState === 'error' ? <WarningCircle size={15} /> : <Copy size={15} />}
            {copyState === 'copied' ? t('session.copied') : copyState === 'error' ? t('session.copyFailed') : t('session.copy')}
          </button>
        )}
      </div>

      {prompt && (
        <div className="mt-5 rounded-2xl border border-line bg-abyss/55 p-4 md:p-5">
          <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-faint">{t('session.derived')}</p>
          <pre className="prompt-pre max-h-56 overflow-y-auto">{prompt}</pre>
        </div>
      )}
    </section>
  )
}
