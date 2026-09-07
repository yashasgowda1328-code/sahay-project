import { useState } from 'react'

interface AlertItem {
  id: number
  case_id: string
  priority: string
  alert_type: string
  status: string
  explanation: string | null
  details: string | null
  requires_counsellor_review: boolean
  created_at: string
  updated_at: string
}

interface AlertReviewProps {
  alert: AlertItem
  onReviewed: () => void
}

export default function AlertReview({ alert, onReviewed }: AlertReviewProps) {
  const [counsellorId, setCounsellorId] = useState('')
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!counsellorId.trim()) return
    setSubmitting(true)
    try {
      const res = await fetch(`/api/v1/alerts/${alert.id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ counsellor_id: counsellorId, review_notes: notes }),
      })
      if (res.ok) {
        onReviewed()
        setNotes('')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: '#1e293b', marginBottom: '1rem' }}>
      <h3 style={{ color: '#e2e8f0', marginBottom: '0.5rem' }}>Review Alert #{alert.id}</h3>
      <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
        <strong>Case:</strong> {alert.case_id} | <strong>Priority:</strong> {alert.priority}
      </p>
      {alert.explanation && (
        <p style={{ color: '#cbd5e1', fontSize: '0.875rem', marginBottom: '0.5rem' }}>{alert.explanation}</p>
      )}
      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem' }}>
        <input
          value={counsellorId}
          onChange={e => setCounsellorId(e.target.value)}
          placeholder="Counsellor ID"
          style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0' }}
        />
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Review notes"
          rows={3}
          style={{ padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0' }}
        />
        <button
          type="submit"
          disabled={submitting}
          style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', background: '#2563eb', color: '#fff', cursor: 'pointer' }}
        >
          {submitting ? 'Saving...' : 'Submit Review'}
        </button>
      </form>
    </div>
  )
}
