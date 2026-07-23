export const GALLERY_SESSION_SCHEMA = 'oip-gallery-session-v1'
export const GALLERY_TAXONOMY_VERSION = 'oip-visual-v2'

const SESSION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/

function clean(value) {
  return String(value || '').trim()
}

function normalizeMatchReason(reason) {
  if (typeof reason === 'string') return clean(reason)
  if (!reason || typeof reason !== 'object') return ''
  return {
    type: clean(reason.type),
    value: clean(reason.value),
    values: Array.isArray(reason.values) ? reason.values.map(clean).filter(Boolean) : [],
    scope: clean(reason.scope),
    matched_by: Array.isArray(reason.matched_by) ? reason.matched_by.map(clean).filter(Boolean) : [],
    count: Number.isFinite(Number(reason.count)) ? Number(reason.count) : null,
    percentile: Number.isFinite(Number(reason.percentile)) ? Number(reason.percentile) : null,
  }
}

export function galleryRequestFromSearch(search = '') {
  const params = new URLSearchParams(search)
  const sessionId = clean(params.get('session')).toLocaleLowerCase()
  return {
    sessionId: SESSION_ID.test(sessionId) ? sessionId : '',
    focusId: clean(params.get('focus')),
    lang: params.get('lang') === 'zh' ? 'zh' : params.get('lang') === 'en' ? 'en' : '',
  }
}

export function normalizeGallerySession(payload, requestedId = '') {
  if (!payload || typeof payload !== 'object') throw new Error('Gallery session is not a JSON object')
  if (payload.schema_version !== GALLERY_SESSION_SCHEMA) throw new Error('Unsupported gallery session schema')
  if (payload.taxonomy_version !== GALLERY_TAXONOMY_VERSION) throw new Error('Gallery session is not based on oip-visual-v2')
  const sessionId = clean(payload.session_id).toLocaleLowerCase()
  if (!SESSION_ID.test(sessionId) || (requestedId && sessionId !== requestedId)) {
    throw new Error('Gallery session ID does not match the requested session')
  }

  const seen = new Set()
  const references = (Array.isArray(payload.references) ? payload.references : [])
    .map((reference, index) => ({
      tweet_id: clean(reference?.tweet_id),
      rank: Number.isFinite(Number(reference?.rank)) ? Number(reference.rank) : index + 1,
      score: Number.isFinite(Number(reference?.score)) ? Number(reference.score) : null,
      match_reasons: Array.isArray(reference?.match_reasons)
        ? reference.match_reasons.map(normalizeMatchReason).filter(Boolean)
        : [],
    }))
    .filter((reference) => {
      if (!reference.tweet_id || seen.has(reference.tweet_id)) return false
      seen.add(reference.tweet_id)
      return true
    })
  if (!references.length) throw new Error('Gallery session contains no references')

  return {
    schema_version: GALLERY_SESSION_SCHEMA,
    taxonomy_version: GALLERY_TAXONOMY_VERSION,
    session_id: sessionId,
    created_at: clean(payload.created_at),
    intent: clean(payload.intent),
    locale: payload.locale === 'zh-Hans' ? 'zh-Hans' : 'en',
    creative_spec: payload.creative_spec && typeof payload.creative_spec === 'object'
      ? payload.creative_spec
      : {},
    derived_prompt: {
      en: clean(payload.derived_prompt?.en),
      'zh-Hans': clean(payload.derived_prompt?.['zh-Hans']),
    },
    references,
  }
}

export async function fetchGallerySession(sessionId, { signal, fetcher = fetch } = {}) {
  const response = await fetcher(`/_oip/sessions/${encodeURIComponent(sessionId)}.json`, {
    signal,
    cache: 'no-store',
  })
  if (!response.ok) throw new Error(`Gallery session request failed with status ${response.status}`)
  return normalizeGallerySession(await response.json(), sessionId)
}

export function galleryPromptApiUrl(session) {
  const ids = (session?.references || []).map((reference) => reference.tweet_id).filter(Boolean)
  if (!ids.length) throw new Error('Gallery session contains no references')
  const params = new URLSearchParams({
    limit: String(ids.length),
    ids: ids.join(','),
  })
  return `./api/prompts?${params}`
}

export function orderItemsForGallerySession(items, session) {
  if (!session) return { items, missingIds: [] }
  const byId = new Map(items.map((item) => [String(item.tweet_id), item]))
  const ordered = []
  const missingIds = []
  session.references.forEach((reference) => {
    const item = byId.get(reference.tweet_id)
    if (item) {
      ordered.push({ ...item, session_reference: reference })
    } else {
      missingIds.push(reference.tweet_id)
    }
  })
  return { items: ordered, missingIds }
}

export function localizedDerivedPrompt(session, lang) {
  if (!session) return ''
  const preferred = lang === 'zh' ? 'zh-Hans' : 'en'
  const fallback = preferred === 'en' ? 'zh-Hans' : 'en'
  return session.derived_prompt?.[preferred] || session.derived_prompt?.[fallback] || ''
}

export function validGalleryFocus(focusId, session, items) {
  if (!focusId || !session) return ''
  const referenceIds = new Set(session.references.map((reference) => reference.tweet_id))
  const itemIds = new Set(items.map((item) => String(item.tweet_id)))
  return referenceIds.has(String(focusId)) && itemIds.has(String(focusId)) ? String(focusId) : ''
}
