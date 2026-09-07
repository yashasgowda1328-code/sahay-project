import { useEffect, useState } from 'react'

interface DashboardProps {
  role: string
  district: string | null
  username: string
  onNavigate: (view: string) => void
}

export default function Dashboard({ role, district, username, onNavigate }: DashboardProps) {
  const [metrics, setMetrics] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        let url = '/api/v1/cases/dashboard/state'
        if (role === 'DISTRICT_ADMIN' && district) {
          url = `/api/v1/cases/dashboard/district/${encodeURIComponent(district)}`
        } else if (role === 'COUNSELLOR') {
          url = `/api/v1/cases/counsellor/${encodeURIComponent(username)}`
        }
        const res = await fetch(url)
        if (res.ok) {
          const data = await res.json()
          setMetrics(data)
        }
      } finally {
        setLoading(false)
      }
    }
    fetchDashboard()
  }, [role, district, username])

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 17) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ color: '#e2e8f0', margin: '0 0 0.25rem 0', fontSize: '1.25rem' }}>{getGreeting()}, {username}</h2>
        <p style={{ color: '#94a3b8', margin: 0, fontSize: '0.875rem' }}>{role.replace('_', ' ')} Dashboard</p>
      </div>

      {loading && <p style={{ color: '#94a3b8' }}>Loading dashboard...</p>}

      {!loading && metrics && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            {role === 'STATE_ADMIN' && (
              <>
                <MetricCard title="Total Cases" value={metrics.metrics?.total_cases || 0} />
                <MetricCard title="High Priority" value={metrics.metrics?.high_priority || 0} color="#f87171" />
                <MetricCard title="Watch" value={metrics.metrics?.watch || 0} color="#fbbf24" />
                <MetricCard title="Normal" value={metrics.metrics?.normal || 0} color="#4ade80" />
                <MetricCard title="Active Monitoring" value={metrics.metrics?.active_monitoring || 0} />
                <MetricCard title="Open Alerts" value={metrics.metrics?.open_alerts || 0} color="#f87171" />
                <MetricCard title="Follow-ups Due" value={metrics.metrics?.follow_ups_due || 0} color="#fbbf24" />
              </>
            )}
            {(role === 'DISTRICT_ADMIN' || role === 'COUNSELLOR') && (
              <>
                <MetricCard title="Total Cases" value={metrics.metrics?.total_cases || metrics.metrics?.my_cases || 0} />
                <MetricCard title="High Priority" value={metrics.metrics?.high_priority || 0} color="#f87171" />
                <MetricCard title="Watch" value={metrics.metrics?.watch || 0} color="#fbbf24" />
                <MetricCard title="Normal" value={metrics.metrics?.normal || 0} color="#4ade80" />
                <MetricCard title="Active Monitoring" value={metrics.metrics?.active_monitoring || 0} />
                <MetricCard title="Open Alerts" value={metrics.metrics?.open_alerts || 0} color="#f87171" />
                <MetricCard title="Follow-ups Due" value={metrics.metrics?.follow_ups_due || 0} color="#fbbf24" />
              </>
            )}
          </div>

          {role === 'STATE_ADMIN' && metrics.districts && (
            <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '0.5rem', padding: '1rem' }}>
              <h3 style={{ color: '#e2e8f0', margin: '0 0 1rem 0', fontSize: '1rem' }}>District Overview</h3>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #334155' }}>
                      <th style={{ textAlign: 'left', padding: '0.5rem', color: '#94a3b8', fontWeight: 600 }}>District</th>
                      <th style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8', fontWeight: 600 }}>Total Cases</th>
                      <th style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8', fontWeight: 600 }}>High Priority</th>
                      <th style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8', fontWeight: 600 }}>Watch</th>
                      <th style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8', fontWeight: 600 }}>Normal</th>
                      <th style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8', fontWeight: 600 }}>Active</th>
                      <th style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8', fontWeight: 600 }}>Open Alerts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.districts.map((d: any) => (
                      <tr key={d.district_name} style={{ borderBottom: '1px solid #1e293b' }}>
                        <td style={{ padding: '0.5rem', color: '#e2e8f0' }}>{d.district_name}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', color: '#cbd5e1' }}>{d.total_cases}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', color: '#f87171' }}>{d.high_priority}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', color: '#fbbf24' }}>{d.watch}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', color: '#4ade80' }}>{d.normal}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', color: '#cbd5e1' }}>{d.active_monitoring}</td>
                        <td style={{ textAlign: 'right', padding: '0.5rem', color: '#f87171' }}>{d.open_alerts}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {metrics.cases && (
            <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '0.5rem', padding: '1rem', marginTop: '1rem' }}>
              <h3 style={{ color: '#e2e8f0', margin: '0 0 1rem 0', fontSize: '1rem' }}>Recent Cases</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {metrics.cases.slice(0, 10).map((c: any) => (
                  <div
                    key={c.case_id}
                    onClick={() => onNavigate('cases')}
                    style={{
                      padding: '0.75rem',
                      borderRadius: '0.375rem',
                      border: '1px solid #334155',
                      background: '#0f172a',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      cursor: 'pointer',
                    }}
                  >
                    <div>
                      <div style={{ color: '#e2e8f0', fontSize: '0.875rem', fontWeight: 600 }}>{c.person_name || c.case_id}</div>
                      <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>{c.case_type} • {c.district || 'N/A'}</div>
                    </div>
                    <span style={{
                      padding: '0.25rem 0.5rem',
                      borderRadius: '0.25rem',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      background: c.priority === 'HIGH_PRIORITY' ? '#7f1d1d' : c.priority === 'WATCH' ? '#78350f' : '#14532d',
                      color: c.priority === 'HIGH_PRIORITY' ? '#fca5a5' : c.priority === 'WATCH' ? '#fcd34d' : '#86efac',
                    }}>
                      {c.priority.replace('_', ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function MetricCard({ title, value, color }: { title: string; value: number; color?: string }) {
  return (
    <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '0.5rem', padding: '1rem' }}>
      <div style={{ color: '#94a3b8', fontSize: '0.75rem', marginBottom: '0.25rem' }}>{title}</div>
      <div style={{ color: color || '#e2e8f0', fontSize: '1.5rem', fontWeight: 700 }}>{value}</div>
    </div>
  )
}
