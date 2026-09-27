import { useEffect, useState } from 'react'
import { apiError } from '../utils/apiError'

// Pass a useCallback loader; aborted/stale responses cannot overwrite a newer page.
export function useResource<T>(loader: (signal: AbortSignal) => Promise<T>) {
  const [data, setData] = useState<T>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    setData(undefined)
    loader(controller.signal).then(value => {
      if (!controller.signal.aborted) setData(value)
    }).catch(cause => {
      if (!controller.signal.aborted) setError(apiError(cause))
    }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [loader, revision])
  return { data, setData, loading, error, reload: () => setRevision(value => value + 1) }
}
