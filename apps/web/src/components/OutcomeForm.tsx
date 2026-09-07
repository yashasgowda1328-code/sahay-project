import { useState, useEffect } from 'react'

interface Intervention {
  id: number
  case_id: string
  category: string
  description: string | null
  protocol_reference: string | null
  status: string
  created_by: string
  created_at: string
  updated_at: string
}

interface OutcomeFormProps {
  interventions: Intervention[]
  onRecorded: () => void
}

export default function OutcomeForm({ interventions, onRecorded }: OutcomeFormProps) {
  const [selectedId, setSelectedId] = useState<number | ''>('')
  const [notes, setNotes] = useState('')
  const [recordedBy, setRecordedBy] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (interventions.length > 0 && !selectedId) {
      setSelectedId(interventions[0].id)
    }
  }, [interventions, selectedId])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedId || !recordedBy.trim()) return
    setSubmitting(true)
    try {
      const res = await fetch('/api/v1/outcomes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intervention_id: selectedId, outcome_notes: notes, recorded_by: recordedBy }),
      })
      if (res.ok) {
        setNotes('')
        onRecorded()
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: '#1e293b', marginBottom: '1rem' }}>
      <h3 style={{ color: '#e2e8f0', marginBottom: '0.5rem' }}>Record Outcome</h3>
      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <select
          value={selectedId}
          onChange={e => setSelectedId(Number(e.target.value))}
          style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0' }}
        >
          {interventions.map(i => (
            <option key={i.id} value={i.id}>
              #{i.id} - {i.category.replace('_', ' ')} ({i.status})
            </option>
          ))}
        </select>
        <input
          value={recordedBy}
          onChange={e => setRecordedBy(e.target.value)}
          placeholder="Recorded by (counsellor ID)"
          style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0' }}
        />
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Outcome notes"
          rows={3}
          style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0' }}
        />
        <button
          type="submit"
          disabled={submitting}
          style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', background: '#2563eb', color: '#fff', cursor: 'pointer' }}
        >
          {submitting ? 'Saving...' : 'Save Outcome'}
        </button>
      </form>
    </div>
  )
}
