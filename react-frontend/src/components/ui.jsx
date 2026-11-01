import { useCallback, useEffect, useRef, useState } from 'react'

/** Fetch helper: { data, error, loading, reload }. Optional polling interval (ms). */
export function useApi(fn, { interval = 0, deps = [] } = {}) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const fnRef = useRef(fn)
  fnRef.current = fn

  const reload = useCallback(async () => {
    try {
      const d = await fnRef.current()
      setData(d)
      setError(null)
    } catch (e) {
      setError(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    reload()
    if (!interval) return undefined
    const id = setInterval(reload, interval)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reload, interval, ...deps])

  return { data, error, loading, reload, setData }
}

export function Card({ title, sub, icon, actions, children, className = '', style }) {
  return (
    <section className={`card ${className}`} style={style}>
      {(title || actions) && (
        <div className="card-head">
          <div>
            {title && <h2 className="card-title">{icon}{title}</h2>}
            {sub && <p className="card-sub">{sub}</p>}
          </div>
          {actions && <div className="row wrap">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  )
}

export function Badge({ tone = 'gray', children, dot, pulse }) {
  return (
    <span className={`badge b-${tone}`}>
      {dot && <span className={`dot ${pulse ? 'pulse' : ''}`} />}
      {children}
    </span>
  )
}

export function Kpi({ icon: Icon, color, label, value, foot, footTone }) {
  return (
    <div className="card kpi lift">
      <div className="kpi-icon" style={{ background: `${color}1f`, color, border: `1px solid ${color}40` }}>
        <Icon size={19} aria-hidden="true" />
      </div>
      <div style={{ minWidth: 0 }}>
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">{value}</div>
        {foot && <div className="kpi-foot" style={{ color: `var(--${footTone || 'muted'})` }}>{foot}</div>}
      </div>
    </div>
  )
}

export function Loading({ height = 120 }) {
  return <div className="skeleton" style={{ height }} aria-label="Loading" />
}

export function ErrorBox({ error, hint = true }) {
  if (!error) return null
  return (
    <div className="error-box" role="alert">
      <strong>Could not reach the backend.</strong> {error}
      {hint && <div className="dim" style={{ marginTop: '.35rem' }}>Is <code className="mono">python server.py</code> running on port 8000?</div>}
    </div>
  )
}

export const ESC = [
  { label: 'Level 0 · Normal', tone: 'green', color: 'var(--green)' },
  { label: 'Level 1 · Watch', tone: 'amber', color: 'var(--amber)' },
  { label: 'Level 2 · Warning', tone: 'orange', color: 'var(--orange)' },
  { label: 'Level 3 · Critical', tone: 'red', color: 'var(--red)' },
]

export function EscalationBadge({ level = 0 }) {
  const e = ESC[Math.max(0, Math.min(3, level))]
  return <Badge tone={e.tone} dot pulse={level >= 2}>{e.label}</Badge>
}

export function EscalationLadder({ level = 0 }) {
  return (
    <div className="ladder" role="meter" aria-valuemin={0} aria-valuemax={3} aria-valuenow={level} aria-label="Escalation level">
      {ESC.map((e, i) => (
        <div key={i} style={{ background: i <= level ? e.color : undefined, opacity: i <= level ? 1 : 0.5 }} />
      ))}
    </div>
  )
}

export function timeAgo(iso) {
  if (!iso) return ''
  const s = Math.round((Date.now() - new Date(iso).getTime()) / 1000)
  if (s < 60) return `${s}s ago`
  if (s < 3600) return `${Math.round(s / 60)}m ago`
  if (s < 86400) return `${Math.round(s / 3600)}h ago`
  return new Date(iso).toLocaleDateString()
}
