import { useState } from 'react'

interface InterventionFormProps {
  caseId: string
  alertId?: number
  defaultProtocol?: { category: string; source: string } | null
  onCreated: () => void
}

const CATEGORIES = [
  'counselling', 'medical_support', 'protection', 'relocation',
  'legal_aid', 'financial_support', 'rehabilitation', 'other'
]

export default function InterventionForm({ caseId, alertId, defaultProtocol, onCreated }: InterventionFormProps) {
  const [category, setCategory] = useState(defaultProtocol?.category || CATEGORIES[0])
  const [description, setDescription] = useState('')
  const [protocolReference, setProtocolReference] = useState(defaultProtocol?.source || '')
  const [status, setStatus] = useState('PLANNED')
  const [createdBy, setCreatedBy] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!createdBy.trim()) return
    setSubmitting(true)
    try {
      const res = await fetch('/api/v1/interventions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseId,
          alert_id: alertId,
          category,
          description,
          protocol_reference: protocolReference || null,
          status,
          created_by: createdBy,
        }),
      })
      if (res.ok) {
        setDescription('')
        setProtocolReference('')
        onCreated()
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: '#1e293b', marginBottom: '1rem' }}>
      <h3 style={{ color: '#e2e8f0', marginBottom: '0.5rem' }}>Record Intervention</h3>
      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <select
          value={category}
          onChange={e => setCategory(e.target.value)}
          style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0' }}
        >
          {CATEGORIES.map(c => (
            <option key={c} value={c}>{c.replace('_', ' ')}</option>
          ))}
        </select>
        <input
          value={createdBy}
          onChange={e => setCreatedBy(e.target.value)}
          placeholder="Created by (counsellor ID)"
          style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0' }}
        />
        <input
          value={protocolReference}
          onChange={e => setProtocolReference(e.target.value)}
          placeholder="Protocol reference (optional)"
          style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0' }}
        />
        <textarea
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="Intervention description"
          rows={3}
          style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0' }}
        />
        <select
          value={status}
          onChange={e => setStatus(e.target.value)}
          style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0' }}
        >
          <option value="PLANNED">PLANNED</option>
          <option value="IN_PROGRESS">IN_PROGRESS</option>
          <option value="COMPLETED">COMPLETED</option>
          <option value="CANCELLED">CANCELLED</option>
        </select>
        <button
          type="submit"
          disabled={submitting}
          style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', background: '#16a34a', color: '#fff', cursor: 'pointer' }}
        >
          {submitting ? 'Saving...' : 'Create Intervention'}
        </button>
      </form>
    </div>
  )
}
