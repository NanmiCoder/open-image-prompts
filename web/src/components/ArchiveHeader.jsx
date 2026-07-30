import { motion } from 'framer-motion'
import { useEffect, useMemo, useState } from 'react'
import { LANG_OPTIONS, useLang } from '../i18n'
import { firstImageSources } from '../media'
import SmartImage from './ui/SmartImage'

const statKeys = ['prompts', 'images', 'authors', 'tools']

function useCountUp(target, duration = 1400) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    if (!target) return undefined
    let raf
    const start = performance.now()
    const tick = (now) => {
      const t = Math.min((now - start) / duration, 1)
      setValue(Math.round(target * (1 - Math.pow(1 - t, 4))))
      if (t < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target, duration])

  return value
}

function Stat({ value, label, loading }) {
  const { locale } = useLang()
  const count = useCountUp(loading ? 0 : value)
  return (
    <div className="min-w-0">
      <p className="display-num text-[clamp(1.55rem,2.3vw,2.25rem)] leading-none text-ink tabular-nums">
        {loading ? '—' : count.toLocaleString(locale)}
      </p>
      <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.18em] text-muted">{label}</p>
    </div>
  )
}

const GITHUB_REPO_URL = 'https://github.com/NanmiCoder/open-image-prompts'

function GithubLink() {
  const { t } = useLang()
  return (
    <a
      href={GITHUB_REPO_URL}
      target="_blank"
      rel="noreferrer"
      aria-label={t('nav.github')}
      title={t('nav.github')}
      className="focus-ring group grid size-8 place-items-center rounded-full border border-line bg-surface/60 text-muted transition-colors duration-300 hover:border-line-strong hover:bg-elevate hover:text-ink"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true" className="size-4 transition-transform duration-300 group-hover:scale-110">
        <path
          fill="currentColor"
          d="M12 2C6.48 2 2 6.58 2 12.22c0 4.52 2.87 8.35 6.84 9.7.5.1.68-.22.68-.49 0-.24-.01-1.04-.01-1.89-2.78.62-3.37-1.22-3.37-1.22-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.63.07-.63 1 .07 1.53 1.06 1.53 1.06.9 1.56 2.35 1.11 2.92.85.09-.66.35-1.11.63-1.37-2.22-.26-4.55-1.14-4.55-5.06 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.28 2.75 1.05A9.32 9.32 0 0 1 12 5.92c.85 0 1.7.12 2.5.34 1.9-1.33 2.74-1.05 2.74-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.93-2.34 4.79-4.56 5.05.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.81 0 .27.18.59.69.49A10.04 10.04 0 0 0 22 12.22C22 6.58 17.52 2 12 2Z"
        />
      </svg>
      <span className="sr-only">{t('nav.github')}</span>
    </a>
  )
}

function LangSwitch() {
  const { lang, setLang } = useLang()
  return (
    <div className="grid grid-cols-2 rounded-full border border-line bg-surface/60 p-0.5" role="group" aria-label="Language / 语言">
      {LANG_OPTIONS.map((option) => (
        <button
          key={option.code}
          type="button"
          onClick={() => setLang(option.code)}
          aria-pressed={lang === option.code}
          aria-label={option.label}
          className={`focus-ring grid h-7 min-w-[34px] place-items-center rounded-full px-2 font-mono text-[11px] font-medium transition-colors duration-300 ${
            lang === option.code ? 'bg-ink text-abyss' : 'text-muted hover:text-ink'
          }`}
        >
          {option.short}
        </button>
      ))}
    </div>
  )
}

function Marquee({ items, onSelect }) {
  const { t } = useLang()
  const slides = useMemo(() => {
    const picks = items.filter((item) => firstImageSources(item).length > 0).slice(0, 28)
    return [...picks, ...picks]
  }, [items])

  if (slides.length === 0) return null

  const uniqueCount = slides.length / 2

  return (
    <div className="marquee-mask relative overflow-hidden border-t border-line py-3" aria-label={t('gallery.featured')}>
      <div className="marquee-track gap-3 pr-3">
        {slides.map((item, index) => {
          const isDuplicate = index >= uniqueCount
          return (
            <button
              key={`${item.tweet_id}-${index}`}
              type="button"
              tabIndex={isDuplicate ? -1 : 0}
              onClick={() => onSelect?.(item)}
              aria-label={t('card.open', { author: item.author })}
              className={`focus-ring h-20 shrink-0 overflow-hidden rounded-lg text-left outline-1 -outline-offset-1 outline-line transition-[outline-color,transform,filter] duration-300 hover:outline-line-strong hover:brightness-110 active:scale-[0.98] md:h-28 ${item._ratio ? '' : 'aspect-[4/3]'}`}
              style={item._ratio ? { aspectRatio: `${item._ratio}` } : undefined}
            >
              <SmartImage
                sources={firstImageSources(item)}
                alt={isDuplicate ? '' : t('card.alt', { author: item.author })}
                eager={index < 8}
                className="h-full w-full"
              />
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default function ArchiveHeader({ stats, loading, items, onSelect }) {
  const { t } = useLang()

  return (
    <header className="relative overflow-hidden border-b border-line">
      <div className="hero-spotlight" aria-hidden="true" />

      <div className="relative mx-auto w-full max-w-[1760px] px-5 md:px-10">
        <nav className="flex h-16 items-center justify-between border-b border-line" aria-label={t('nav.label')}>
          <a href="./" className="group inline-flex items-center gap-3 focus-ring">
            <span className="grid size-8 place-items-center rounded-lg bg-brass font-mono text-[13px] font-bold text-abyss transition-transform duration-300 group-hover:-rotate-6">
              OI
            </span>
            <span className="text-sm font-semibold tracking-tight">Open Image Prompts</span>
          </a>

          <div className="flex items-center gap-4">
            <div className="hidden items-center gap-2.5 font-mono text-[11px] uppercase tracking-[0.16em] text-muted md:inline-flex">
              <span className="status-pulse" aria-hidden="true" />
              {t('nav.status')}
            </div>
            <GithubLink />
            <LangSwitch />
          </div>
        </nav>

        <div className="grid gap-8 py-9 md:grid-cols-[minmax(0,1fr)_minmax(32rem,0.9fr)] md:items-end md:gap-12 md:py-11 xl:gap-20">
          <div className="min-w-0">
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="eyebrow flex flex-wrap items-center gap-x-4 gap-y-2 text-brass"
            >
              {t('hero.eyebrow')}
              <span className="hidden h-px w-8 bg-brass/40 sm:inline-block" aria-hidden="true" />
              <span className="text-muted">{t('hero.eyebrow.suffix')}</span>
            </motion.p>

            <motion.h1
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.65, delay: 0.06, ease: [0.16, 1, 0.3, 1] }}
              className="mt-4 max-w-[16ch] text-[clamp(2.25rem,5vw,4.75rem)] font-semibold leading-[1.02] tracking-[-0.045em] text-ink"
            >
              {t('hero.title')}
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.14, ease: [0.16, 1, 0.3, 1] }}
              className="mt-4 max-w-[48ch] text-[14px] leading-relaxed text-body md:text-[15px]"
            >
              {t('hero.description')}
            </motion.p>
          </div>

          <motion.dl
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="grid grid-cols-2 gap-x-6 gap-y-6 border-t border-line pt-6 md:border-l md:border-t-0 md:py-2 md:pl-8 xl:pl-12"
          >
            {statKeys.map((key) => (
              <Stat key={key} value={stats[key]} label={t(`hero.stats.${key}`)} loading={loading} />
            ))}
          </motion.dl>
        </div>
      </div>

      <Marquee items={items} onSelect={onSelect} />
      <div className="hero-hairline" aria-hidden="true" />
    </header>
  )
}
