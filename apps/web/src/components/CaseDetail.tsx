import { useEffect, useState } from 'react'
import AlertReview from './AlertReview'
import ProtocolAssistant from './ProtocolAssistant'
import InterventionForm from './InterventionForm'
import OutcomeForm from './OutcomeForm'
import AuditHistory from './AuditHistory'

interface CaseDetailProps {
  caseId: string
  onBack: () => void
}

export default function CaseDetail({ caseId, onBack }: CaseDetailProps) {
  const [health, setHealth] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<any>(null)
  const [analysisHistory, setAnalysisHistory] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const [interventions, setInterventions] = useState<any[]>([])
  const [selectedAlert, setSelectedAlert] = useState<any | null>(null)
  const [caseLoading, setCaseLoading] = useState(false)

  useEffect(() => {
    fetch('/api/v1/health')
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data: any) => {
        setHealth(data)
        setLoading(false)
      })
      .catch((err: any) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    if (!caseId) return
    setCaseLoading(true)
    Promise.all([
      fetch(`/api/v1/cases/${encodeURIComponent(caseId)}/status`).then(r => r.ok ? r.json() : Promise.reject()),
      fetch(`/api/v1/cases/${encodeURIComponent(caseId)}/analysis`).then(r => r.json()),
      fetch(`/api/v1/alerts`).then(r => r.ok ? r.json() : Promise.reject()),
      fetch(`/api/v1/cases/${encodeURIComponent(caseId)}/interventions`).then(r => r.ok ? r.json() : Promise.reject()),
    ])
      .then(([statusData, historyData, alertsData, interventionsData]) => {
        setStatus(statusData)
        setAnalysisHistory(historyData)
        setAlerts(alertsData)
        setInterventions(interventionsData)
        setCaseLoading(false)
      })
      .catch(() => setCaseLoading(false))
  }, [caseId])

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: '#94a3b8' }}>Checking connection...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: '#f87171' }}>Error: {error}</p>
        <button onClick={onBack} style={{ marginTop: '1rem', padding: '0.5rem 1rem', cursor: 'pointer' }}>Back</button>
      </div>
    )
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <button onClick={onBack} style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0', cursor: 'pointer', marginRight: '1rem' }}>
            Back
          </button>
          <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Case: {caseId}</span>
        </div>
        {health && (
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Backend: {health.backend}</span>
            <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>DB: {health.database}</span>
          </div>
        )}
      </div>

      {caseLoading && <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>Loading case data...</p>}

      {!caseLoading && !status && (
        <div style={{ padding: '2rem', textAlign: 'center', border: '1px solid #334155', borderRadius: '0.5rem', background: '#1e293b' }}>
          <p style={{ color: '#64748b', fontSize: '0.875rem' }}>No data available for this case.</p>
          <p style={{ color: '#64748b', fontSize: '0.875rem' }}>Ingest readings or start a demo to begin analysis.</p>
        </div>
      )}

      {status && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <div>
              <span style={{ color: '#94a3b8', fontSize: '0.875rem', marginRight: '0.5rem' }}>Priority:</span>
              <PriorityBadge priority={status.priority} />
            </div>
            <div style={{ color: '#64748b', fontSize: '0.875rem' }}>
              Updated: {new Date(status.computed_at).toLocaleString()}
            </div>
          </div>

          {status.details && (
            <div style={{ marginBottom: '1.5rem', padding: '0.75rem 1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: '#1e293b' }}>
              <div style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Explanation</div>
              <div style={{ color: '#e2e8f0', fontSize: '0.875rem' }}>
                {(() => {
                  try {
                    const parsed = JSON.parse(status.details)
                    const parts: string[] = []
                    if (parsed.high_features?.length) parts.push(`High priority features: ${parsed.high_features.join(', ')}`)
                    if (parsed.watch_features?.length) parts.push(`Watch features: ${parsed.watch_features.join(', ')}`)
                    if (parsed.recent_deviations?.length) {
                      const latest = parsed.recent_deviations[0]
                      parts.push(`Latest deviation: ${latest.feature} (z-score ${latest.z_score?.toFixed(2) ?? 'N/A'})`)
                    }
                    return parts.join('. ') || 'No significant deviations detected.'
                  } catch {
                    return status.details
                  }
                })()}
              </div>
            </div>
          )}

          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#e2e8f0' }}>Current Measurements</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {status.current_features && Object.entries(status.current_features).map(([key, data]: [string, any]) => {
                const labels: Record<string, string> = {
                  hr_mean: 'Heart Rate',
                  steps_count: 'Steps',
                  active_ratio: 'Active Ratio',
                  inactive_minutes: 'Inactive Minutes',
                }
                const units: Record<string, string> = {
                  hr_mean: 'bpm',
                  steps_count: 'steps',
                  active_ratio: '',
                  inactive_minutes: 'min',
                }
                const baselineMap: Record<string, number | null> = {
                  hr_mean: status.baseline?.hr_median ?? null,
                  steps_count: status.baseline?.steps_median ?? null,
                  active_ratio: status.baseline?.active_ratio_median ?? null,
                  inactive_minutes: status.baseline?.inactive_minutes_median ?? null,
                }
                const baseline = baselineMap[key] ?? null
                const raw = data.raw_value
                const pct = baseline ? ((raw - baseline) / baseline) * 100 : null
                return (
                  <MetricCard
                    key={key}
                    label={labels[key] || key}
                    current={raw}
                    baseline={baseline}
                    deviation={pct}
                    unit={units[key] || ''}
                  />
                )
              })}
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#e2e8f0' }}>Persistent Change Status</h2>
            {status.deviations && status.deviations.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {status.deviations.map((d: any) => (
                  <div key={d.feature_name} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.75rem 1rem',
                    borderRadius: '0.5rem',
                    border: '1px solid #334155',
                    background: '#1e293b',
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ color: '#94a3b8', fontSize: '0.875rem' }}>{d.feature_name.replace('_', ' ')}</div>
                      <div style={{ color: '#e2e8f0', fontSize: '0.875rem' }}>
                        Z-score: {d.z_score?.toFixed(2)} | Persistence: {d.persistence_count}
                      </div>
                    </div>
                    <PersistenceBadge count={d.persistence_count} changeDetected={d.change_detected} />
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#64748b', fontSize: '0.875rem' }}>No significant deviations detected.</p>
            )}
          </div>

          {analysisHistory.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#e2e8f0' }}>Recent Analysis Timeline</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '300px', overflowY: 'auto' }}>
                {analysisHistory.map((h: any) => (
                  <div key={h.id} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '0.375rem',
                    border: '1px solid #334155',
                    background: '#1e293b',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <PriorityBadge priority={h.priority} />
                      <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
                        {new Date(h.computed_at).toLocaleString()}
                      </span>
                    </div>
                    {h.explanation && (
                      <span style={{ color: '#cbd5e1', fontSize: '0.75rem', maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {h.explanation}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {alerts.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#f87171' }}>Active Alerts</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {alerts.map((a: any) => (
                  <div key={a.id} style={{
                    padding: '1rem',
                    borderRadius: '0.5rem',
                    border: '2px solid #991b1b',
                    background: '#7f1d1d',
                    color: '#fecaca',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <PriorityBadge priority={a.priority} />
                        <span style={{ fontWeight: 600, color: '#fca5a5' }}>Case: {a.case_id}</span>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: '#fecaca' }}>
                        {new Date(a.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.875rem', marginBottom: '0.5rem', color: '#fef2f2', fontWeight: 600 }}>
                      Requires Counsellor Review
                    </div>
                    {a.explanation && (
                      <div style={{ fontSize: '0.875rem', color: '#fecaca', marginBottom: '0.5rem' }}>
                        {a.explanation}
                      </div>
                    )}
                    {a.details && (
                      <pre style={{ fontSize: '0.75rem', color: '#fecaca', whiteSpace: 'pre-wrap', margin: 0 }}>
                        {a.details}
                      </pre>
                    )}
                    <button
                      onClick={() => setSelectedAlert(a)}
                      style={{ marginTop: '0.75rem', padding: '0.5rem 1rem', borderRadius: '0.375rem', border: '1px solid #fecaca', background: 'transparent', color: '#fecaca', cursor: 'pointer' }}
                    >
                      Review Alert
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedAlert && (
            <div style={{ marginTop: '2rem' }}>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#f87171' }}>Counsellor Workflow</h2>
              <AlertReview alert={selectedAlert} onReviewed={() => setSelectedAlert(null)} />
              <ProtocolAssistant caseContext={status?.details || ''} onSelectProtocol={(category: string) => {
                setSelectedAlert((prev: any) => prev ? { ...prev, explanation: `Protocol: ${category}` } : prev)
              }} />
              <InterventionForm caseId={caseId} alertId={selectedAlert.id} onCreated={() => {
                setSelectedAlert(null)
              }} />
              <OutcomeForm interventions={interventions} onRecorded={() => {}} />
              <AuditHistory caseId={caseId} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, { bg: string; text: string; border: string }> = {
    NORMAL: { bg: '#064e3b', text: '#4ade80', border: '#065f46' },
    WATCH: { bg: '#78350f', text: '#fbbf24', border: '#92400e' },
    HIGH_PRIORITY: { bg: '#7f1d1d', text: '#f87171', border: '#991b1b' },
  }
  const c = colors[priority] || colors.NORMAL
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.5rem',
      padding: '0.5rem 1rem',
      borderRadius: '0.5rem',
      border: `1px solid ${c.border}`,
      background: c.bg,
      color: c.text,
      fontWeight: 600,
      fontSize: '0.875rem',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
    }}>
      {priority.replace('_', ' ')}
    </div>
  )
}

function MetricCard({ label, current, baseline, deviation, unit }: {
  label: string
  current: number | null
  baseline: number | null
  deviation: number | null
  unit: string
}) {
  const isDeviated = deviation !== null && Math.abs(deviation) >= 20
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '0.75rem 1rem',
      borderRadius: '0.5rem',
      border: '1px solid #334155',
      background: '#1e293b',
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ color: '#94a3b8', fontSize: '0.875rem' }}>{label}</div>
        <div style={{ color: '#e2e8f0', fontSize: '1.125rem', fontWeight: 600 }}>
          {current !== null ? current.toFixed(2) : '--'} {unit}
        </div>
      </div>
      <div style={{ flex: 1, textAlign: 'right' }}>
        <div style={{ color: '#64748b', fontSize: '0.875rem' }}>Baseline</div>
        <div style={{ color: '#cbd5e1', fontSize: '1.125rem', fontWeight: 600 }}>
          {baseline !== null ? baseline.toFixed(2) : '--'} {unit}
        </div>
      </div>
      {deviation !== null && (
        <div style={{
          color: isDeviated ? '#f87171' : '#4ade80',
          fontWeight: 600,
          fontSize: '0.875rem',
          minWidth: '80px',
          textAlign: 'right',
        }}>
          {deviation >= 0 ? '+' : ''}{deviation.toFixed(1)}%
        </div>
      )}
    </div>
  )
}

function PersistenceBadge({ count, changeDetected }: { count: number; changeDetected: boolean }) {
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.5rem',
      padding: '0.5rem 1rem',
      borderRadius: '0.5rem',
      border: `1px solid ${changeDetected ? '#991b1b' : '#334155'}`,
      background: changeDetected ? '#7f1d1d' : '#1e293b',
      color: changeDetected ? '#f87171' : '#94a3b8',
      fontWeight: 600,
      fontSize: '0.875rem',
    }}>
      {count} consecutive windows
      {changeDetected && ' (Change Detected)'}
    </div>
  )
}
