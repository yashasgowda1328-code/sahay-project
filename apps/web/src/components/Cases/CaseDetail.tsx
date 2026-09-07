import { useEffect, useState } from 'react'

interface CaseDetailProps {
  caseId: string
  onBack: () => void
}

interface CaseData {
  case_id: string
  person_name: string
  case_type: string
  age: number | null
  district: string | null
  state: string | null
  assigned_counsellor: string | null
  priority: string
  monitoring_status: string | null
  consent_status: string | null
  case_opened: string | null
  last_counselling: string | null
  next_follow_up: string | null
  last_reading: string | null
  baseline: Record<string, any> | null
  current_features: Record<string, any> | null
  deviations: any[]
  explanation: string | null
  alerts: any[]
  interventions: any[]
  counselling_sessions: any[]
  follow_ups: any[]
  audit_logs: any[]
}

export default function CaseDetail({ caseId, onBack }: CaseDetailProps) {
  const [data, setData] = useState<CaseData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('summary')

  useEffect(() => {
    const fetchCase = async () => {
      setLoading(true)
      try {
        const res = await fetch(`/api/v1/cases/${encodeURIComponent(caseId)}`)
        if (res.ok) {
          const json = await res.json()
          setData(json)
        }
      } finally {
        setLoading(false)
      }
    }
    fetchCase()
  }, [caseId])

  const formatDate = (d: string | null) => d ? new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'N/A'

  const priorityColor = (p: string) => {
    if (p === 'HIGH_PRIORITY') return '#f87171'
    if (p === 'WATCH') return '#fbbf24'
    return '#4ade80'
  }

  if (loading) return <p style={{ color: '#94a3b8' }}>Loading case...</p>
  if (!data) return <p style={{ color: '#f87171' }}>Case not found.</p>

  const tabs = ['summary', 'wearable', 'alerts', 'interventions', 'counselling', 'follow-ups', 'audit']

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
        <button onClick={onBack} style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0', cursor: 'pointer', fontSize: '0.875rem' }}>
          ← Back to Cases
        </button>
        <h2 style={{ color: '#e2e8f0', margin: 0, fontSize: '1.25rem' }}>{data.person_name}</h2>
        <span style={{
          padding: '0.25rem 0.75rem',
          borderRadius: '0.25rem',
          fontSize: '0.75rem',
          fontWeight: 600,
          background: data.priority === 'HIGH_PRIORITY' ? '#7f1d1d' : data.priority === 'WATCH' ? '#78350f' : '#14532d',
          color: priorityColor(data.priority),
        }}>
          {data.priority.replace('_', ' ')}
        </span>
      </div>

      <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '1rem', borderBottom: '1px solid #334155', paddingBottom: '0.5rem', overflowX: 'auto' }}>
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: '0.375rem',
              border: 'none',
              background: activeTab === tab ? '#1e3a8a' : 'transparent',
              color: activeTab === tab ? '#fff' : '#94a3b8',
              cursor: 'pointer',
              fontSize: '0.875rem',
              textTransform: 'capitalize',
              whiteSpace: 'nowrap',
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'summary' && <SummaryTab data={data} formatDate={formatDate} />}
      {activeTab === 'wearable' && <WearableTab data={data} formatDate={formatDate} />}
      {activeTab === 'alerts' && <AlertsTab data={data} formatDate={formatDate} />}
      {activeTab === 'interventions' && <InterventionsTab data={data} formatDate={formatDate} />}
      {activeTab === 'counselling' && <CounsellingTab data={data} formatDate={formatDate} />}
      {activeTab === 'follow-ups' && <FollowUpsTab data={data} formatDate={formatDate} />}
      {activeTab === 'audit' && <AuditTab data={data} formatDate={formatDate} />}
    </div>
  )
}

function SummaryTab({ data, formatDate }: { data: CaseData; formatDate: (d: string | null) => string }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
      <Card title="Case Information">
        <InfoRow label="Case ID" value={data.case_id} />
        <InfoRow label="Person" value={data.person_name} />
        <InfoRow label="Case Type" value={data.case_type} />
        <InfoRow label="Age" value={data.age?.toString() || 'N/A'} />
        <InfoRow label="District" value={data.district || 'N/A'} />
        <InfoRow label="State" value={data.state || 'N/A'} />
        <InfoRow label="Assigned Counsellor" value={data.assigned_counsellor || 'N/A'} />
        <InfoRow label="Case Opened" value={formatDate(data.case_opened)} />
      </Card>

      <Card title="Support Priority">
        <InfoRow label="Current Priority" value={data.priority.replace('_', ' ')} />
        <InfoRow label="Monitoring Status" value={data.monitoring_status || 'N/A'} />
        <InfoRow label="Consent Status" value={data.consent_status || 'pending'} />
        <InfoRow label="Last Counselling" value={formatDate(data.last_counselling)} />
        <InfoRow label="Next Follow-up" value={formatDate(data.next_follow_up)} />
      </Card>

      {data.explanation && (
        <Card title="Monitoring Summary" color="#f8fafc">
          <p style={{ color: '#475569', fontSize: '0.875rem', lineHeight: 1.5, margin: 0 }}>{data.explanation}</p>
        </Card>
      )}
    </div>
  )
}

function WearableTab({ data, formatDate }: { data: CaseData; formatDate: (d: string | null) => string }) {
  const [readings, setReadings] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/v1/readings/${encodeURIComponent(data.case_id)}`)
      .then(r => r.ok ? r.json() : [])
      .then(setReadings)
      .finally(() => setLoading(false))
  }, [data.case_id])

  const baseline = data.baseline || {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <Card title="SAHAY Wearable Monitoring">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <div style={{ color: '#64748b', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Device</div>
            <div style={{ color: '#e2e8f0', fontSize: '0.875rem' }}>SAHAY Band</div>
          </div>
          <div>
            <div style={{ color: '#64748b', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Data Source</div>
            <div style={{ color: '#e2e8f0', fontSize: '0.875rem' }}>Simulated Fit-Band</div>
          </div>
          <div>
            <div style={{ color: '#64748b', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Monitoring</div>
            <div style={{ color: '#4ade80', fontSize: '0.875rem', fontWeight: 600 }}>Active</div>
          </div>
          <div>
            <div style={{ color: '#64748b', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Last Sync</div>
            <div style={{ color: '#e2e8f0', fontSize: '0.875rem' }}>{readings.length > 0 ? formatDate(readings[0].timestamp) : 'N/A'}</div>
          </div>
        </div>
        <p style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.75rem', marginBottom: 0 }}>This prototype simulates future wearable integration. Data does not measure medical conditions.</p>
      </Card>

      {baseline && Object.keys(baseline).length > 0 && (
        <Card title="Personal Baseline">
          <BaselineComparison current={data.current_features || {}} baseline={baseline} />
        </Card>
      )}

      <Card title="Raw Wearable Data">
        {loading ? (
          <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Loading readings...</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #334155' }}>
                  <th style={{ textAlign: 'left', padding: '0.5rem', color: '#94a3b8' }}>Timestamp</th>
                  <th style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8' }}>Heart Rate</th>
                  <th style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8' }}>Activity</th>
                  <th style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8' }}>Inactivity</th>
                  <th style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8' }}>Steps</th>
                </tr>
              </thead>
              <tbody>
                {readings.slice(0, 20).map((r: any) => (
                  <tr key={r.id} style={{ borderBottom: '1px solid #1e293b' }}>
                    <td style={{ padding: '0.5rem', color: '#cbd5e1' }}>{new Date(r.timestamp).toLocaleString()}</td>
                    <td style={{ textAlign: 'right', padding: '0.5rem', color: '#e2e8f0' }}>{r.heart_rate}</td>
                    <td style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8' }}>{r.activity_level}</td>
                    <td style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8' }}>{r.is_inactive ? 'Yes' : 'No'}</td>
                    <td style={{ textAlign: 'right', padding: '0.5rem', color: '#94a3b8' }}>{r.steps_increment}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {readings.length === 0 && <p style={{ color: '#64748b', fontSize: '0.875rem' }}>No readings available.</p>}
          </div>
        )}
      </Card>
    </div>
  )
}

function AlertsTab({ data, formatDate }: { data: CaseData; formatDate: (d: string | null) => string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {data.alerts.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No alerts for this case.</p>}
      {data.alerts.map(a => (
        <div key={a.id} style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: '#1e293b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>Alert #{a.id}</span>
            <span style={{
              padding: '0.25rem 0.5rem',
              borderRadius: '0.25rem',
              fontSize: '0.75rem',
              fontWeight: 600,
              background: a.priority === 'HIGH_PRIORITY' ? '#7f1d1d' : '#78350f',
              color: a.priority === 'HIGH_PRIORITY' ? '#fca5a5' : '#fcd34d',
            }}>
              {a.priority.replace('_', ' ')}
            </span>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>{a.explanation}</p>
          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#64748b' }}>
            <span>Created: {formatDate(a.created_at)}</span>
            <span>Status: {a.status}</span>
            <span>Requires Review: {a.requires_counsellor_review ? 'Yes' : 'No'}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

function InterventionsTab({ data, formatDate }: { data: CaseData; formatDate: (d: string | null) => string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {data.interventions.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No interventions recorded.</p>}
      {data.interventions.map(i => (
        <div key={i.id} style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: '#1e293b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{i.category.replace('_', ' ')}</span>
            <span style={{ padding: '0.25rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', background: '#1e3a8a', color: '#93c5fd' }}>{i.status}</span>
          </div>
          {i.description && <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>{i.description}</p>}
          {i.protocol_reference && <p style={{ color: '#64748b', fontSize: '0.75rem', marginBottom: '0.5rem' }}>Protocol: {i.protocol_reference}</p>}
          <p style={{ color: '#64748b', fontSize: '0.75rem', margin: 0 }}>Created by {i.created_by} on {formatDate(i.created_at)}</p>
        </div>
      ))}
    </div>
  )
}

function CounsellingTab({ data, formatDate }: { data: CaseData; formatDate: (d: string | null) => string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {data.counselling_sessions.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No counselling sessions recorded.</p>}
      {data.counselling_sessions.map(s => (
        <div key={s.id} style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: '#1e293b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{s.session_type}</span>
            <span style={{ padding: '0.25rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', background: '#14532d', color: '#86efac' }}>{s.status}</span>
          </div>
          {s.summary && <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>{s.summary}</p>}
          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: '#64748b' }}>
            <span>Counsellor: {s.counsellor_id}</span>
            {s.duration_minutes && <span>Duration: {s.duration_minutes} min</span>}
            <span>Date: {formatDate(s.created_at)}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

function FollowUpsTab({ data, formatDate }: { data: CaseData; formatDate: (d: string | null) => string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {data.follow_ups.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No follow-ups scheduled.</p>}
      {data.follow_ups.map(f => (
        <div key={f.id} style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: '#1e293b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{f.purpose || 'Follow-up'}</span>
            <span style={{ padding: '0.25rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', background: '#1e3a8a', color: '#93c5fd' }}>{f.status}</span>
          </div>
          {f.notes && <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>{f.notes}</p>}
          <p style={{ color: '#64748b', fontSize: '0.75rem', margin: 0 }}>Due: {formatDate(f.due_date)}</p>
        </div>
      ))}
    </div>
  )
}

function AuditTab({ data, formatDate }: { data: CaseData; formatDate: (d: string | null) => string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '400px', overflowY: 'auto' }}>
      {data.audit_logs.length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No audit records.</p>}
      {data.audit_logs.map(l => (
        <div key={l.id} style={{ padding: '0.75rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
            <span style={{ color: '#e2e8f0', fontSize: '0.875rem', fontWeight: 600 }}>{l.action}</span>
            <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>{formatDate(l.performed_at)}</span>
          </div>
          <div style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
            {l.entity_type} #{l.entity_id} by {l.performed_by}
          </div>
        </div>
      ))}
    </div>
  )
}

function Card({ title, children, color }: { title: string; children: React.ReactNode; color?: string }) {
  return (
    <div style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: color || '#1e293b' }}>
      <h3 style={{ color: '#e2e8f0', margin: '0 0 0.75rem 0', fontSize: '0.875rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{title}</h3>
      {children}
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.375rem 0', borderBottom: '1px solid #1e293b' }}>
      <span style={{ color: '#64748b', fontSize: '0.875rem' }}>{label}</span>
      <span style={{ color: '#e2e8f0', fontSize: '0.875rem', fontWeight: 500 }}>{value}</span>
    </div>
  )
}

function BaselineComparison({ current, baseline }: { current: Record<string, any>; baseline: Record<string, any> }) {
  const features = [
    { key: 'hr_mean', label: 'Heart Rate', unit: 'bpm', format: (v: number) => v?.toFixed(1) },
    { key: 'steps_mean', label: 'Steps', unit: '', format: (v: number) => v?.toFixed(0) },
    { key: 'active_ratio_mean', label: 'Activity', unit: '', format: (v: number) => (v * 100)?.toFixed(0) + '%' },
    { key: 'inactive_minutes_mean', label: 'Inactivity', unit: 'min', format: (v: number) => v?.toFixed(1) },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {features.map(f => {
        const currentVal = current[f.key]?.raw_value ?? current[f.key]
        const baselineVal = baseline[f.key]
        const change = baselineVal ? (((currentVal - baselineVal) / baselineVal) * 100).toFixed(0) : '0'
        const isHigh = Number(change) > 10
        const isLow = Number(change) < -10

        return (
          <div key={f.key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem', borderRadius: '0.375rem', background: '#0f172a' }}>
            <div>
              <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>{f.label}</div>
              <div style={{ color: '#e2e8f0', fontSize: '0.875rem', fontWeight: 600 }}>
                {f.format(Number(currentVal) || 0)} {f.unit}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ color: '#64748b', fontSize: '0.75rem' }}>Usual: {f.format(Number(baselineVal) || 0)} {f.unit}</div>
              <div style={{ color: isHigh ? '#f87171' : isLow ? '#4ade80' : '#94a3b8', fontSize: '0.875rem', fontWeight: 600 }}>
                {Number(change) > 0 ? '+' : ''}{change}%
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
