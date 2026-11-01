import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { Activity, Bot, HeartHandshake, House, Menu, MessageCircleHeart, ServerCrash, Stethoscope } from 'lucide-react'
import { api } from '../api'
import { Badge, EscalationBadge, useApi } from './ui'

const LINKS = [
  { to: '/agents', label: 'Agent Control Room', icon: Bot, title: 'Agent Control Room', sub: 'Run the 5-agent network live and watch them coordinate' },
  { to: '/caregiver', label: 'Caregiver', icon: HeartHandshake, title: 'Caregiver Hub', sub: 'For Suresh: alerts about Papa, and what you did about them' },
  { to: '/clinician', label: 'Clinician', icon: Stethoscope, title: 'Clinician Dashboard', sub: 'For Dr. Sharma: 30-day trends, AI briefing, care-plan approvals' },
  { to: '/patient', label: 'Patient · Asha', icon: MessageCircleHeart, title: 'Patient Companion', sub: 'For Ramesh-ji: talk to Asha, log today’s check-in, SOS' },
]

export function Brand() {
  return (
    <span className="brand">
      <span className="brand-mark"><Activity size={18} color="#fff" aria-hidden="true" /></span>
      <span>CareSync <span className="grad-text">AI</span></span>
    </span>
  )
}

export function LlmPill() {
  const { data, error } = useApi(() => api.llmStatus(false), { interval: 15000 })
  if (error) return <Badge tone="red" dot>Backend offline</Badge>
  if (!data) return <Badge tone="gray">Checking LLM…</Badge>
  if (!data.configured) return <Badge tone="amber" dot>Template mode (no key)</Badge>
  if (data.last_error) return <Badge tone="orange" dot>Gemini errors</Badge>
  return <Badge tone="green" dot pulse>Gemini · {data.last_model_used || data.models?.[0]}</Badge>
}

export default function Layout() {
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()
  const page = LINKS.find((l) => pathname.startsWith(l.to)) || LINKS[0]
  const status = useApi(api.status, { interval: 6000 })
  const cg = useApi(api.caregiverDashboard, { interval: 6000 })
  const unacked = cg.data?.unacknowledged_count || 0
  // Pages fire this after changing state so the nav badge / escalation update instantly
  const { reload: reloadCg } = cg
  const { reload: reloadStatus } = status
  useEffect(() => {
    const h = () => { reloadCg(); reloadStatus() }
    window.addEventListener('caresync:changed', h)
    return () => window.removeEventListener('caresync:changed', h)
  }, [reloadCg, reloadStatus])

  return (
    <div className="shell">
      <aside className={`sidebar ${open ? 'open' : ''}`} aria-label="Primary">
        <NavLink to="/" onClick={() => setOpen(false)}><Brand /></NavLink>
        <nav className="nav">
          <span className="nav-label">Portals</span>
          {LINKS.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)}>
              <Icon size={17} aria-hidden="true" /> {label}
              {to === '/caregiver' && unacked > 0 && <span className="nav-count" aria-label={`${unacked} alerts need action`}>{unacked > 99 ? '99+' : unacked}</span>}
            </NavLink>
          ))}
          <span className="nav-label">Site</span>
          <NavLink to="/" end onClick={() => setOpen(false)}><House size={17} aria-hidden="true" /> Home</NavLink>
        </nav>
        <div className="sidebar-foot card" style={{ padding: '.9rem' }}>
          <div className="dim" style={{ fontSize: '.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em' }}>Patient</div>
          <div style={{ fontWeight: 700, marginTop: '.2rem' }}>Ramesh Kumar, 78M</div>
          <div className="muted" style={{ fontSize: '.78rem', marginBottom: '.5rem' }}>Hypertension · T2 Diabetes</div>
          {status.data && <EscalationBadge level={status.data.escalation_level} />}
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="row">
            <button className="menu-btn" onClick={() => setOpen((o) => !o)} aria-label="Toggle navigation" aria-expanded={open}>
              <Menu size={18} />
            </button>
            <div>
              <h1>{page.title}</h1>
              <p>{page.sub}</p>
            </div>
          </div>
          <LlmPill />
        </header>
        {status.error && (
          <div className="banner" role="alert">
            <ServerCrash size={17} aria-hidden="true" />
            <span>Can’t reach the backend. Start it with <code>python server.py</code>. This page reconnects automatically.</span>
          </div>
        )}
        <main className="content fade-in" key={pathname}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
