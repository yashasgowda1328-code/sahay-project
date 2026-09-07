import { useState, useEffect } from 'react'

interface AuditLog {
  id: number
  case_id: string
  action: string
  entity_type: string
  entity_id: number
  details: string | null
  performed_by: string
  performed_at: string
}

interface AuditHistoryProps {
  caseId: string
}

export default function AuditHistory({ caseId }: AuditHistoryProps) {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/v1/cases/${encodeURIComponent(caseId)}/audit`)
      if (res.ok) {
        const data = await res.json()
        setLogs(data)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (caseId) load()
  }, [caseId])

  return (
    <div style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: '#1e293b', marginBottom: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <h3 style={{ color: '#e2e8f0', margin: 0 }}>Audit History</h3>
        <button
          onClick={load}
          style={{ padding: '0.25rem 0.75rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0', cursor: 'pointer', fontSize: '0.875rem' }}
        >
          {loading ? '...' : 'Refresh'}
        </button>
      </div>
      {logs.length === 0 && !loading && (
        <p style={{ color: '#64748b', fontSize: '0.875rem' }}>No audit records.</p>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '300px', overflowY: 'auto' }}>
        {logs.map(l => (
          <div key={l.id} style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#e2e8f0', fontSize: '0.875rem', fontWeight: 600 }}>{l.action}</span>
              <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>{new Date(l.performed_at).toLocaleString()}</span>
            </div>
            <div style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
              {l.entity_type} #{l.entity_id} by {l.performed_by}
            </div>
            {l.details && (
              <pre style={{ color: '#cbd5e1', fontSize: '0.75rem', whiteSpace: 'pre-wrap', margin: '0.25rem 0 0 0' }}>{l.details}</pre>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
