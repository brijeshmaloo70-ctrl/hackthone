import { useEffect, useRef, useState } from 'react'
import {
  BrainCircuit, CalendarClock, FastForward, HeartHandshake, MessageCircleHeart, MessageSquare,
  Pause, Play, Radio, RotateCcw, ShieldAlert, SkipForward, Stethoscope, Users, Zap,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { PageHint, useToast } from '../components/feedback'
import { Badge, Card, ErrorBox, EscalationBadge, EscalationLadder, Loading, timeAgo, useApi } from '../components/ui'

const AGENT_ICON = {
  Asha: [MessageCircleHeart, '#5b8cff'],
  ConnectAgent: [HeartHandshake, '#10b981'],
  MedInsightAgent: [Stethoscope, '#8b5cf6'],
  RiskAnalysisAgent: [ShieldAlert, '#f97316'],
  SocialWellbeingAgent: [Users, '#ec4899'],
}

const EVENT_TONE = {
  VITALS_ALERT: 'orange', RISK_ALERT_ISSUED: 'red', MEDICATION_MISSED: 'amber', EMERGENCY_TRIGGERED: 'red',
  ESCALATION_NEEDED: 'red', SOCIAL_ISOLATION_DETECTED: 'violet', SOCIAL_INTERVENTION_TRIGGERED: 'violet',
  CHECKIN_COMPLETED: 'green', SCHEDULE_TRIGGERED: 'blue', CAREGIVER_ACTION_RECORDED: 'green',
}

function eventSummary(e) {
  const d = e.data || {}
  if (d.risk_level) return `${d.risk_level}: ${(d.reasons || []).join('; ')}`
  if (e.event_type === 'CHECKIN_COMPLETED') return `BP ${d.bp_systolic}/${d.bp_diastolic} · glucose ${d.blood_glucose} · meds ${d.medication_taken ? 'taken' : 'missed'}`
  if (e.event_type === 'VITALS_ALERT') return `BP ${d.bp_systolic}/${d.bp_diastolic}, glucose ${d.blood_glucose}`
  if (d.action_taken) return `${d.caregiver || 'Caregiver'}: ${d.action_taken}${d.notes ? ` (${d.notes})` : ''}`
  if (d.action) return d.action
  if (d.med_name) return `Missed: ${d.med_name}`
  if (d.job) return `Job ${d.job} at ${d.time}`
  return d.message || d.reason || d.notes || ''
}

function LlmCard() {
  const [status, setStatus] = useState(null)
  const [testing, setTesting] = useState(false)
  const [err, setErr] = useState(null)

  const run = async (live) => {
    setTesting(live)
    try { setStatus(await api.llmStatus(live)); setErr(null) } catch (e) { setErr(e.message) } finally { setTesting(false) }
  }
  useEffect(() => { run(false) }, [])

  const lt = status?.live_test
  return (
    <Card title="Gemini LLM" icon={<BrainCircuit size={17} color="#93b4ff" />} sub="Live connectivity check of the configured key and models"
      actions={<button className="btn btn-ghost btn-sm" onClick={() => run(true)} disabled={testing}>{testing ? <span className="spinner" /> : <Zap size={14} />} Run live test</button>}>
      <ErrorBox error={err} />
      {!status ? <Loading height={90} /> : (
        <div className="stack" style={{ gap: '.6rem', fontSize: '.84rem' }}>
          <div className="row between"><span className="muted">API key</span>{status.configured ? <Badge tone="green">Set ({status.key_preview})</Badge> : <Badge tone="amber">Missing, template mode</Badge>}</div>
          <div className="row between"><span className="muted">Model chain</span><span className="mono" style={{ fontSize: '.72rem', textAlign: 'right' }}>{status.models.join(' → ')}</span></div>
          <div className="row between"><span className="muted">Calls / ok / failed</span><span className="mono">{status.calls} / {status.successes} / {status.failures}</span></div>
          {lt && (lt.ok
            ? <div className="row between"><span className="muted">Live test</span><Badge tone="green" dot>OK · {lt.model}</Badge></div>
            : <div className="error-box" style={{ fontSize: '.75rem' }}><strong>Live test failed:</strong> {lt.error}</div>)}
          {status.last_error && !lt && <div className="error-box" style={{ fontSize: '.75rem' }}><strong>Last error:</strong> {status.last_error}</div>}
        </div>
      )}
    </Card>
  )
}

export default function AgentsLive() {
  const status = useApi(api.status, { interval: 5000 })
  const timeline = useApi(api.timeline)
  const events = useApi(() => api.events(150), { interval: 2500 })
  const wa = useApi(() => api.whatsapp(40), { interval: 2500 })

  const [dayIdx, setDayIdx] = useState(0)
  const [running, setRunning] = useState(false)
  const [auto, setAuto] = useState(false)
  const [log, setLog] = useState([])
  const [err, setErr] = useState(null)
  const autoRef = useRef(false)
  const toast = useToast()

  const reset = async () => {
    if (!window.confirm('Reset the live session? Escalation goes back to 0 and events and messages are cleared. The 30-day history stays.')) return
    try {
      const r = await api.resetLive()
      setLog([]); setDayIdx(0); setAuto(false)
      status.reload(); events.reload(); wa.reload()
      toast(r.message, 'success')
    } catch (e) { toast(e.message, 'error') }
  }

  const days = timeline.data || []
  const current = days[dayIdx]

  const runOne = async (idx) => {
    const rec = days[idx]
    if (!rec) return false
    setRunning(true)
    try {
      const res = await api.runDay(rec.day, rec)
      setLog((l) => [{ day: rec.day, phase: rec.phase, results: res.scheduled_results }, ...l].slice(0, 30))
      setDayIdx(idx + 1)
      setErr(null)
      status.reload(); events.reload(); wa.reload()
      return true
    } catch (e) {
      setErr(e.message); return false
    } finally {
      setRunning(false)
    }
  }

  useEffect(() => {
    autoRef.current = auto
    if (!auto) return undefined
    let cancelled = false
    ;(async () => {
      let idx = dayIdx
      while (!cancelled && autoRef.current && idx < days.length) {
        const ok = await runOne(idx)
        if (!ok) break
        idx += 1
        await new Promise((r) => setTimeout(r, 1200))
      }
      setAuto(false)
    })()
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auto])

  const evs = [...(events.data?.events || [])].sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''))
  const msgs = [...(wa.data?.messages || [])].sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''))
  const level = status.data?.escalation_level ?? 0

  return (
    <>
      <PageHint id="agents" title="Quick demo in 3 steps" steps={[
        'Click “Jump to day 21”, then “Auto-play”. Each day runs the agents’ 4 scheduled jobs.',
        'Watch the event bus and outbound messages fill up. Escalation climbs to Level 2, then Level 3 on day 28.',
        'Open Caregiver to respond to the alerts, Clinician for the AI briefing, Patient to chat with Asha.',
      ]} />
      <div className="steps">
        <Link to="/caregiver" className="step lift"><span className="step-n">1</span><span><strong>Caregiver</strong><br /><span className="muted">Acknowledge alerts and log what you did</span></span></Link>
        <Link to="/clinician" className="step lift"><span className="step-n">2</span><span><strong>Clinician</strong><br /><span className="muted">Trends, AI briefing, approve the care plan</span></span></Link>
        <Link to="/patient" className="step lift"><span className="step-n">3</span><span><strong>Patient</strong><br /><span className="muted">Chat with Asha, check-in, SOS</span></span></Link>
      </div>
      <ErrorBox error={status.error} />

      <div className="grid g-main">
        <Card title="Live simulation driver" icon={<CalendarClock size={17} color="#93b4ff" />}
          sub="Each step runs the proactive scheduler for one day (08:00 check-in → 09:00 meds → 13:00 social → 19:00 risk). Agents react over the event bus."
          actions={<>
            <button className="btn btn-ghost btn-sm" disabled={running || auto || dayIdx >= days.length} onClick={() => runOne(dayIdx)}><SkipForward size={14} /> Run day {current?.day ?? '—'}</button>
            {auto
              ? <button className="btn btn-ghost btn-sm" onClick={() => setAuto(false)}><Pause size={14} /> Pause</button>
              : <button className="btn btn-primary btn-sm" disabled={running || dayIdx >= days.length} onClick={() => setAuto(true)}><Play size={14} /> Auto-play</button>}
            <button className="btn btn-ghost btn-sm" disabled={running || auto} onClick={() => setDayIdx(20)} title="Jump to the dangerous phase"><FastForward size={14} /> Jump to day 21</button>
            <button className="btn btn-ghost btn-sm" disabled={running || auto} onClick={reset} title="Clear live events, messages and escalation"><RotateCcw size={14} /> Reset</button>
          </>}>
          <ErrorBox error={err || timeline.error} />
          {!days.length && !timeline.loading && (
            <div className="empty">No timeline found. Run <code className="mono">python main.py</code> once to generate <code className="mono">data/timeline_enriched.json</code>.</div>
          )}
          {current ? (
            <div className="grid g-4" style={{ gap: '.7rem', marginBottom: '1rem' }}>
              {[
                ['Next day', `Day ${current.day}`, current.phase],
                ['Blood pressure', `${current.bp_systolic}/${current.bp_diastolic}`, current.bp_systolic >= 160 ? 'danger' : current.bp_systolic >= 150 ? 'warning' : 'ok'],
                ['Glucose', `${current.blood_glucose}`, current.blood_glucose >= 300 ? 'danger' : current.blood_glucose >= 250 ? 'warning' : 'ok'],
                ['Meds · Social', `${current.medication_taken ? '✓' : '✗'} · ${current.social_interaction ? '✓' : '✗'}`, current.symptoms?.join(', ') || 'no symptoms'],
              ].map(([l, v, s]) => (
                <div key={l} style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 12, padding: '.75rem' }}>
                  <div className="dim" style={{ fontSize: '.7rem' }}>{l}</div>
                  <div style={{ fontWeight: 800, fontSize: '1.15rem' }}>{v}</div>
                  <div className="muted" style={{ fontSize: '.72rem', textTransform: 'capitalize' }}>{s}</div>
                </div>
              ))}
            </div>
          ) : days.length > 0 && <div className="empty">All 30 days have run. Open the Clinician dashboard to see the results.</div>}

          <div className="row between" style={{ marginBottom: '.4rem' }}>
            <span className="muted" style={{ fontSize: '.8rem' }}>Progress: {dayIdx}/{days.length || 30} days</span>
            <EscalationBadge level={level} />
          </div>
          <div style={{ height: 6, background: 'var(--surface-3)', borderRadius: 99, overflow: 'hidden', marginBottom: '1rem' }}>
            <div style={{ height: '100%', width: `${(dayIdx / (days.length || 30)) * 100}%`, background: 'var(--grad)', transition: 'width .4s' }} />
          </div>

          <div className="feed" style={{ maxHeight: 260 }}>
            {log.length === 0 && <div className="empty">Press <strong>Run day</strong> or <strong>Auto-play</strong> to start the agents.</div>}
            {log.map((entry, i) => (
              <div key={`${entry.day}-${log.length - i}`} className="feed-item fade-in" style={{ flexDirection: 'column', gap: '.3rem' }}>
                <div className="row between"><strong>Day {entry.day}</strong><Badge tone={{ stable: 'green', deteriorating: 'amber', dangerous: 'orange', intervention: 'red' }[entry.phase] || 'gray'}>{entry.phase}</Badge></div>
                {entry.results.map((r) => (
                  <div key={r.job_id} className="mono" style={{ fontSize: '.72rem', color: r.status === 'success' ? 'var(--muted)' : 'var(--red)' }}>
                    {r.result || r.error}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </Card>

        <div className="stack">
          <Card title="Agent registry" icon={<Radio size={17} color="#93b4ff" />}>
            {!status.data ? <Loading height={200} /> : (
              <div className="stack" style={{ gap: '.5rem' }}>
                {status.data.agents.map((a) => {
                  const [I, c] = AGENT_ICON[a.name] || [Radio, '#94a0bd']
                  return (
                    <div key={a.name} className="row" style={{ padding: '.55rem .65rem', background: 'var(--bg-2)', borderRadius: 11, border: '1px solid var(--border)' }}>
                      <I size={17} color={c} aria-hidden="true" />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 600, fontSize: '.85rem' }}>{a.name}</div>
                        <div className="dim" style={{ fontSize: '.72rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.role}</div>
                      </div>
                      <Badge tone="green" dot>{a.status}</Badge>
                    </div>
                  )
                })}
                <div style={{ marginTop: '.5rem' }}><EscalationLadder level={level} /></div>
              </div>
            )}
          </Card>
          <LlmCard />
        </div>
      </div>

      <div className="grid g-2">
        <Card title="Event bus" icon={<Zap size={17} color="#fcd34d" />} sub={`${evs.length} events: agent-to-agent coordination in real time`}>
          <div className="feed" style={{ maxHeight: 420 }}>
            {!evs.length && <div className="empty">No events yet in this server session.</div>}
            {evs.map((e, i) => (
              <div key={`${e.timestamp}-${i}`} className="feed-item">
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div className="row between wrap">
                    <Badge tone={EVENT_TONE[e.event_type] || 'gray'}>{e.event_type}</Badge>
                    <span className="meta">Day {e.day} · {e.source} · {timeAgo(e.timestamp)}</span>
                  </div>
                  <div className="muted" style={{ marginTop: '.3rem', fontSize: '.78rem' }}>{eventSummary(e)}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Outbound messages (mock WhatsApp)" icon={<MessageSquare size={17} color="#6ee7b7" />} sub={`${msgs.length} messages sent by agents to family and doctor`}>
          <div className="feed" style={{ maxHeight: 420 }}>
            {!msgs.length && <div className="empty">Agents haven’t messaged anyone yet.</div>}
            {msgs.map((m) => (
              <div key={m.id} className="feed-item">
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div className="row between wrap">
                    <strong>{m.from} → {m.to}</strong>
                    <span className="meta">{m.message_type === 'urgent_alert' ? '🚨 urgent · ' : ''}{timeAgo(m.timestamp)}</span>
                  </div>
                  <div className="muted" style={{ marginTop: '.3rem', fontSize: '.78rem', whiteSpace: 'pre-wrap' }}>{m.message}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </>
  )
}
