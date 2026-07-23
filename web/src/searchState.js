export const initialSearchState = Object.freeze({
  draft: '',
  submitted: '',
})

export function normalizeSearchQuery(value) {
  return String(value || '').trim()
}

export function searchReducer(state, action) {
  switch (action.type) {
    case 'edit':
      return { ...state, draft: String(action.value || '') }
    case 'submit': {
      const submitted = normalizeSearchQuery(state.draft)
      if (state.draft === submitted && state.submitted === submitted) return state
      return { draft: submitted, submitted }
    }
    case 'clear':
      if (!state.draft && !state.submitted) return state
      return initialSearchState
    default:
      return state
  }
}
