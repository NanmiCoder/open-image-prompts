import assert from 'node:assert/strict'
import {
  galleryPromptApiUrl,
  galleryRequestFromSearch,
  localizedDerivedPrompt,
  normalizeGallerySession,
  orderItemsForGallerySession,
  validGalleryFocus,
} from '../src/gallerySession.js'

const sessionId = '123e4567-e89b-42d3-a456-426614174000'
const request = galleryRequestFromSearch(`?session=${sessionId}&focus=22&lang=zh`)
assert.deepEqual(request, { sessionId, focusId: '22', lang: 'zh' })
assert.equal(galleryRequestFromSearch('?session=../../secret').sessionId, '')

const session = normalizeGallerySession({
  schema_version: 'oip-gallery-session-v1',
  taxonomy_version: 'oip-visual-v2',
  session_id: sessionId,
  intent: '雨夜霓虹女性肖像',
  locale: 'zh-Hans',
  derived_prompt: { en: 'English prompt', 'zh-Hans': '中文提示词' },
  references: [
    { tweet_id: '22', rank: 1, score: 0.9, match_reasons: ['霓虹光'] },
    {
      tweet_id: '11',
      rank: 2,
      score: 0.8,
      match_kind: 'related',
      missing_constraints: ['lighting:neon'],
    },
    { tweet_id: '22', rank: 3 },
    { tweet_id: 'missing', rank: 4 },
  ],
}, sessionId)

assert.deepEqual(session.references.map((entry) => entry.tweet_id), ['22', '11', 'missing'], 'reference order is authoritative and duplicate IDs are removed')
assert.equal(session.references[0].match_kind, 'exact', 'legacy references default to exact')
assert.equal(session.references[1].match_kind, 'related')
assert.deepEqual(session.references[1].missing_constraints, ['lighting:neon'])
assert.equal(localizedDerivedPrompt(session, 'zh'), '中文提示词')
assert.equal(localizedDerivedPrompt(session, 'en'), 'English prompt')
const promptRequest = new URL(galleryPromptApiUrl(session), 'http://localhost/')
assert.equal(promptRequest.searchParams.get('limit'), '3')
assert.equal(promptRequest.searchParams.get('ids'), '22,11,missing')

const ordered = orderItemsForGallerySession([
  { tweet_id: '11', prompt_text: 'original eleven' },
  { tweet_id: '33', prompt_text: 'unrequested' },
  { tweet_id: '22', prompt_text: 'original twenty-two' },
], session)
assert.deepEqual(ordered.items.map((item) => item.tweet_id), ['22', '11'], 'only requested references are shown in session order')
assert.deepEqual(ordered.missingIds, ['missing'], 'missing references are reported, not replaced')
assert.equal(ordered.items[0].prompt_text, 'original twenty-two', 'source prompt remains byte-for-byte unchanged')
assert.equal(ordered.items[1].session_reference.match_kind, 'related', 'related status reaches the card rendering boundary')
assert.equal(validGalleryFocus('22', session, ordered.items), '22')
assert.equal(validGalleryFocus('missing', session, ordered.items), '')
assert.equal(validGalleryFocus('33', session, ordered.items), '')

assert.throws(
  () => normalizeGallerySession({ ...session, taxonomy_version: 'legacy' }, sessionId),
  /oip-visual-v2/,
  'legacy sessions fail closed',
)

console.log('Gallery session contract test OK')
