import { useState, useEffect } from 'react'

interface ProtocolResult {
  category: string
  score: number
  content: string
  source: string
}

interface ProtocolAssistantProps {
  caseContext: string
  onSelectProtocol: (category: string, source: string) => void
}

export default function ProtocolAssistant({ caseContext, onSelectProtocol }: ProtocolAssistantProps) {
  const [query, setQuery] = useState(caseContext)
  const [results, setResults] = useState<ProtocolResult[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setQuery(caseContext)
  }, [caseContext])

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await fetch(`/api/v1/protocols/search?q=${encodeURIComponent(query)}&max_results=3`)
      if (res.ok) {
        const data = await res.json()
        setResults(data.results || [])
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: '#1e293b', marginBottom: '1rem' }}>
      <h3 style={{ color: '#e2e8f0', marginBottom: '0.5rem' }}>Protocol Assistant</h3>
      <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
        Search approved protocols for guidance. The assistant summarizes content but does not make final decisions.
      </p>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && search()}
          placeholder="Describe case context or needs..."
          style={{ flex: 1, padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0' }}
        />
        <button
          onClick={search}
          disabled={loading}
          style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', background: '#2563eb', color: '#fff', cursor: 'pointer' }}
        >
          {loading ? '...' : 'Search'}
        </button>
      </div>
      {results.length === 0 && !loading && (
        <p style={{ color: '#64748b', fontSize: '0.875rem' }}>No protocols retrieved yet.</p>
      )}
      {results.map(r => (
        <div key={r.category} style={{ padding: '0.75rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', marginBottom: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
            <strong style={{ color: '#e2e8f0', textTransform: 'capitalize' }}>{r.category.replace('_', ' ')}</strong>
            <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Source: {r.source}</span>
          </div>
          <p style={{ color: '#cbd5e1', fontSize: '0.875rem', marginBottom: '0.5rem', whiteSpace: 'pre-wrap' }}>
            {r.content.split('\n').slice(0, 6).join('\n')}
          </p>
          <button
            onClick={() => onSelectProtocol(r.category, r.source)}
            style={{ padding: '0.25rem 0.75rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0', cursor: 'pointer', fontSize: '0.875rem' }}
          >
            Use this protocol
          </button>
        </div>
      ))}
    </div>
  )
}
