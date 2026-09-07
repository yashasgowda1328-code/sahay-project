interface CaseItem {
  case_id: string
  priority: string
  computed_at: string | null
}

interface CasesListProps {
  cases: CaseItem[]
  onSelect: (caseId: string) => void
  onStartDemo: () => void
}

export default function CasesList({ cases, onSelect, onStartDemo }: CasesListProps) {
  return (
    <div style={{ padding: '2rem', maxWidth: '700px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ color: '#e2e8f0', margin: 0 }}>Cases</h2>
        <button
          onClick={onStartDemo}
          style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', background: '#2563eb', color: '#fff', cursor: 'pointer' }}
        >
          Start Demo
        </button>
      </div>
      {cases.length === 0 && (
        <p style={{ color: '#64748b', fontSize: '0.875rem' }}>No cases found. Start a demo or ingest readings.</p>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {cases.map(c => (
          <div
            key={c.case_id}
            onClick={() => onSelect(c.case_id)}
            style={{
              padding: '0.75rem 1rem',
              borderRadius: '0.5rem',
              border: '1px solid #334155',
              background: '#1e293b',
              color: '#e2e8f0',
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontWeight: 600 }}>{c.case_id}</span>
            <span style={{ fontSize: '0.875rem', color: '#94a3b8' }}>
              {c.priority ? c.priority.replace('_', ' ') : 'N/A'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
