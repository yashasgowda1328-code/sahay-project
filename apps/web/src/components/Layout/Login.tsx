import { useState } from 'react'

interface LoginProps {
  onLogin: (username: string, password: string) => void
  error: string | null
  demo: boolean
}

export default function Login({ onLogin, error, demo }: LoginProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    onLogin(username, password)
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a', padding: '1rem' }}>
      <div style={{ width: '100%', maxWidth: '400px', padding: '2rem', borderRadius: '0.75rem', border: '1px solid #334155', background: '#1e293b' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ color: '#e2e8f0', margin: '0 0 0.5rem 0', fontSize: '1.75rem' }}>SAHAY</h1>
          <p style={{ color: '#94a3b8', margin: 0, fontSize: '0.875rem' }}>Support Administration and Help for At-Risk Youth</p>
          {demo && (
            <p style={{ color: '#fbbf24', margin: '0.5rem 0 0 0', fontSize: '0.75rem' }}>Demo Environment</p>
          )}
        </div>
        <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', color: '#cbd5e1', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Username</label>
            <input
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter username"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: '0.875rem' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', color: '#cbd5e1', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter password"
              style={{ width: '100%', padding: '0.625rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: '0.875rem' }}
            />
          </div>
          {error && (
            <p style={{ color: '#f87171', fontSize: '0.875rem', margin: 0 }}>{error}</p>
          )}
          <button
            type="submit"
            style={{ padding: '0.625rem', borderRadius: '0.375rem', border: 'none', background: '#2563eb', color: '#fff', cursor: 'pointer', fontSize: '0.875rem', fontWeight: 600 }}
          >
            Sign In
          </button>
        </form>
        {demo && (
          <div style={{ marginTop: '1.5rem', padding: '1rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a' }}>
            <p style={{ color: '#94a3b8', fontSize: '0.75rem', margin: '0 0 0.5rem 0', fontWeight: 600 }}>Demo Accounts</p>
            <p style={{ color: '#64748b', fontSize: '0.75rem', margin: '0 0 0.25rem 0' }}>State Admin: state.admin / demo123</p>
            <p style={{ color: '#64748b', fontSize: '0.75rem', margin: '0 0 0.25rem 0' }}>District Admin: district.admin / demo123</p>
            <p style={{ color: '#64748b', fontSize: '0.75rem', margin: 0 }}>Counsellor: counsellor.anjali / demo123</p>
          </div>
        )}
      </div>
    </div>
  )
}
