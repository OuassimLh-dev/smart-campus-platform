import { api } from '../api/client'
import type { LoginCredentials, TokenResponse, User } from '../types/auth'

export const authService = {
  async login(credentials: LoginCredentials) {
    const response = await api.post<TokenResponse>('/auth/login', credentials)
    return response.data
  },
  async me(signal?: AbortSignal) {
    const response = await api.get<User>('/auth/me', { signal })
    return response.data
  },
}
