import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate } from 'react-router'
import { Brand } from '../components/Brand'
import { SessionLoading } from '../components/SessionLoading'
import { useAuth } from '../hooks/useAuth'
import { authError } from '../utils/authError'

export function LoginPage() {
  const { login, loading, initializing, isAuthenticated } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (loading) return
    setError('')
    try {
      await login({ email: email.trim(), password })
      setPassword('')
    } catch (cause) {
      setError(authError(cause))
      setPassword('')
    }
  }

  if (initializing) return <SessionLoading />
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <main className="login-page">
    <section className="login-intro">
      <Brand />
      <div className="intro-copy"><p className="eyebrow">ONE CAMPUS. ONE WORKSPACE.</p>
        <h1>A little more focus.<br />A better campus day.</h1>
        <p>Your academic life, brought together.<br />A shared space to learn, teach, and grow.</p>
        <div className="campus-lines" aria-hidden="true"><span /><span /><span /><span /><span /></div>
      </div>
      <p className="intro-footer">SMART CAMPUS MANAGEMENT PLATFORM</p>
    </section>
    <section className="login-panel" aria-labelledby="login-heading">
      <div className="login-form-wrap">
        <p className="eyebrow">WELCOME BACK</p>
        <h2 id="login-heading">Sign in to your workspace</h2>
        <p className="muted">Use your campus account to continue.</p>
        <form onSubmit={submit} aria-busy={loading}>
          <label htmlFor="email">Email address</label>
          <input id="email" name="email" type="email" autoComplete="username" placeholder="you@university.edu"
            required maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} disabled={loading} />
          <label htmlFor="password">Password</label>
          <input id="password" name="password" type="password" autoComplete="current-password" placeholder="Enter your password"
            required maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} disabled={loading} />
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="primary-button" type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'} <span aria-hidden="true">→</span></button>
        </form>
        <p className="login-help">Need an account? Contact your campus administrator.</p>
      </div>
      <p className="login-footer">A connected campus starts here.</p>
    </section>
  </main>
}
