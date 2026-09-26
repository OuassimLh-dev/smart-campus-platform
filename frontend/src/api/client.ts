import axios from 'axios'
import { tokenStorage } from '../utils/tokenStorage'

export const AUTH_EXPIRED_EVENT = 'smart-campus:auth-expired'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = tokenStorage.get()
  if (token) config.headers.set('Authorization', `Bearer ${token}`)
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const token = tokenStorage.get()
      // Ignore a late response belonging to a previous session.
      if (token && error.config?.headers.get('Authorization') === `Bearer ${token}`) {
        tokenStorage.clear()
        window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
      }
    }
    return Promise.reject(error)
  },
)
