import { useEffect, useState } from 'react'

interface CaseItem {
  case_id: string
  person_name: string
  case_type: string
  district: string | null
  assigned_counsellor: string | null
  priority: string
  monitoring_status: string | null
  consent_status: string | null
  last_counselling: string | null
  next_follow_up: string | null
  last_reading: string | null
}

interface CaseListProps {
  onSelectCase: (caseId: string) => void
}

export default function CaseList({ onSelectCase }: CaseListProps) {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [districtFilter, setDistrictFilter] = useState('')
  const [caseTypeFilter, setCaseTypeFilter] = useState('')

  useEffect(() => {
    const fetchCases = async () => {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        if (priorityFilter) params.set('priority', priorityFilter)
        if (districtFilter) params.set('district', districtFilter)
      if (caseTypeFilter) params.set('case_type', caseTypeFilter)

        const res = await fetch(`/api/v1/cases?${params.toString()}`)
        if (res.ok) {
          const data = await res.json()
          setCases(data)
        }
      } finally {
        setLoading(false)
      }
    }
    fetchCases()
  }, [priorityFilter, districtFilter, caseTypeFilter])

  const filtered = cases.filter(c => {
    if (!search) return true
    const q = search.toLowerCase()
    return c.case_id.toLowerCase().includes(q) || c.person_name.toLowerCase().includes(q) || c.district?.toLowerCase().includes(q)
  })

  const priorityColor = (p: string) => {
    if (p === 'HIGH_PRIORITY') return '#f87171'
    if (p === 'WATCH') return '#fbbf24'
    return '#4ade80'
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ color: '#e2e8f0', margin: 0, fontSize: '1.25rem' }}>Cases</h2>
        <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>{filtered.length} cases</span>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search cases..."
          style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: '0.875rem', minWidth: '200px' }}
        />
        <select value={priorityFilter} onChange={e => setPriorityFilter(e.target.value)} style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: '0.875rem' }}>
          <option value="">All Priorities</option>
          <option value="NORMAL">NORMAL</option>
          <option value="WATCH">WATCH</option>
          <option value="HIGH_PRIORITY">HIGH_PRIORITY</option>
        </select>
        <select value={districtFilter} onChange={e => setDistrictFilter(e.target.value)} style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: '0.875rem' }}>
          <option value="">All Districts</option>
          <option value="Bengaluru Urban">Bengaluru Urban</option>
          <option value="Mysuru">Mysuru</option>
          <option value="Mandya">Mandya</option>
          <option value="Tumakuru">Tumakuru</option>
        </select>
        <select value={caseTypeFilter} onChange={e => setCaseTypeFilter(e.target.value)} style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: '0.875rem' }}>
          <option value="">All Types</option>
          <option value="Sexual Assault">Sexual Assault</option>
          <option value="Murder">Murder</option>
          <option value="Physical Assault">Physical Assault</option>
          <option value="Domestic Violence">Domestic Violence</option>
          <option value="Trafficking">Trafficking</option>
          <option value="Other Atrocity">Other Atrocity</option>
        </select>
      </div>

      {loading && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Loading cases...</p>}

      {!loading && filtered.length === 0 && (
        <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No cases found.</p>
      )}

      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '0.5rem', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #334155', background: '#0f172a' }}>
              <th style={{ textAlign: 'left', padding: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Case ID</th>
              <th style={{ textAlign: 'left', padding: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Person</th>
              <th style={{ textAlign: 'left', padding: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Case Type</th>
              <th style={{ textAlign: 'left', padding: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>District</th>
              <th style={{ textAlign: 'left', padding: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Counsellor</th>
              <th style={{ textAlign: 'left', padding: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Priority</th>
              <th style={{ textAlign: 'left', padding: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Monitoring</th>
              <th style={{ textAlign: 'left', padding: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Consent</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(c => (
              <tr
                key={c.case_id}
                onClick={() => onSelectCase(c.case_id)}
                style={{ borderBottom: '1px solid #1e293b', cursor: 'pointer' }}
              >
                <td style={{ padding: '0.75rem', color: '#e2e8f0', fontWeight: 600 }}>{c.case_id}</td>
                <td style={{ padding: '0.75rem', color: '#cbd5e1' }}>{c.person_name}</td>
                <td style={{ padding: '0.75rem', color: '#94a3b8' }}>{c.case_type}</td>
                <td style={{ padding: '0.75rem', color: '#94a3b8' }}>{c.district || 'N/A'}</td>
                <td style={{ padding: '0.75rem', color: '#94a3b8' }}>{c.assigned_counsellor || 'N/A'}</td>
                <td style={{ padding: '0.75rem' }}>
                  <span style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: '0.25rem',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    background: c.priority === 'HIGH_PRIORITY' ? '#7f1d1d' : c.priority === 'WATCH' ? '#78350f' : '#14532d',
                    color: priorityColor(c.priority),
                  }}>
                    {c.priority.replace('_', ' ')}
                  </span>
                </td>
                <td style={{ padding: '0.75rem', color: '#94a3b8' }}>{c.monitoring_status || 'N/A'}</td>
                <td style={{ padding: '0.75rem' }}>
                  <span style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: '0.25rem',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    background: c.consent_status === 'granted' ? '#14532d' : '#78350f',
                    color: c.consent_status === 'granted' ? '#86efac' : '#fcd34d',
                  }}>
                    {c.consent_status || 'pending'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
