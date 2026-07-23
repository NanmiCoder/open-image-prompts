import { Copy, Play } from '@phosphor-icons/react'
import { motion } from 'framer-motion'
import { writeClipboard } from '../clipboard'
import { useLang } from '../i18n'
import { firstImageSources } from '../media'
import SmartImage from './ui/SmartImage'

function excerpt(text, limit = 120) {
  const normalized = String(text || '').replace(/\s+/g, ' ').trim()
  return normalized.length > limit ? `${normalized.slice(0, limit)}…` : normalized
}

function reasonLabel(reason) {
  if (typeof reason === 'string') return reason
  if (!reason || typeof reason !== 'object') return ''
  if (reason.value) return reason.value
  if (reason.values?.length) return reason.values.slice(0, 2).join(' · ')
  if (reason.type === 'image_available' && reason.count) return `${reason.count} images`
  return ''
}

export default function PromptCard({ item, index, onSelect, onCopied }) {
  const { t, locale } = useLang()
  const imageCount = item.images?.length || 0
  const hasVideo = Boolean(item.videos?.length)
  const tool = item.tool && item.tool !== 'None' ? item.tool : null
  const ratio = item._ratio && item._ratio > 0.2 && item._ratio < 5 ? item._ratio : null
  const matchReasons = (item.session_reference?.match_reasons || [])
    .map(reasonLabel)
    .filter(Boolean)
    .slice(0, 2)

  const date = new Date(item.created_at)
  const dateLabel = Number.isNaN(date.getTime())
    ? ''
    : new Intl.DateTimeFormat(locale, { month: 'short', day: 'numeric' }).format(date)

  async function handleCopy(event) {
    event.stopPropagation()
    try {
      await writeClipboard(item.prompt_text)
      onCopied?.(t('card.copied'))
    } catch {
      onCopied?.(t('card.copyFailed'))
    }
  }

  return (
    <motion.article
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        opacity: { duration: 0.3, delay: Math.min((index % 24) * 0.015, 0.18) },
        y: { type: 'spring', stiffness: 140, damping: 24, delay: Math.min((index % 24) * 0.015, 0.18) },
      }}
      data-prompt-id={item.tweet_id}
      className="masonry-item relative"
    >
      <button
        type="button"
        onClick={onSelect}
        className="wall-card focus-ring block w-full text-left"
        style={ratio ? { aspectRatio: `${ratio}` } : undefined}
        aria-label={t('card.open', { author: item.author })}
      >
        <SmartImage
          sources={firstImageSources(item)}
          alt={t('card.alt', { author: item.author })}
          className={`h-full w-full ${ratio ? '' : 'aspect-[4/5]'}`}
          eager={index < 6}
        />

        <div className="card-top pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between gap-2 bg-gradient-to-b from-abyss/70 to-transparent p-2.5 pb-7">
          {tool ? (
            <span className="rounded-full border border-white/12 bg-abyss/55 px-2.5 py-1 font-mono text-[10px] font-medium text-white/85 backdrop-blur-md">
              {tool}
            </span>
          ) : (
            <span />
          )}
          {(imageCount > 1 || hasVideo) && (
            <span className="inline-flex items-center gap-1 rounded-full border border-white/12 bg-abyss/55 px-2.5 py-1 font-mono text-[10px] text-white/85 backdrop-blur-md">
              {hasVideo ? (
                <>
                  <Play size={10} weight="fill" /> {t('card.video')}
                </>
              ) : (
                t('card.imageCount', { n: imageCount })
              )}
            </span>
          )}
        </div>

        <div className="card-veil pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-abyss/95 via-abyss/75 to-transparent px-3.5 pb-3.5 pt-14">
          {matchReasons.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-1">
              {matchReasons.map((reason, reasonIndex) => (
                <span key={`${reason}-${reasonIndex}`} className="rounded-full border border-brass/35 bg-abyss/70 px-2 py-0.5 font-mono text-[9px] text-brass-soft">
                  {reason}
                </span>
              ))}
            </div>
          )}
          <p className="line-clamp-2 text-[12px] leading-relaxed text-white/88">{excerpt(item.localized_prompt || item.prompt_text)}</p>
          <p className="mt-2 truncate font-mono text-[10.5px] text-white/55">
            @{item.author}
            {dateLabel && <span className="text-white/30"> · {dateLabel}</span>}
          </p>
        </div>
      </button>

      <button
        type="button"
        onClick={handleCopy}
        aria-label={t('card.copyAria')}
        className="card-copy focus-ring absolute bottom-3 right-3 z-10 inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-white/10 px-2.5 py-1 text-[10.5px] font-medium text-white/85 backdrop-blur-md hover:bg-brass hover:text-abyss"
      >
        <Copy size={11} />
        {t('card.copy')}
      </button>
    </motion.article>
  )
}
