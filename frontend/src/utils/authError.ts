import axios from 'axios'

export function authError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) return 'The email or password is incorrect. Please try again.'
    if (error.response?.status === 422) return 'Please check your email and password.'
    if (!error.response) return 'Unable to reach Smart Campus. Check your connection and try again.'
  }
  return 'We could not sign you in. Please try again in a moment.'
}
