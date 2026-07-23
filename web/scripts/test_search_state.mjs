import assert from 'node:assert/strict'
import test from 'node:test'
import {
  initialSearchState,
  normalizeSearchQuery,
  searchReducer,
} from '../src/searchState.js'

test('editing never changes the submitted API query', () => {
  const first = searchReducer(initialSearchState, { type: 'edit', value: 'p' })
  const second = searchReducer(first, { type: 'edit', value: 'portrait' })

  assert.deepEqual(second, { draft: 'portrait', submitted: '' })
})

test('submitting trims the draft and applies it once', () => {
  const edited = searchReducer(initialSearchState, { type: 'edit', value: '  portrait  ' })
  const submitted = searchReducer(edited, { type: 'submit' })

  assert.deepEqual(submitted, { draft: 'portrait', submitted: 'portrait' })
  assert.equal(searchReducer(submitted, { type: 'submit' }), submitted)
})

test('submitting an empty draft clears the active query', () => {
  const active = { draft: '   ', submitted: 'portrait' }

  assert.deepEqual(searchReducer(active, { type: 'submit' }), { draft: '', submitted: '' })
})

test('clear removes both the draft and submitted query immediately', () => {
  const active = { draft: 'new text', submitted: 'old text' }

  assert.equal(searchReducer(active, { type: 'clear' }), initialSearchState)
})

test('query normalization handles non-string and whitespace values', () => {
  assert.equal(normalizeSearchQuery(null), '')
  assert.equal(normalizeSearchQuery('  centered  '), 'centered')
})
