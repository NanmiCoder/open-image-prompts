import {
  ArrowSquareOut,
  CaretLeft,
  CaretRight,
  Check,
  Copy,
  Play,
  WarningCircle,
  X,
} from '@phosphor-icons/react'
import { motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { writeClipboard } from '../clipboard'
import { useLang } from '../i18n'
import { mediaItems } from '../media'
import SmartImage from './ui/SmartImage'

export default function PromptDialog({ item, position, total, onClose, onStep, onCopied }) {
  const { t, locale } = useLang()
  const [currentIndex, setCurrentIndex] = useState(0)
  const [copyState, setCopyState] = useState('idle')
  const [showOriginal, setShowOriginal] = useState(true)
  const closeButtonRef = useRef(null)
  const resetTimerRef = useRef(null)
  const media = mediaItems(item)
  const currentMedia = media[currentIndex]
  const hasReadingTranslation = Boolean(item.localized_prompt && item.localized_prompt !== item.prompt_text)
  const displayedPrompt = showOriginal || !hasReadingTranslation ? item.prompt_text : item.localized_prompt

  const showPrevious = () => {
    setCurrentIndex((index) => (index - 1 + media.length) % media.length)
  }

  const showNext = () => {
    setCurrentIndex((index) => (index + 1) % media.length)
  }

  useEffect(() => {
    setCurrentIndex(0)
    setCopyState('idle')
    setShowOriginal(true)
    window.clearTimeout(resetTimerRef.current)
  }, [item.tweet_id])

  useEffect(() => {
    const previousFocus = document.activeElement
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeButtonRef.current?.focus()

    function handleKeyDown(event) {
      if (event.key === 'Escape') onClose()
      if (event.key === 'ArrowLeft') onStep(-1)
      if (event.key === 'ArrowRight') onStep(1)
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = previousOverflow
      previousFocus?.focus?.()
      window.clearTimeout(resetTimerRef.current)
    }
  }, [onClose, onStep])

  function mediaLabel(entry, index) {
    return entry.type === 'video-link'
      ? t('dialog.media.video', { n: index + 1 })
      : t('dialog.media.image', { n: index + 1 })
  }

  const date = new Date(item.created_at)
  const fullDate = Number.isNaN(date.getTime())
    ? ''
    : new Intl.DateTimeFormat(locale, { year: 'numeric', month: 'long', day: 'numeric' }).format(date)

  async function copyPrompt() {
    try {
      await writeClipboard(item.prompt_text)
      setCopyState('copied')
      onCopied?.(t('card.copied'))
    } catch {
      setCopyState('error')
    }

    window.clearTimeout(resetTimerRef.current)
    resetTimerRef.current = window.setTimeout(() => setCopyState('idle'), 2200)
  }

  return (
    <motion.div
      role="dialog"
      aria-modal="true"
      aria-labelledby="prompt-dialog-title"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.22 }}
      className="fixed inset-0 z-40 grid place-items-center bg-abyss/85 p-0 backdrop-blur-xl md:p-8"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 32, scale: 0.985 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.985 }}
        transition={{ type: 'spring', stiffness: 260, damping: 28 }}
        className="relative grid h-[100dvh] w-full grid-rows-[44dvh_minmax(0,1fr)] overflow-hidden bg-canvas md:h-[min(88dvh,860px)] md:max-w-[1280px] md:grid-cols-[minmax(0,1.4fr)_minmax(360px,0.72fr)] md:grid-rows-1 md:rounded-3xl md:border md:border-line md:shadow-[0_48px_140px_-40px_rgba(0,0,0,0.9)]"
      >
        <section className="relative min-h-[44dvh] overflow-hidden bg-abyss md:min-h-0" aria-label="Media">
          {currentMedia?.type === 'video-link' ? (
            <VideoPreview media={currentMedia} />
          ) : currentMedia ? (
            <>
              <img
                src={currentMedia.sources[0]}
                alt=""
                aria-hidden="true"
                className="absolute inset-0 h-full w-full scale-125 object-cover opacity-25 blur-2xl"
              />
              <SmartImage
                sources={currentMedia.sources}
                alt={`${mediaLabel(currentMedia, currentIndex)} — @${item.author}`}
                className="relative h-full w-full"
                eager
                fit="contain"
              />
            </>
          ) : (
            <div className="grid h-full place-items-center text-sm text-muted">{t('dialog.noMedia')}</div>
          )}

          <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-abyss/80 to-transparent" />

          <div className="absolute left-4 top-4 flex items-center gap-2 md:left-5 md:top-5">
            <div className="flex items-center gap-1 rounded-full border border-white/12 bg-abyss/60 p-1 backdrop-blur-md">
              <button
                type="button"
                onClick={() => onStep(-1)}
                aria-label={t('dialog.prevItem')}
                className="focus-ring grid size-7 place-items-center rounded-full text-white/80 transition-colors hover:bg-white/10 hover:text-white"
              >
                <CaretLeft size={15} />
              </button>
              <span className="min-w-[68px] text-center font-mono text-[10.5px] tabular-nums text-white/70">
                {position} / {total}
              </span>
              <button
                type="button"
                onClick={() => onStep(1)}
                aria-label={t('dialog.nextItem')}
                className="focus-ring grid size-7 place-items-center rounded-full text-white/80 transition-colors hover:bg-white/10 hover:text-white"
              >
                <CaretRight size={15} />
              </button>
            </div>
            {media.length > 1 && (
              <span className="rounded-full border border-white/12 bg-abyss/60 px-3 py-1.5 font-mono text-[10px] text-white/70 backdrop-blur-md">
                {currentIndex + 1} / {media.length}
              </span>
            )}
          </div>

          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="focus-ring absolute right-4 top-4 grid size-10 place-items-center rounded-full border border-white/12 bg-abyss/60 text-white/85 backdrop-blur-md transition-colors hover:bg-white/10 hover:text-white md:right-5 md:top-5"
            aria-label={t('dialog.close')}
          >
            <X size={17} />
          </button>

          {media.length > 1 && (
            <>
              <MediaNavButton direction="left" onClick={showPrevious} label={t('dialog.prevMedia')}>
                <CaretLeft size={17} />
              </MediaNavButton>
              <MediaNavButton direction="right" onClick={showNext} label={t('dialog.nextMedia')}>
                <CaretRight size={17} />
              </MediaNavButton>
              <div className="absolute bottom-4 left-1/2 flex -translate-x-1/2 gap-1.5 rounded-full border border-white/12 bg-abyss/60 p-2 backdrop-blur-md">
                {media.map((entry, index) => (
                  <button
                    key={`${entry.type}-${index}`}
                    type="button"
                    onClick={() => setCurrentIndex(index)}
                    aria-label={t('dialog.mediaLabel', { label: mediaLabel(entry, index) })}
                    aria-current={index === currentIndex}
                    className={`h-1.5 rounded-full transition-[width,background-color] duration-300 ${
                      index === currentIndex ? 'w-6 bg-brass' : 'w-1.5 bg-white/35 hover:bg-white/60'
                    }`}
                  />
                ))}
              </div>
            </>
          )}

          <p className="pointer-events-none absolute bottom-4 right-4 hidden items-center gap-1.5 font-mono text-[10px] text-white/40 md:flex">
            <span className="kbd">←</span>
            <span className="kbd">→</span>
            {t('dialog.stepHint')}
          </p>
        </section>

        <section className="custom-scrollbar flex min-h-0 flex-col overflow-y-auto border-t border-line bg-canvas md:border-l md:border-t-0">
          <div className="border-b border-line px-5 py-5 md:px-7 md:py-6">
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-brass">{t('dialog.record')}</p>
            <div className="mt-3 flex items-start justify-between gap-5">
              <div className="min-w-0">
                <h2 id="prompt-dialog-title" className="display-serif truncate text-2xl font-semibold text-ink">
                  @{item.author}
                </h2>
                <p className="mt-1.5 font-mono text-[11px] text-muted">{fullDate}</p>
              </div>
              <a
                href={item.tweet_url}
                target="_blank"
                rel="noopener noreferrer"
                className="focus-ring hidden shrink-0 items-center gap-1.5 rounded-full border border-line px-3.5 py-2 text-xs font-medium text-body transition-colors hover:border-line-strong hover:text-ink sm:inline-flex"
              >
                {t('dialog.viewPost')}
                <ArrowSquareOut size={13} />
              </a>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {item.tool && item.tool !== 'None' && <MetaTag accent>{item.tool}</MetaTag>}
              <MetaTag>
                {t(`dialog.images.${(item.images?.length || 0) === 1 ? 'one' : 'other'}`, { n: item.images?.length || 0 })}
              </MetaTag>
              {item.videos?.length > 0 && (
                <MetaTag>{t(`dialog.videos.${item.videos.length === 1 ? 'one' : 'other'}`, { n: item.videos.length })}</MetaTag>
              )}
            </div>
          </div>

          <div className="flex flex-1 flex-col px-5 py-5 md:px-7 md:py-6">
            <div className="mb-3.5 flex items-center justify-between gap-4">
              <div>
                <h3 className="text-[13px] font-semibold text-ink">{t('dialog.fullPrompt')}</h3>
                <p className="mt-0.5 font-mono text-[10.5px] text-faint">{t('dialog.promptNote')}</p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {hasReadingTranslation && (
                  <button
                    type="button"
                    onClick={() => setShowOriginal((value) => !value)}
                    className="focus-ring rounded-full border border-line px-3 py-2.5 text-xs font-medium text-body transition-colors hover:border-line-strong hover:text-ink"
                  >
                    {showOriginal ? t('dialog.showTranslation') : t('dialog.showOriginal')}
                  </button>
                )}
                <button
                  type="button"
                  onClick={copyPrompt}
                  className={`focus-ring inline-flex min-w-[104px] shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-full px-4 py-2.5 text-xs font-semibold transition-colors active:scale-[0.97] ${
                    copyState === 'error'
                      ? 'bg-error-soft text-error'
                      : copyState === 'copied'
                        ? 'bg-brass-soft text-brass-strong'
                        : 'bg-brass text-abyss hover:bg-brass-strong'
                  }`}
                >
                  {copyState === 'copied' ? <Check size={14} /> : copyState === 'error' ? <WarningCircle size={14} /> : <Copy size={14} />}
                  {copyState === 'copied' ? t('dialog.copied') : copyState === 'error' ? t('dialog.copyFailed') : hasReadingTranslation ? t('dialog.copyOriginal') : t('dialog.copy')}
                </button>
              </div>
            </div>

            <div className="flex-1 rounded-2xl border border-line bg-abyss/60 p-4 md:p-5">
              <pre className="prompt-pre">{displayedPrompt}</pre>
            </div>

            <a
              href={item.tweet_url}
              target="_blank"
              rel="noopener noreferrer"
              className="focus-ring mt-4 inline-flex items-center justify-center gap-2 rounded-full border border-line px-4 py-3 text-xs font-medium text-body sm:hidden"
            >
              {t('dialog.viewPost')}
              <ArrowSquareOut size={14} />
            </a>
          </div>
        </section>
      </motion.div>
    </motion.div>
  )
}

function VideoPreview({ media }) {
  const { t } = useLang()
  return (
    <div className="relative grid h-full place-items-center">
      {media.sources.length > 0 && (
        <SmartImage sources={media.sources} alt="Video preview" className="absolute inset-0 h-full w-full opacity-60" eager />
      )}
      <a
        href={media.url}
        target="_blank"
        rel="noopener noreferrer"
        className="focus-ring relative inline-flex items-center gap-2 rounded-full bg-brass px-5 py-3 text-sm font-semibold text-abyss shadow-[0_16px_40px_-16px_rgba(0,0,0,0.8)] transition-transform active:scale-[0.97]"
      >
        <Play size={16} weight="fill" />
        {t('dialog.openVideo')}
        <ArrowSquareOut size={14} />
      </a>
    </div>
  )
}

function MediaNavButton({ direction, onClick, label, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className={`focus-ring absolute top-1/2 grid size-10 -translate-y-1/2 place-items-center rounded-full border border-white/12 bg-abyss/60 text-white/85 backdrop-blur-md transition-colors hover:bg-white/10 hover:text-white ${
        direction === 'left' ? 'left-4' : 'right-4'
      }`}
    >
      {children}
    </button>
  )
}

function MetaTag({ children, accent = false }) {
  return (
    <span
      className={`rounded-full px-3 py-1 text-[11px] font-medium ${
        accent ? 'bg-brass-soft text-brass-strong' : 'bg-overlay text-body'
      }`}
    >
      {children}
    </span>
  )
}
