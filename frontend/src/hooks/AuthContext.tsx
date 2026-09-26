import { createContext, useCallback, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { AUTH_EXPIRED_EVENT } from '../api/client'
import { authService } from '../services/authService'
import type { LoginCredentials, User } from '../types/auth'
import { tokenStorage } from '../utils/tokenStorage'

interface AuthState {
  user: User | null
  loading: boolean
  initializing: boolean
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthState | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [initializing, setInitializing] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const generation = useRef(0)

  const logout = useCallback(() => {
    generation.current += 1
    tokenStorage.clear()
    setUser(null)
    setSubmitting(false)
  }, [])

  useEffect(() => {
    window.addEventListener(AUTH_EXPIRED_EVENT, logout)
    const controller = new AbortController()
    const requestGeneration = generation.current

    async function restoreSession() {
      try {
        if (tokenStorage.get()) {
          const current = await authService.me(controller.signal)
          if (!controller.signal.aborted && requestGeneration === generation.current) setUser(current)
        }
      } catch {
        if (!controller.signal.aborted && requestGeneration === generation.current) logout()
      } finally {
        if (!controller.signal.aborted) setInitializing(false)
      }
    }
    void restoreSession()
    return () => {
      controller.abort()
      window.removeEventListener(AUTH_EXPIRED_EVENT, logout)
    }
  }, [logout])

  const login = useCallback(async (credentials: LoginCredentials) => {
    const requestGeneration = ++generation.current
    tokenStorage.clear()
    setUser(null)
    setSubmitting(true)
    try {
      const { access_token } = await authService.login(credentials)
      if (requestGeneration !== generation.current) return
      tokenStorage.set(access_token)
      const current = await authService.me()
      if (requestGeneration === generation.current) setUser(current)
    } catch (error) {
      if (requestGeneration === generation.current) {
        tokenStorage.clear()
        setUser(null)
      }
      throw error
    } finally {
      if (requestGeneration === generation.current) setSubmitting(false)
    }
  }, [])

  return (
    <AuthContext.Provider value={{
      user, initializing, loading: initializing || submitting,
      isAuthenticated: user !== null, login, logout,
    }}>
      {children}
    </AuthContext.Provider>
  )
}
