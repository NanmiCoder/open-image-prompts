import {
  MagnifyingGlass,
  SortAscending,
  SortDescending,
  X,
} from '@phosphor-icons/react'
import { useRef } from 'react'
import { useLang } from '../i18n'
import SelectMenu from './ui/SelectMenu'

const CHIP_LIMIT = 8
const TAG_CHIP_LIMIT = 10

function formatCount(count) {
  return count >= 1000 ? `${(count / 1000).toFixed(1)}k` : String(count)
}

export default function FilterBar({
  query,
  activeQuery,
  queryDirty,
  onQueryChange,
  onQuerySubmit,
  onQueryClear,
  searchInputRef,
  popularTools,
  tools,
  selectedTool,
  onToolChange,
  authors,
  selectedAuthor,
  onAuthorChange,
  popularTags = [],
  tags = [],
  selectedTag,
  onTagChange,
  sortOrder,
  onSortChange,
  resultCount,
  hasActiveFilters,
  onReset,
  disabled,
}) {
  const { t, locale } = useLang()
  const composingRef = useRef(false)
  const chipTools = popularTools.slice(0, CHIP_LIMIT)
  const chipTags = popularTags.slice(0, TAG_CHIP_LIMIT)
  const selectedInChips = !selectedTool || chipTools.some(({ tool }) => tool === selectedTool)
  const selectedTagInChips = !selectedTag || chipTags.some(({ tagValue }) => tagValue === selectedTag)
  const selectedTagLabel = tags.find((tag) => tag.value === selectedTag)?.label || selectedTag

  return (
    <section className="glass-bar sticky top-0 z-30 border-b border-line">
      <div className="mx-auto w-full max-w-[1760px] px-5 py-4 md:px-10">
        <div className="flex flex-wrap items-center gap-3">
          <form
            role="search"
            className="flex w-full min-w-0 items-center gap-2 sm:w-auto sm:flex-1"
            onSubmit={(event) => {
              event.preventDefault()
              if (!composingRef.current) onQuerySubmit()
            }}
          >
            <div className="relative min-w-0 flex-1">
              <MagnifyingGlass
                size={16}
                className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted"
              />
              <input
                ref={searchInputRef}
                type="search"
                value={query}
                onChange={(event) => onQueryChange(event.target.value)}
                onCompositionStart={() => {
                  composingRef.current = true
                }}
                onCompositionEnd={() => {
                  composingRef.current = false
                }}
                onKeyDown={(event) => {
                  if (
                    event.key === 'Enter'
                    && (composingRef.current || event.nativeEvent.isComposing || event.keyCode === 229)
                  ) {
                    event.preventDefault()
                  }
                  if (event.key === 'Escape' && query) {
                    event.preventDefault()
                    onQueryClear()
                  }
                }}
                enterKeyHint="search"
                disabled={disabled}
                placeholder={t('filter.search.placeholder')}
                aria-describedby={queryDirty ? 'search-pending-hint' : undefined}
                className="search-input focus-ring h-11 w-full rounded-full border border-line bg-surface/80 pl-11 pr-11 text-[13.5px] text-ink placeholder:text-faint transition-colors hover:border-line-strong disabled:cursor-not-allowed disabled:opacity-50"
              />
              {query && (
                <button
                  type="button"
                  onClick={onQueryClear}
                  className="focus-ring absolute right-3.5 top-1/2 grid size-7 -translate-y-1/2 place-items-center rounded-full text-muted transition-colors hover:bg-overlay hover:text-ink"
                  aria-label={t('filter.search.clear')}
                >
                  <X size={13} />
                </button>
              )}
            </div>
            <button
              type="submit"
              disabled={disabled || !queryDirty}
              aria-label={t('filter.search.submit')}
              className="focus-ring inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-full bg-brass px-4 text-xs font-semibold text-abyss transition-colors hover:bg-brass-strong disabled:cursor-not-allowed disabled:bg-elevate disabled:text-faint"
            >
              <MagnifyingGlass size={15} weight="bold" />
              <span className="hidden sm:inline">{t('filter.search.submit')}</span>
            </button>
            <span id="search-pending-hint" className="sr-only" aria-live="polite">
              {queryDirty ? t('filter.search.pending') : ''}
            </span>
          </form>

          <div className="grid h-11 shrink-0 grid-cols-2 rounded-full border border-line bg-surface/80 p-1">
            <SortButton
              active={sortOrder === 'newest'}
              onClick={() => onSortChange('newest')}
              label={t('filter.sort.newest')}
              icon={SortDescending}
              disabled={disabled}
            />
            <SortButton
              active={sortOrder === 'oldest'}
              onClick={() => onSortChange('oldest')}
              label={t('filter.sort.oldest')}
              icon={SortAscending}
              disabled={disabled}
            />
          </div>

          <p
            className="shrink-0 font-mono text-[11px] tabular-nums tracking-wide text-muted max-sm:ml-auto"
            aria-live="polite"
            aria-atomic="true"
          >
            <span className="text-brass">{new Intl.NumberFormat(locale).format(resultCount)}</span>
            {t('filter.results').replace('{n}', '')}
          </p>
        </div>

        <div className="mt-3.5 flex flex-wrap items-center gap-2.5">
          <div className="chip-row order-1 flex w-full min-w-0 items-center gap-2 overflow-x-auto py-0.5 lg:order-none lg:w-auto lg:flex-1">
            <button type="button" className="chip focus-ring" data-active={!selectedTool} onClick={() => onToolChange('')} disabled={disabled}>
              {t('filter.allTools')}
            </button>
            {chipTools.map(({ tool, count }) => (
              <button
                key={tool}
                type="button"
                className="chip focus-ring"
                data-active={selectedTool === tool}
                onClick={() => onToolChange(selectedTool === tool ? '' : tool)}
                disabled={disabled}
              >
                {tool}
                <span className="chip-count">{formatCount(count)}</span>
              </button>
            ))}
          </div>

          {tools.length > CHIP_LIMIT && (
            <div className="order-2 shrink-0 lg:order-none">
              <SelectMenu
                compact
                value={selectedInChips ? '' : selectedTool}
                options={tools}
                onChange={onToolChange}
                emptyLabel={t('filter.moreTools')}
                resetLabel={t('filter.allTools')}
                searchable
                searchPlaceholder={t('filter.searchTools')}
                disabled={disabled}
              />
            </div>
          )}

          <div className="order-3 min-w-0 flex-1 lg:order-none lg:w-48 lg:flex-none">
            <SelectMenu
              compact
              value={selectedAuthor}
              displayValue={selectedAuthor ? `@${selectedAuthor}` : ''}
              options={authors}
              onChange={onAuthorChange}
              emptyLabel={t('filter.allAuthors')}
              searchable
              searchPlaceholder={t('filter.searchAuthors')}
              disabled={disabled}
            />
          </div>

          {tags.length > 0 && (
            <div className="order-4 flex w-full min-w-0 items-center gap-2">
              <div className="chip-row flex min-w-0 flex-1 items-center gap-2 overflow-x-auto py-0.5">
                <button type="button" className="chip focus-ring" data-active={!selectedTag} onClick={() => onTagChange('')} disabled={disabled}>
                  {t('filter.allTags')}
                </button>
                {chipTags.map(({ tagValue, label, count }) => (
                  <button
                    key={tagValue}
                    type="button"
                    className="chip focus-ring"
                    data-active={selectedTag === tagValue}
                    onClick={() => onTagChange(selectedTag === tagValue ? '' : tagValue)}
                    disabled={disabled}
                  >
                    {label || tagValue}
                    <span className="chip-count">{formatCount(count)}</span>
                  </button>
                ))}
              </div>
              {tags.length > TAG_CHIP_LIMIT && (
                <div className="shrink-0">
                  <SelectMenu
                    compact
                    value={selectedTagInChips ? '' : selectedTag}
                    options={tags}
                    onChange={onTagChange}
                    emptyLabel={t('filter.moreTags')}
                    resetLabel={t('filter.allTags')}
                    searchable
                    searchPlaceholder={t('filter.searchTags')}
                    disabled={disabled}
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {hasActiveFilters && (
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted">
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-faint">{t('filter.active')}</span>
            {activeQuery && <FilterToken>“{activeQuery}”</FilterToken>}
            {selectedTool && <FilterToken>{selectedTool}</FilterToken>}
            {selectedAuthor && <FilterToken>@{selectedAuthor}</FilterToken>}
            {selectedTag && <FilterToken>{selectedTagLabel}</FilterToken>}
            {sortOrder === 'oldest' && <FilterToken>{t('filter.oldestFirst')}</FilterToken>}
            <button
              type="button"
              onClick={onReset}
              className="focus-ring rounded-full px-2.5 py-1 font-medium text-brass transition-colors hover:bg-brass-soft"
            >
              {t('filter.clearAll')}
            </button>
          </div>
        )}
      </div>
    </section>
  )
}

function SortButton({ active, onClick, label, icon: Icon, disabled }) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      aria-pressed={active}
      className={`focus-ring inline-flex min-w-[64px] items-center justify-center gap-1.5 rounded-full px-3.5 text-xs font-medium transition-colors duration-300 disabled:cursor-not-allowed disabled:opacity-50 ${
        active ? 'bg-ink text-abyss' : 'text-muted hover:text-ink'
      }`}
    >
      <Icon size={14} />
      {label}
    </button>
  )
}

function FilterToken({ children }) {
  return (
    <span className="rounded-full bg-brass-soft px-2.5 py-1 font-medium text-brass-strong">{children}</span>
  )
}
