import { ArrowClockwise, FolderOpen, Images } from '@phosphor-icons/react'
import { useEffect, useRef } from 'react'
import { useMasonryColumnCount, useMasonryColumns } from '../hooks/useMasonryColumns'
import { useLang } from '../i18n'
import PromptCard from './PromptCard'

export default function PromptGallery({
  items,
  loading,
  error,
  hasMore,
  onLoadMore,
  onRetry,
  onReset,
  onSelect,
  onCopied,
  hasActiveFilters,
  preserveOrder = false,
}) {
  const { t } = useLang()
  const sentinelRef = useRef(null)
  const requestedItemCountRef = useRef(null)
  const columnCount = useMasonryColumnCount()
  const columns = useMasonryColumns(items, columnCount)
  const visibleItemsKey = `${items[0]?.tweet_id || 'empty'}:${items.at(-1)?.tweet_id || 'empty'}:${items.length}`

  useEffect(() => {
    if (!hasMore || loading || error) return undefined

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && requestedItemCountRef.current !== visibleItemsKey) {
          requestedItemCountRef.current = visibleItemsKey
          onLoadMore()
        }
      },
      { rootMargin: '480px 0px' },
    )

    const sentinel = sentinelRef.current
    if (sentinel) observer.observe(sentinel)
    return () => observer.disconnect()
  }, [error, hasMore, loading, onLoadMore, visibleItemsKey])

  if (loading) return <GallerySkeleton columnCount={columnCount} />

  if (error) {
    return (
      <StatePanel
        icon={ArrowClockwise}
        eyebrow={t('gallery.error.eyebrow')}
        title={t('gallery.error.title')}
        description={error}
        actionLabel={t('gallery.error.action')}
        onAction={onRetry}
      />
    )
  }

  if (items.length === 0) {
    return (
      <StatePanel
        icon={FolderOpen}
        eyebrow={t('gallery.empty.eyebrow')}
        title={t('gallery.empty.title')}
        description={t('gallery.empty.description')}
        actionLabel={hasActiveFilters ? t('gallery.empty.action') : undefined}
        onAction={onReset}
      />
    )
  }

  return (
    <section className="px-5 pt-7 md:px-10" aria-label={t('gallery.label')}>
      {preserveOrder ? (
        <div className="grid grid-cols-1 items-start gap-4 min-[400px]:grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {items.map((item, index) => (
            <PromptCard
              key={item.tweet_id}
              item={item}
              index={index}
              onSelect={() => onSelect(item)}
              onCopied={onCopied}
            />
          ))}
        </div>
      ) : (
        <div className="masonry-grid" style={{ '--masonry-columns': columnCount }}>
          {columns.map((column, columnIndex) => (
            <div key={columnIndex} className="masonry-column">
              {column.map(({ item, index }) => (
                <PromptCard
                  key={item.tweet_id}
                  item={item}
                  index={index}
                  onSelect={() => onSelect(item)}
                  onCopied={onCopied}
                />
              ))}
            </div>
          ))}
        </div>
      )}

      <div ref={sentinelRef} className="flex min-h-24 items-center justify-center pt-10">
        {hasMore ? (
          <button
            type="button"
            onClick={onLoadMore}
            className="focus-ring inline-flex items-center gap-2 rounded-full border border-line px-5 py-2.5 text-xs font-medium text-body transition-colors duration-300 hover:border-line-strong hover:text-ink"
          >
            <Images size={15} />
            {t('gallery.loadMore')}
          </button>
        ) : (
          <p className="font-mono text-[10.5px] uppercase tracking-[0.22em] text-faint">
            {t('gallery.end')}
          </p>
        )}
      </div>
    </section>
  )
}

function GallerySkeleton({ columnCount }) {
  const { t } = useLang()
  const ratios = ['aspect-[4/5]', 'aspect-square', 'aspect-[3/4]', 'aspect-[5/6]', 'aspect-[4/3]', 'aspect-[3/4]']
  const skeletonItems = Array.from({ length: 15 }, (_, index) => index)
  const columns = Array.from({ length: columnCount }, () => [])
  skeletonItems.forEach((index) => columns[index % columnCount].push(index))

  return (
    <section className="px-5 pt-7 md:px-10" aria-label={t('gallery.loadingAria')}>
      <div className="masonry-grid" style={{ '--masonry-columns': columnCount }} aria-hidden="true">
        {columns.map((column, columnIndex) => (
          <div key={columnIndex} className="masonry-column">
            {column.map((index) => (
              <div key={index} className="masonry-item">
                <div className={`skeleton-shimmer rounded-[14px] outline-1 -outline-offset-1 outline-line ${ratios[index % ratios.length]}`} />
              </div>
            ))}
          </div>
        ))}
      </div>
      <span className="sr-only">{t('gallery.loadingSr')}</span>
    </section>
  )
}

function StatePanel({ icon: Icon, eyebrow, title, description, actionLabel, onAction }) {
  return (
    <section className="grid min-h-[420px] place-items-center px-5 py-16 text-center">
      <div className="max-w-md">
        <span className="mx-auto grid size-12 place-items-center rounded-2xl border border-line bg-surface text-brass">
          <Icon size={22} />
        </span>
        <p className="mt-5 font-mono text-[10px] uppercase tracking-[0.22em] text-brass">{eyebrow}</p>
        <h2 className="display-serif mt-3 text-2xl font-semibold text-ink">{title}</h2>
        <p className="mt-3 text-sm leading-relaxed text-muted">{description}</p>
        {actionLabel && (
          <button
            type="button"
            onClick={onAction}
            className="focus-ring mt-7 rounded-full bg-brass px-6 py-2.5 text-[13px] font-semibold text-abyss transition-transform hover:bg-brass-strong active:scale-[0.97]"
          >
            {actionLabel}
          </button>
        )}
      </div>
    </section>
  )
}
