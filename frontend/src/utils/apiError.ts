import axios from 'axios'

export function isNotFound(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 404
}
export function apiError(error: unknown): string {
  if (!axios.isAxiosError(error)) return 'Something went wrong. Please try again.'
  if (!error.response) return 'Unable to reach Smart Campus. Please try again.'
  if (error.response.status === 401) return 'Your session has expired. Please sign in again.'
  if (error.response.status === 403) return 'You do not have permission to perform this action.'
  const detail: unknown = error.response.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item: { loc?: string[]; msg?: string }) =>
      `${item.loc?.slice(1).join(' ') || 'Input'}: ${item.msg || 'Invalid value'}`).join('. ')
  }
  return 'The request could not be completed. Please try again.'
}
