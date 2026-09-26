const KEY = 'smart-campus.access-token'

// Tab-scoped persistence for this portfolio version. No passwords or user data
// are persisted. Memory fallback supports browsers that disable sessionStorage.
let memoryToken: string | null = null
try {
  memoryToken = sessionStorage.getItem(KEY)
} catch {
  // Storage may be unavailable in restricted browser sessions.
}

export const tokenStorage = {
  get: () => memoryToken,
  set(token: string) {
    memoryToken = token
    try { sessionStorage.setItem(KEY, token) } catch { /* memory-only session */ }
  },
  clear() {
    memoryToken = null
    try { sessionStorage.removeItem(KEY) } catch { /* memory-only session */ }
  },
}
