import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react'
import {
  fetchGallerySession,
  galleryPromptApiUrl,
  galleryRequestFromSearch,
  orderItemsForGallerySession,
  validGalleryFocus,
} from '../gallerySession'
import { useLang } from '../i18n'
import { initialSearchState, normalizeSearchQuery, searchReducer } from '../searchState'

const PAGE_SIZE = 24
const BUSY_RETRIES = 3

function wait(milliseconds, signal) {
  if (signal?.aborted) return Promise.reject(new DOMException('Request aborted', 'AbortError'))
  return new Promise((resolve, reject) => {
    const onAbort = () => {
      window.clearTimeout(timer)
      reject(new DOMException('Request aborted', 'AbortError'))
    }
    const timer = window.setTimeout(() => {
      signal?.removeEventListener('abort', onAbort)
      resolve()
    }, milliseconds)
    signal?.addEventListener('abort', onAbort, { once: true })
  })
}

async function fetchApiJson(url, { signal, retries = BUSY_RETRIES } = {}) {
  for (let attempt = 0; ; attempt += 1) {
    const response = await fetch(url, { signal })
    if (response.status !== 503 || attempt >= retries) {
      if (!response.ok) throw new Error(`API ${response.status}`)
      return response.json()
    }
    const retryAfter = Number(response.headers.get('Retry-After'))
    const delay = Number.isFinite(retryAfter) && retryAfter > 0
      ? retryAfter * 1000
      : 500 * (attempt + 1)
    await wait(delay, signal)
  }
}

function dateValue(item) {
  const value = Date.parse(item.created_at || item.collected_at)
  return Number.isNaN(value) ? 0 : value
}

function hydrate(item, dims, lang) {
  const ratios = dims?.[item.tweet_id] || null
  return {
    ...item,
    localized_prompt: localizedPrompt(item, lang),
    _ratios: ratios,
    _ratio: ratios?.[0] ? ratios[0][0] / ratios[0][1] : null,
    _dateValue: dateValue(item),
    _tagValues: Object.entries(item.tags || {}).flatMap(([dimension, entries]) =>
      (entries || []).map((entry) => `${dimension}:${entry.tag}`),
    ),
  }
}

function localizedPrompt(item, lang) {
  return lang === 'zh'
    ? item.translations?.['zh-Hans'] || item.prompt_text
    : item.translations?.en || item.prompt_text
}

export function usePromptArchiveApi() {
  const { lang } = useLang()
  const [items, setItems] = useState([])
  const [catalog, setCatalog] = useState({ tools: [], authors: [], tags: [], stats: {} })
  const [dims, setDims] = useState({})
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')
  const [retryToken, setRetryToken] = useState(0)
  const [gallerySession, setGallerySession] = useState(null)
  const [missingSessionReferences, setMissingSessionReferences] = useState([])
  const [search, dispatchSearch] = useReducer(searchReducer, initialSearchState)
  const [selectedTool, setSelectedTool] = useState('')
  const [selectedAuthor, setSelectedAuthor] = useState('')
  const [selectedTag, setSelectedTag] = useState('')
  const [sortOrder, setSortOrder] = useState('newest')
  const requestGenerationRef = useRef(0)
  const loadMoreControllerRef = useRef(null)
  const galleryRequest = useMemo(
    () => galleryRequestFromSearch(typeof window === 'undefined' ? '' : window.location.search),
    [],
  )

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([
      fetchApiJson('./api/catalog', { signal: controller.signal }),
      fetch('./dims.json', { signal: controller.signal }).then((response) => response.ok ? response.json() : {}),
    ]).then(([nextCatalog, nextDims]) => {
      setCatalog(nextCatalog)
      setDims(nextDims)
    }).catch((loadError) => {
      if (loadError.name !== 'AbortError') setError(loadError.message)
    })
    return () => controller.abort()
  }, [retryToken])

  const requestUrl = useCallback((offset = 0) => {
    const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset), sort: sortOrder })
    if (search.submitted) params.set('q', search.submitted)
    if (selectedTool) params.set('tool', selectedTool)
    if (selectedAuthor) params.set('author', selectedAuthor)
    if (selectedTag) params.set('tag', selectedTag)
    return `./api/prompts?${params}`
  }, [search.submitted, selectedAuthor, selectedTag, selectedTool, sortOrder])

  useEffect(() => {
    const controller = new AbortController()
    const generation = requestGenerationRef.current + 1
    requestGenerationRef.current = generation
    loadMoreControllerRef.current?.abort()
    loadMoreControllerRef.current = null
    setLoadingMore(false)
    setLoading(true)
    setError('')
    setGallerySession(null)
    setMissingSessionReferences([])

    async function loadPrompts() {
      const session = galleryRequest.sessionId
        ? await fetchGallerySession(galleryRequest.sessionId, { signal: controller.signal })
        : null
      const payload = await fetchApiJson(
        session ? galleryPromptApiUrl(session) : requestUrl(0),
        { signal: controller.signal },
      )
      return { payload, session }
    }

    loadPrompts()
      .then(({ payload, session }) => {
        if (requestGenerationRef.current !== generation) return
        const ordered = orderItemsForGallerySession(payload.items, session)
        setItems(ordered.items)
        setTotal(session ? ordered.items.length : payload.total)
        setGallerySession(session)
        setMissingSessionReferences(ordered.missingIds)
      })
      .catch((loadError) => {
        if (loadError.name !== 'AbortError') setError(loadError.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => {
      controller.abort()
      loadMoreControllerRef.current?.abort()
    }
  }, [galleryRequest.sessionId, requestUrl, retryToken])

  const loadMore = useCallback(async () => {
    if (gallerySession || loadingMore || items.length >= total) return
    const controller = new AbortController()
    const generation = requestGenerationRef.current
    loadMoreControllerRef.current?.abort()
    loadMoreControllerRef.current = controller
    setLoadingMore(true)
    try {
      const payload = await fetchApiJson(requestUrl(items.length), { signal: controller.signal })
      if (requestGenerationRef.current !== generation) return
      setItems((current) => [...current, ...payload.items])
      setTotal(payload.total)
    } catch (loadError) {
      if (loadError.name !== 'AbortError') setError(loadError.message)
    } finally {
      if (loadMoreControllerRef.current === controller) {
        loadMoreControllerRef.current = null
        setLoadingMore(false)
      }
    }
  }, [gallerySession, items.length, loadingMore, requestUrl, total])

  const setQuery = useCallback((value) => {
    dispatchSearch({ type: 'edit', value })
  }, [])

  const submitQuery = useCallback(() => {
    dispatchSearch({ type: 'submit' })
  }, [])

  const clearQuery = useCallback(() => {
    dispatchSearch({ type: 'clear' })
  }, [])

  const localizedItems = useMemo(
    () => items.map((item) => hydrate(item, dims, lang)),
    [dims, items, lang],
  )
  const tags = useMemo(() => catalog.tags.map((tag) => ({
    value: tag.value,
    label: lang === 'zh' ? tag.label_zh : tag.label_en,
  })), [catalog.tags, lang])
  const popularTags = useMemo(() => catalog.tags.map((tag) => ({
    tagValue: tag.value,
    label: lang === 'zh' ? tag.label_zh : tag.label_en,
    count: tag.count,
  })), [catalog.tags, lang])

  const resetFilters = useCallback(() => {
    dispatchSearch({ type: 'clear' })
    setSelectedTool('')
    setSelectedAuthor('')
    setSelectedTag('')
    setSortOrder('newest')
  }, [])

  return {
    items: localizedItems,
    visibleItems: localizedItems,
    loading,
    error,
    retry: () => setRetryToken((token) => token + 1),
    query: search.draft,
    appliedQuery: search.submitted,
    queryDirty: normalizeSearchQuery(search.draft) !== search.submitted,
    setQuery,
    submitQuery,
    clearQuery,
    tools: catalog.tools.map((entry) => entry.tool),
    popularTools: catalog.tools,
    selectedTool,
    setSelectedTool,
    authors: catalog.authors,
    selectedAuthor,
    setSelectedAuthor,
    tags,
    popularTags,
    selectedTag,
    setSelectedTag,
    sortOrder,
    setSortOrder,
    stats: catalog.stats,
    gallerySession,
    missingSessionReferences,
    focusId: validGalleryFocus(galleryRequest.focusId, gallerySession, items),
    filteredCount: gallerySession ? localizedItems.length : total,
    hasMore: !gallerySession && items.length < total,
    loadMore,
    resetFilters,
    hasActiveFilters: !gallerySession && Boolean(search.submitted || selectedTool || selectedAuthor || selectedTag || sortOrder !== 'newest'),
  }
}
