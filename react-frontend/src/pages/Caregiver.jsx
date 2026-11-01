import { useState } from 'react'
import {
  BellRing, CalendarCheck, CircleCheck, Droplet, HeartPulse, House, MessageSquare, PenLine, Phone,
  Pill, ShieldAlert, Stethoscope, Users, Zap,
} from 'lucide-react'
import { api } from '../api'
import { PageHint, useToast } from '../components/feedback'
import { Badge, Card, ErrorBox, EscalationLadder, ESC, Kpi, Loading, timeAgo, useApi } from '../components/ui'

const URGENCY = {
  critical: { tone: 'red', label: 'Urgent' },
  moderate: { tone: 'amber', label: 'Needs attention' },
  normal: { tone: 'blue', label: 'For your information' },
}
const QUICK = [
  { icon: Phone, label: 'I called Papa' },
  { icon: House, label: 'I visited him' },
  { icon: Pill, label: 'Reminded him about medicines' },
  { icon: Stethoscope, label: 'Booked a doctor visit' },
]
const SOURCE = { ConnectAgent: 'ConnectAgent', SocialWellbeingAgent: 'Social wellbeing', AshaChat: 'Asha chat', EmergencySOS: 'SOS button' }
const TABS = [['open', 'Needs action'], ['critical', 'Urgent'], ['done', 'Done'], ['all', 'All']]
const PAGE = 8

function AlertCard({ a, onAck }) {
  const [busy, setBusy] = useState(false)
  const [custom, setCustom] = useState(false)
  const [text, setText] = useState('')
  const [note, setNote] = useState('')
  const u = URGENCY[a.urgency] || URGENCY.normal

  const log = async (action, notes = '') => {
    setBusy(true)
    const ok = await onAck(a.alert_id, action, notes)
    setBusy(false)
    if (ok) { setCustom(false); setText(''); setNote('') }
  }

  return (
    <article className={`alert-card ${a.urgency === 'critical' && !a.acknowledged ? 'critical' : ''} ${a.acknowledged ? 'done' : ''}`}>
      <div className="row between wrap">
        <div className="row wrap">
          <Badge tone={a.acknowledged ? 'gray' : u.tone} dot pulse={a.urgency === 'critical' && !a.acknowledged}>{u.label}</Badge>
          <span className="dim" style={{ fontSize: '.74rem' }}>Day {a.day} · from {SOURCE[a.source] || a.source} · {timeAgo(a.timestamp)}</span>
        </div>
      </div>
      <div className="alert-msg">{a.message}</div>

      {a.acknowledged ? (
        <div className="done-line">
          <CircleCheck size={15} aria-hidden="true" />
          <span>You logged <strong>“{a.action_taken}”</strong>{a.notes ? `: ${a.notes}` : ''} · {timeAgo(a.acknowledged_at)}</span>
        </div>
      ) : custom ? (
        <form className="stack" style={{ gap: '.5rem' }} onSubmit={(e) => { e.preventDefault(); if (text.trim()) log(text.trim(), note.trim()) }}>
          <div className="grid g-2" style={{ gap: '.5rem' }}>
            <input className="input" autoFocus placeholder="What did you do? e.g. Asked neighbour to check" value={text} onChange={(e) => setText(e.target.value)} aria-label="Action taken" />
            <input className="input" placeholder="Note for the care team (optional)" value={note} onChange={(e) => setNote(e.target.value)} aria-label="Note" />
          </div>
          <div className="row">
            <button className="btn btn-primary btn-sm" disabled={busy || !text.trim()}>{busy ? <span className="spinner" /> : <CircleCheck size={14} />} Log action</button>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setCustom(false)}>Cancel</button>
          </div>
        </form>
      ) : (
        <div className="quick-actions">
          <span className="lbl">What did you do?</span>
          {QUICK.map(({ icon: I, label }) => (
            <button key={label} className="qa" disabled={busy} onClick={() => log(label)}><I size={14} aria-hidden="true" /> {label}</button>
          ))}
          <button className="qa" disabled={busy} onClick={() => setCustom(true)}><PenLine size={14} aria-hidden="true" /> Something else…</button>
          {busy && <span className="spinner" />}
        </div>
      )}
    </article>
  )
}

export default function Caregiver() {
  const dash = useApi(api.caregiverDashboard, { interval: 5000 })
  const wa = useApi(() => api.whatsapp(60), { interval: 5000 })
  const toast = useToast()
  const [tab, setTab] = useState('open')
  const [shown, setShown] = useState(PAGE)
  const [seeding, setSeeding] = useState(false)
  const [bulkBusy, setBulkBusy] = useState(false)

  const d = dash.data
  const alerts = d?.notifications || []
  const counts = {
    open: alerts.filter((a) => !a.acknowledged).length,
    critical: alerts.filter((a) => a.urgency === 'critical' && !a.acknowledged).length,
    done: alerts.filter((a) => a.acknowledged).length,
    all: alerts.length,
  }
  const filtered = alerts
    .filter((a) => (tab === 'open' ? !a.acknowledged : tab === 'critical' ? a.urgency === 'critical' && !a.acknowledged : tab === 'done' ? a.acknowledged : true))
    // urgent first, then newest
    .sort((x, y) => (y.urgency === 'critical') - (x.urgency === 'critical') || (y.timestamp || '').localeCompare(x.timestamp || ''))

  const ack = async (id, action, notes) => {
    try {
      const r = await api.acknowledge(id, action, notes)
      toast(r.message || 'Logged. The care team can see it.', 'success')
      dash.setData((prev) => prev && ({
        ...prev,
        notifications: prev.notifications.map((n) => (n.alert_id === id ? r.alert : n)),
        unacknowledged_count: Math.max(0, (prev.unacknowledged_count || 1) - 1),
      }))
      dash.reload()
      return true
    } catch (e) {
      toast(`Couldn't save: ${e.message}`, 'error')
      return false
    }
  }

  const seed = async () => {
    setSeeding(true)
    try {
      const n = await api.runDays(21, 24)
      toast(`Ran ${n} risky days through the agents. New alerts are below.`, 'success')
      dash.reload(); wa.reload()
    } catch (e) { toast(e.message, 'error') } finally { setSeeding(false) }
  }

  const phone = d?.caregiver?.phone
  const thread = [...(wa.data?.messages || [])].filter((m) => !phone || m.to === phone || m.from === phone)
    .sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''))
  const lvl = d?.escalation_level ?? 0
  const lv = d?.latest_vitals
  // Colour by what needs the caregiver now, not only the escalation level
  const statusColor = counts.critical > 0 ? 'var(--red)' : counts.open > 0 ? 'var(--amber)' : ESC[lvl].color
  const nonUrgentOpen = alerts.filter((a) => !a.acknowledged && a.urgency !== 'critical')
  const actions = (d?.recent_actions || []).filter((x) => x.action_taken !== 'Seen')

  const markSeen = async () => {
    if (!window.confirm(`Mark ${nonUrgentOpen.length} non-urgent alerts as seen? Urgent alerts stay open.`)) return
    setBulkBusy(true)
    let ok = 0
    for (const a of nonUrgentOpen) {
      try { await api.acknowledge(a.alert_id, 'Seen', 'Marked as seen from the caregiver hub'); ok++ } catch { /* keep going */ }
    }
    setBulkBusy(false)
    toast(`Marked ${ok} alerts as seen.`, 'success')
    dash.reload()
  }

  return (
    <>
      <PageHint id="caregiver" title="How to respond to an alert" steps={[
        'Alerts that still need you are under “Needs action”. Urgent ones are shown first.',
        'Read the alert, then tap what you did, e.g. “I called Papa”. It is saved straight away.',
        'Did something different? Tap “Something else…”, type it, and add a note for Dr. Sharma if you like.',
        'Logged alerts move to “Done”. The care team and the event log in the Agent Control Room both see your action.',
      ]} />
      <ErrorBox error={dash.error} />
      {!d && !dash.error && <Loading height={110} />}

      {d && (
        <>
          <Card>
            <div className="big-status" style={{ background: `color-mix(in srgb, ${statusColor} 10%, transparent)`, border: `1px solid color-mix(in srgb, ${statusColor} 35%, transparent)` }}>
              {counts.critical > 0 ? <ShieldAlert size={30} color="var(--red)" aria-hidden="true" /> : <CircleCheck size={30} color="var(--green)" aria-hidden="true" />}
              <div style={{ flex: 1 }}>
                <h2>
                  {counts.critical > 0
                    ? `${counts.critical} urgent alert${counts.critical > 1 ? 's' : ''} about Papa need your response`
                    : counts.open > 0 ? `${counts.open} update${counts.open > 1 ? 's' : ''} waiting for you` : 'All caught up. Nothing needs your action.'}
                </h2>
                <p>{d.patient.name}, {d.patient.age} · {d.patient.conditions.join(' · ')} · {d.patient.doctor}</p>
                <div style={{ maxWidth: 260, marginTop: '.5rem' }}><EscalationLadder level={lvl} /></div>
              </div>
              <a className="btn btn-danger" href="tel:108"><Phone size={16} /> Call 108</a>
            </div>
          </Card>

          <div className="grid g-4">
            <Kpi icon={HeartPulse} color="#ef4444" label={`Latest BP${lv ? ` (day ${lv.day})` : ''}`} value={lv ? `${lv.bp_systolic}/${lv.bp_diastolic}` : '—'} foot={lv && lv.bp_systolic >= 150 ? 'High, keep an eye on it' : 'Target under 140/90'} footTone={lv && lv.bp_systolic >= 150 ? 'orange' : 'green'} />
            <Kpi icon={Droplet} color="#f59e0b" label="Latest sugar (mg/dL)" value={lv ? lv.blood_glucose : '—'} foot={lv && lv.blood_glucose >= 250 ? 'High' : 'Target 100–180'} footTone={lv && lv.blood_glucose >= 250 ? 'orange' : 'green'} />
            <Kpi icon={Pill} color="#8b5cf6" label="Medicines taken (last 7 days)" value={`${d.adherence_7d_pct}%`} foot={d.adherence_7d_pct < 80 ? 'He is missing doses' : 'On track'} footTone={d.adherence_7d_pct < 80 ? 'red' : 'green'} />
            <Kpi icon={Users} color="#ec4899" label="Days with company (last 7)" value={`${d.social_interaction_days_7d}/7`} foot={d.isolation_days_7d >= 3 ? `${d.isolation_days_7d} days alone, call him` : 'Good'} footTone={d.isolation_days_7d >= 3 ? 'orange' : 'green'} />
          </div>
        </>
      )}

      <div className="grid g-main">
        <Card title="Alerts about Papa" icon={<BellRing size={17} color="#fcd34d" />} sub="Sent by ConnectAgent and the other agents. Tap what you did to log it."
          actions={nonUrgentOpen.length > 0 && (
            <button className="btn btn-ghost btn-sm" onClick={markSeen} disabled={bulkBusy}>
              {bulkBusy ? <span className="spinner" /> : <CircleCheck size={14} />} Mark {nonUrgentOpen.length} non-urgent as seen
            </button>
          )}>
          <div className="seg" role="tablist" aria-label="Filter alerts" style={{ marginBottom: '1rem' }}>
            {TABS.map(([k, l]) => (
              <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? 'on' : ''} onClick={() => { setTab(k); setShown(PAGE) }}>
                {l} <span className="dim">({counts[k]})</span>
              </button>
            ))}
          </div>

          <div className="stack" style={{ gap: '.7rem' }}>
            {d && alerts.length === 0 && (
              <div className="empty">
                <p style={{ marginBottom: '.8rem' }}>No alerts yet. Run <code className="mono">python main.py</code> to load the 30-day history, or simulate a few risky days now.</p>
                <button className="btn btn-primary" onClick={seed} disabled={seeding}>{seeding ? <span className="spinner" /> : <Zap size={15} />} Simulate days 21–24</button>
              </div>
            )}
            {d && alerts.length > 0 && filtered.length === 0 && (
              <div className="empty"><CircleCheck size={22} color="var(--green)" /><p>Nothing here. {tab === 'open' || tab === 'critical' ? 'You’ve responded to everything.' : ''}</p></div>
            )}
            {filtered.slice(0, shown).map((a) => <AlertCard key={a.alert_id} a={a} onAck={ack} />)}
            {filtered.length > shown && (
              <button className="btn btn-ghost" onClick={() => setShown((s) => s + PAGE)}>Show {Math.min(PAGE, filtered.length - shown)} more ({filtered.length - shown} left)</button>
            )}
          </div>
        </Card>

        <div className="stack">
          <Card title="What you’ve done" icon={<CircleCheck size={17} color="#6ee7b7" />} sub="Visible to Dr. Sharma">
            <div className="feed" style={{ maxHeight: 260 }}>
              {d && !actions.length && <div className="empty">Nothing logged yet.</div>}
              {actions.map((x) => (
                <div key={x.id} className="feed-item" style={{ flexDirection: 'column', gap: '.15rem' }}>
                  <strong>{x.action_taken}</strong>
                  {x.notes && <span className="muted" style={{ fontSize: '.78rem' }}>{x.notes}</span>}
                  <span className="meta">Day {x.day} · {timeAgo(x.timestamp)}</span>
                </div>
              ))}
            </div>
          </Card>
          <Card title="WhatsApp messages to you" icon={<MessageSquare size={17} color="#6ee7b7" />} sub="This server session (mock gateway)">
            <div className="feed" style={{ maxHeight: 320 }}>
              {!thread.length && <div className="empty">No messages in this session yet.</div>}
              {thread.slice(0, 20).map((m) => (
                <div key={m.id} className="feed-item" style={{ flexDirection: 'column', gap: '.2rem' }}>
                  <span className="meta">{m.from} · {timeAgo(m.timestamp)}</span>
                  <span className="muted" style={{ fontSize: '.78rem', whiteSpace: 'pre-wrap' }}>{m.message}</span>
                </div>
              ))}
            </div>
          </Card>
          <Card title="Next appointment" icon={<CalendarCheck size={17} color="#93b4ff" />}>
            {d && <p className="muted" style={{ fontSize: '.86rem' }}>{d.patient.next_appointment} with {d.patient.doctor}, {d.patient.hospital}. Bring his medicine strip and BP diary.</p>}
          </Card>
        </div>
      </div>
    </>
  )
}
