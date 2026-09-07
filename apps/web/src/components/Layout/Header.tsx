interface HeaderProps {
  user: {
    full_name: string
    role: string | null
    district: string | null
  }
}

export default function Header({ user }: HeaderProps) {
  return (
    <header style={{ height: '56px', background: '#0f172a', borderBottom: '1px solid #334155', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 1.5rem', flexShrink: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <h2 style={{ color: '#e2e8f0', margin: 0, fontSize: '1rem', fontWeight: 600 }}>Dashboard</h2>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>{user.full_name}</span>
        <span style={{ color: '#64748b', fontSize: '0.75rem', padding: '0.25rem 0.5rem', borderRadius: '0.25rem', background: '#1e293b', border: '1px solid #334155' }}>
          {user.role ? user.role.replace('_', ' ') : ''}
        </span>
      </div>
    </header>
  )
}
