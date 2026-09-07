interface SidebarProps {
  role: 'STATE_ADMIN' | 'DISTRICT_ADMIN' | 'COUNSELLOR' | null
  currentView: string
  onNavigate: (view: string) => void
  onLogout: () => void
}

const NAV_ITEMS = {
  STATE_ADMIN: [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'districts', label: 'Districts' },
    { key: 'cases', label: 'Cases' },
    { key: 'alerts', label: 'Alerts' },
    { key: 'reports', label: 'Reports' },
  ],
  DISTRICT_ADMIN: [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'cases', label: 'Cases' },
    { key: 'counsellors', label: 'Counsellors' },
    { key: 'alerts', label: 'Alerts' },
    { key: 'reports', label: 'Reports' },
  ],
  COUNSELLOR: [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'cases', label: 'My Cases' },
    { key: 'alerts', label: 'Alerts' },
    { key: 'counselling', label: 'Counselling' },
    { key: 'interventions', label: 'Interventions' },
    { key: 'protocols', label: 'Protocols' },
  ],
}

export default function Sidebar({ role, currentView, onNavigate, onLogout }: SidebarProps) {
  const items = role ? (NAV_ITEMS[role] || []) : []

  return (
    <aside style={{ width: '240px', background: '#1e293b', borderRight: '1px solid #334155', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
      <div style={{ padding: '1.25rem', borderBottom: '1px solid #334155' }}>
        <h1 style={{ color: '#e2e8f0', margin: '0 0 0.25rem 0', fontSize: '1.25rem' }}>SAHAY</h1>
        <p style={{ color: '#94a3b8', margin: 0, fontSize: '0.75rem' }}>State Administration</p>
      </div>
      <nav style={{ flex: 1, padding: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {items.map(item => (
          <button
            key={item.key}
            onClick={() => onNavigate(item.key)}
            style={{
              padding: '0.625rem 0.75rem',
              borderRadius: '0.375rem',
              border: 'none',
              background: currentView === item.key ? '#1e3a8a' : 'transparent',
              color: currentView === item.key ? '#fff' : '#cbd5e1',
              cursor: 'pointer',
              fontSize: '0.875rem',
              textAlign: 'left',
              fontWeight: currentView === item.key ? 600 : 400,
            }}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <div style={{ padding: '0.75rem', borderTop: '1px solid #334155' }}>
        <button
          onClick={onLogout}
          style={{
            width: '100%',
            padding: '0.625rem',
            borderRadius: '0.375rem',
            border: '1px solid #334155',
            background: 'transparent',
            color: '#cbd5e1',
            cursor: 'pointer',
            fontSize: '0.875rem',
          }}
        >
          Logout
        </button>
      </div>
    </aside>
  )
}
