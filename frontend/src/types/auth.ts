export type Role = 'student' | 'professor' | 'admin'

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
  role: Role
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
}
