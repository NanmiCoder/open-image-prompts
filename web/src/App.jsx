import { AnimatePresence, motion } from 'framer-motion'
import { useCallback, useEffect, useRef, useState } from 'react'
import ArchiveHeader from './components/ArchiveHeader'
import FilterBar from './components/FilterBar'
import GallerySessionPanel from './components/GallerySessionPanel'
import PromptDialog from './components/PromptDialog'
import PromptGallery from './components/PromptGallery'
import { usePromptArchiveApi } from './hooks/usePromptArchiveApi'
import { useLang } from './i18n'

function App() {
  const archive = usePromptArchiveApi()
  const { t } = useLang()
  const [selectedId, setSelectedId] = useState(null)
  const [toast, setToast] = useState(null)
  const toastTimerRef = useRef(null)
  const searchInputRef = useRef(null)
  const navigationItems = archive.gallerySession ? archive.items : archive.visibleItems

  const selectedIndex = selectedId
    ? navigationItems.findIndex((item) => item.tweet_id === selectedId)
    : -1
  const selectedItem = selectedIndex >= 0 ? navigationItems[selectedIndex] : null

  const notify = useCallback((message) => {
    window.clearTimeout(toastTimerRef.current)
    setToast(message)
    toastTimerRef.current = window.setTimeout(() => setToast(null), 2400)
  }, [])

  const stepSelection = useCallback(
    (delta) => {
      const items = navigationItems
      if (!items.length) return
      const next = (selectedIndex + delta + items.length) % items.length
      if (!archive.gallerySession && next >= items.length - 4 && archive.hasMore) archive.loadMore()
      setSelectedId(items[next].tweet_id)
    },
    [archive, navigationItems, selectedIndex],
  )

  useEffect(() => {
    if (archive.focusId) setSelectedId(archive.focusId)
  }, [archive.focusId])

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key !== '/' || selectedId) return
      const tag = document.activeElement?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA') return
      event.preventDefault()
      searchInputRef.current?.focus()
      searchInputRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' })
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [selectedId])

  return (
    <div className="min-h-[100dvh] bg-abyss text-ink">
      <div className="grain-overlay" aria-hidden="true" />

      <ArchiveHeader stats={archive.stats} loading={archive.loading} items={archive.items} />

      <main className="relative mx-auto w-full max-w-[1760px] pb-24">
        <GallerySessionPanel
          session={archive.gallerySession}
          missingReferences={archive.missingSessionReferences}
          onCopied={notify}
        />

        <FilterBar
          query={archive.query}
          activeQuery={archive.appliedQuery}
          queryDirty={archive.queryDirty}
          onQueryChange={archive.setQuery}
          onQuerySubmit={archive.submitQuery}
          onQueryClear={archive.clearQuery}
          searchInputRef={searchInputRef}
          popularTools={archive.popularTools}
          tools={archive.tools}
          selectedTool={archive.selectedTool}
          onToolChange={archive.setSelectedTool}
          authors={archive.authors}
          selectedAuthor={archive.selectedAuthor}
          onAuthorChange={archive.setSelectedAuthor}
          popularTags={archive.popularTags}
          tags={archive.tags}
          selectedTag={archive.selectedTag}
          onTagChange={archive.setSelectedTag}
          sortOrder={archive.sortOrder}
          onSortChange={archive.setSortOrder}
          resultCount={archive.filteredCount}
          hasActiveFilters={archive.hasActiveFilters}
          onReset={archive.resetFilters}
          disabled={Boolean(archive.error || archive.gallerySession)}
        />

        <PromptGallery
          items={archive.visibleItems}
          loading={archive.loading}
          error={archive.error}
          hasMore={archive.hasMore}
          onLoadMore={archive.loadMore}
          onRetry={archive.retry}
          onReset={archive.resetFilters}
          onSelect={(item) => setSelectedId(item.tweet_id)}
          onCopied={notify}
          hasActiveFilters={archive.hasActiveFilters}
          preserveOrder={Boolean(archive.gallerySession)}
        />
      </main>

      <footer className="relative border-t border-line">
        <div className="mx-auto flex w-full max-w-[1760px] flex-col gap-3 px-5 py-10 text-[13px] text-muted md:flex-row md:items-center md:justify-between md:px-10">
          <span className="font-display text-base font-semibold text-ink">Open Image Prompts</span>
          <span>{t('footer.tagline')}</span>
          <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-faint">{t('footer.mark')}</span>
        </div>
      </footer>

      <AnimatePresence>
        {selectedItem && (
          <PromptDialog
            item={selectedItem}
            position={selectedIndex + 1}
            total={archive.gallerySession ? navigationItems.length : archive.filteredCount}
            onClose={() => setSelectedId(null)}
            onStep={stepSelection}
            onCopied={notify}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {toast && (
          <motion.div
            key="toast"
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 400, damping: 28 }}
            className="fixed bottom-6 left-1/2 z-[70] -translate-x-1/2"
            role="status"
          >
            <div className="toast">
              <span className="grid size-5 place-items-center rounded-full bg-brass text-[11px] font-bold text-abyss">✓</span>
              {toast}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default App
