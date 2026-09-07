interface DemoControlsProps {
  demoState: {
    case_id: string
    phase: number
    status: string
  } | null
  onStart: () => void
  onTick: () => void
  onReset: () => void
  speed: number
  onSpeedChange: (speed: number) => void
}

export default function DemoControls({ demoState, onStart, onTick, onReset, speed, onSpeedChange }: DemoControlsProps) {
  const isRunning = demoState && demoState.phase > 0 && demoState.status !== 'completed'
  const isCompleted = demoState && demoState.status === 'completed'

  const statusColors: Record<string, string> = {
    'not_started': '#94a3b8',
    'baseline_complete': '#4ade80',
    'watch_possible': '#fbbf24',
    'high_priority': '#f87171',
    'intervention_ready': '#fbbf24',
    'recovery': '#4ade80',
    'normal': '#4ade80',
    'completed': '#4ade80',
  }

  return (
    <div style={{ padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155', background: '#1e293b', marginBottom: '1rem' }}>
      <h3 style={{ color: '#e2e8f0', marginBottom: '0.75rem' }}>Demo Mode</h3>
      
      {demoState && (
        <div style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Status:</span>
          <span style={{ 
            color: statusColors[demoState.status] || '#94a3b8', 
            fontSize: '0.875rem', 
            fontWeight: 600,
            textTransform: 'uppercase',
          }}>
            {demoState.status.replace('_', ' ')}
          </span>
          {demoState.phase > 0 && (
            <span style={{ color: '#64748b', fontSize: '0.875rem' }}>Phase {demoState.phase}/6</span>
          )}
        </div>
      )}

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
        {!isRunning && !isCompleted && (
          <button
            onClick={onStart}
            style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', background: '#16a34a', color: '#fff', cursor: 'pointer' }}
          >
            Start Demo
          </button>
        )}
        {isRunning && (
          <button
            onClick={onTick}
            style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: 'none', background: '#2563eb', color: '#fff', cursor: 'pointer' }}
          >
            Advance Phase
          </button>
        )}
        {isRunning || isCompleted || (demoState && demoState.phase > 0) ? (
          <button
            onClick={onReset}
            style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0', cursor: 'pointer' }}
          >
            Reset
          </button>
        ) : null}
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Speed:</span>
        {[1, 10, 60].map(s => (
          <button
            key={s}
            onClick={() => onSpeedChange(s)}
            style={{
              padding: '0.25rem 0.75rem',
              borderRadius: '0.375rem',
              border: speed === s ? '1px solid #2563eb' : '1px solid #334155',
              background: speed === s ? '#1e3a8a' : '#1e293b',
              color: speed === s ? '#fff' : '#e2e8f0',
              cursor: 'pointer',
              fontSize: '0.875rem',
            }}
          >
            {s}x
          </button>
        ))}
      </div>
    </div>
  )
}
