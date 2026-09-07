import { useEffect, useState } from 'react'
import Sidebar from './components/Layout/Sidebar'
import Header from './components/Layout/Header'
import Login from './components/Layout/Login'
import Dashboard from './components/Dashboard/Dashboard'
import CaseList from './components/Cases/CaseList'
import CaseDetail from './components/Cases/CaseDetail'

type Role = 'STATE_ADMIN' | 'DISTRICT_ADMIN' | 'COUNSELLOR' | null

interface UserSession {
  user_id: number
  username: string
  full_name: string
  role: Role
  district: string | null
  demo: boolean
}

type View = 'login' | 'dashboard' | 'cases' | 'case-detail' | 'alerts' | 'counselling' | 'interventions' | 'protocols'

function App() {
  const [session, setSession] = useState<UserSession | null>(null)
  const [view, setView] = useState<View>('login')
  const [selectedCaseId, setSelectedCaseId] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const stored = localStorage.getItem('sahay_session')
    if (stored) {
      try {
        const s = JSON.parse(stored)
        setSession(s)
        setView('dashboard')
      } catch {
        localStorage.removeItem('sahay_session')
      }
    }
    setLoading(false)
  }, [])

  const handleLogin = async (username: string, password: string) => {
    setError(null)
    try {
      const res = await fetch('/api/v1/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Login failed')
      }
      const data = await res.json()
      const s: UserSession = {
        user_id: data.user_id,
        username: data.username,
        full_name: data.full_name,
        role: data.role as Role,
        district: data.district,
        demo: data.demo,
      }
      setSession(s)
      localStorage.setItem('sahay_session', JSON.stringify(s))
      setView('dashboard')
    } catch (e: any) {
      setError(e.message)
    }
  }

  const handleLogout = () => {
    setSession(null)
    localStorage.removeItem('sahay_session')
    setView('login')
  }

  const navigate = (v: string) => {
    setView(v as View)
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a' }}>
        <p style={{ color: '#94a3b8' }}>Loading...</p>
      </div>
    )
  }

  if (!session || view === 'login') {
    return <Login onLogin={handleLogin} error={error} demo={true} />
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0f172a' }}>
      <Sidebar role={session.role} currentView={view} onNavigate={navigate} onLogout={handleLogout} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <Header user={session} />
        <main style={{ flex: 1, padding: '1.5rem', overflow: 'auto' }}>
          {view === 'dashboard' && (
            <Dashboard role={session.role!} district={session.district} username={session.username} onNavigate={navigate} />
          )}
          {view === 'cases' && (
            <CaseList onSelectCase={(id) => { setSelectedCaseId(id); navigate('case-detail') }} />
          )}
          {view === 'case-detail' && selectedCaseId && (
            <CaseDetail caseId={selectedCaseId} onBack={() => navigate('cases')} />
          )}
          {view === 'alerts' && (
            <div style={{ color: '#e2e8f0' }}>Alerts - Under construction</div>
          )}
          {view === 'counselling' && (
            <div style={{ color: '#e2e8f0' }}>Counselling - Under construction</div>
          )}
          {view === 'interventions' && (
            <div style={{ color: '#e2e8f0' }}>Interventions - Under construction</div>
          )}
          {view === 'protocols' && (
            <div style={{ color: '#e2e8f0' }}>Protocols - Under construction</div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
