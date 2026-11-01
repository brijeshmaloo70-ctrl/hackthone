import { useMemo, useState } from 'react'
import { Bar, Line } from 'react-chartjs-2'
import '../components/charts'
import { Activity, Check, ClipboardList, Droplet, FileText, HeartPulse, Pill, Sparkles, X } from 'lucide-react'
import { api } from '../api'
import { baseOptions, fill, threshold } from '../components/charts'
import Markdown from '../components/Markdown'
import { PageHint, useToast } from '../components/feedback'
import { Badge, Card, ErrorBox, EscalationBadge, Kpi, Loading, useApi } from '../components/ui'

const PHASES = [['all', 'All'], ['stable', 'Stable'], ['deteriorating', 'Drifting'], ['dangerous', 'Dangerous'], ['intervention', 'Intervention']]
const avg = (a) => (a.length ? Math.round((a.reduce((s, x) => s + x, 0) / a.length) * 10) / 10 : 0)

function AiBriefing() {
  const [state, setState] = useState({ loading: false, data: null, error: null })
  const gen = async () => {
    setState({ loading: true, data: null, error: null })
    try { setState({ loading: false, data: await api.aiBriefing(), error: null }) } catch (e) { setState({ loading: false, data: null, error: e.message }) }
  }
  const d = state.data
  return (
    <Card title="AI pre-visit briefing" icon={<Sparkles size={17} color="#c4b5fd" />} sub="MedInsightAgent asks Gemini to summarise the 10-point dashboard for Dr. Sharma"
      actions={<button className="btn btn-primary btn-sm" onClick={gen} disabled={state.loading}>{state.loading ? <span className="spinner" /> : <Sparkles size={14} />} {d ? 'Regenerate' : 'Generate'}</button>}>
      <ErrorBox error={state.error} />
      {state.loading && <Loading height={160} />}
      {!d && !state.loading && <div className="empty">Click <strong>Generate</strong> for an LLM-written briefing based on the patient's stored data.</div>}
      {d && (
        <>
          <div className="row" style={{ marginBottom: '.6rem' }}>
            {d.llm_used ? <Badge tone="green" dot>Gemini · {d.model}</Badge> : <Badge tone="amber" dot>Rule-based fallback</Badge>}
            {d.llm_error && <span className="dim" style={{ fontSize: '.72rem' }}>{d.llm_error}</span>}
          </div>
          <Markdown text={d.briefing} />
        </>
      )}
    </Card>
  )
}

function Proposals() {
  const plan = useApi(api.carePlan, { interval: 8000 })
  const toast = useToast()
  const [busy, setBusy] = useState(null)
  const review = async (id, approve) => {
    setBusy(id)
    try {
      await api.reviewProposal(id, approve, approve ? 'Approved after 30-day trend review.' : 'Not indicated at this time.')
      toast(approve ? 'Approved and added to the care plan.' : 'Proposal rejected.', 'success')
      await plan.reload()
    } catch (e) { toast(e.message, 'error') } finally { setBusy(null) }
  }
  const props = plan.data?.proposals || []
  return (
    <Card title="Care-plan proposals" icon={<ClipboardList size={17} color="#93b4ff" />} sub="Agents propose changes. Medication changes need clinician approval.">
      <ErrorBox error={plan.error} />
      {!plan.data && !plan.error && <Loading />}
      <div className="stack" style={{ gap: '.6rem' }}>
        {plan.data && !props.length && <div className="empty">No proposals.</div>}
        {props.map((p) => (
          <div key={p.id} className="feed-item" style={{ flexDirection: 'column' }}>
            <div className="row between wrap">
              <strong>{String(p.proposed_value)}</strong>
              <Badge tone={p.status === 'approved' ? 'green' : p.status === 'rejected' ? 'red' : 'amber'}>{p.status.replace('_', ' ')}</Badge>
            </div>
            <div className="muted" style={{ fontSize: '.78rem' }}>{p.reason}</div>
            <div className="row between wrap">
              <span className="meta">{p.agent_name} · {p.category}{p.requires_clinical_approval ? ' · needs clinician' : ''}</span>
              {p.status === 'pending_review' && (
                <div className="row">
                  <button className="btn btn-ghost btn-sm" disabled={busy === p.id} onClick={() => review(p.id, false)}><X size={13} /> Reject</button>
                  <button className="btn btn-primary btn-sm" disabled={busy === p.id} onClick={() => review(p.id, true)}><Check size={13} /> Approve</button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

export default function Clinician() {
  const tl = useApi(api.timeline)
  const dash = useApi(api.clinicianDashboard, { interval: 10000 })
  const report = useApi(api.report)
  const [phase, setPhase] = useState('all')
  const [showReport, setShowReport] = useState(false)

  const all = useMemo(() => tl.data || [], [tl.data])
  const rows = phase === 'all' ? all : all.filter((d) => d.phase === phase)
  const labels = rows.map((d) => `D${d.day}`)
  const n = rows.length

  const stats = useMemo(() => {
    const taken = all.filter((d) => d.medication_taken).length
    return {
      bp: avg(all.map((d) => d.bp_systolic)), dia: avg(all.map((d) => d.bp_diastolic)),
      glu: avg(all.map((d) => d.blood_glucose)), hr: avg(all.map((d) => d.heart_rate)),
      adh: all.length ? Math.round((taken / all.length) * 1000) / 10 : 0,
      iso: all.filter((d) => !d.social_interaction).length,
    }
  }, [all])

  const d = dash.data
  const adherence = d?.['3_medication_adherence']

  return (
    <>
      <PageHint id="clinician" title="Preparing for Ramesh-ji’s visit" steps={[
        'The top cards and charts summarise all 30 days. Use the phase tabs to zoom into one period.',
        'Click “Generate” in AI pre-visit briefing for a Gemini-written summary of the stored data.',
        'Approve or reject the agents’ care-plan proposals. Medication changes always need you.',
        'Open the daily log or the full report at the bottom for detail.',
      ]} />
      <ErrorBox error={tl.error || dash.error} />

      <div className="grid g-4">
        <Kpi icon={HeartPulse} color="#ef4444" label="Avg blood pressure (30d)" value={tl.data ? `${stats.bp}/${stats.dia}` : '…'} foot="Target 120–140 / 70–90" footTone={stats.bp > 140 ? 'orange' : 'green'} />
        <Kpi icon={Droplet} color="#f59e0b" label="Avg glucose (30d)" value={tl.data ? `${stats.glu}` : '…'} foot="Target 100–180 mg/dL" footTone={stats.glu > 180 ? 'orange' : 'green'} />
        <Kpi icon={Activity} color="#5b8cff" label="Avg heart rate" value={tl.data ? `${stats.hr} bpm` : '…'} foot="Normal 60–90" footTone="green" />
        <Kpi icon={Pill} color="#8b5cf6" label="Medication adherence" value={adherence ? `${adherence.rate_pct}%` : tl.data ? `${stats.adh}%` : '…'} foot={adherence ? `${adherence.status} · target 95%` : 'Target 95%'} footTone={(adherence?.rate_pct ?? stats.adh) < 80 ? 'red' : 'green'} />
      </div>

      <div className="row between wrap">
        <div className="seg" role="tablist" aria-label="Phase filter">
          {PHASES.map(([k, l]) => <button key={k} role="tab" aria-selected={phase === k} className={phase === k ? 'on' : ''} onClick={() => setPhase(k)}>{l}</button>)}
        </div>
        {d && <EscalationBadge level={d['7_risk_indicators'].current_escalation_level} />}
      </div>

      <div className="grid g-main">
        <Card title="Blood pressure trend" sub="Systolic / diastolic. Dashed lines are the 150 warning and 160 danger thresholds.">
          <div style={{ height: 280 }}>
            {tl.loading ? <Loading height={280} /> : (
              <Line options={baseOptions()} data={{
                labels,
                datasets: [
                  { label: 'Systolic', data: rows.map((r) => r.bp_systolic), borderColor: '#ef4444', backgroundColor: fill('#ef4444'), fill: true, tension: .35, pointRadius: 2 },
                  { label: 'Diastolic', data: rows.map((r) => r.bp_diastolic), borderColor: '#5b8cff', tension: .35, pointRadius: 2 },
                  threshold('Warning 150', 150, n, '#f59e0b'), threshold('Danger 160', 160, n, '#ef4444aa'),
                ],
              }} />
            )}
          </div>
        </Card>
        <Card title="Blood glucose" sub="mg/dL · warning 250, danger 300">
          <div style={{ height: 280 }}>
            {tl.loading ? <Loading height={280} /> : (
              <Bar options={baseOptions({ plugins: { legend: { display: false } } })} data={{
                labels,
                datasets: [{ label: 'Glucose', data: rows.map((r) => r.blood_glucose), borderRadius: 5,
                  backgroundColor: rows.map((r) => (r.blood_glucose >= 300 ? '#ef4444' : r.blood_glucose >= 250 ? '#f97316' : r.blood_glucose > 180 ? '#f59e0b' : '#10b981')) }],
              }} />
            )}
          </div>
        </Card>
      </div>

      <div className="grid g-2">
        <Card title="Mood, sleep and activity" sub="Mood 1–5 · sleep hours · activity minutes / 10">
          <div style={{ height: 230 }}>
            {!tl.loading && (
              <Line options={baseOptions()} data={{
                labels,
                datasets: [
                  { label: 'Mood', data: rows.map((r) => r.mood), borderColor: '#ec4899', tension: .35, pointRadius: 2 },
                  { label: 'Sleep (h)', data: rows.map((r) => r.sleep_hours), borderColor: '#22d3ee', tension: .35, pointRadius: 2 },
                  { label: 'Activity /10', data: rows.map((r) => r.activity_minutes / 10), borderColor: '#10b981', tension: .35, pointRadius: 2 },
                ],
              }} />
            )}
          </div>
        </Card>
        <Card title="AI observations" sub="Evidence-based findings from MedInsightAgent (10-point dashboard)">
          {!d ? <Loading /> : (
            <div className="stack" style={{ gap: '.5rem' }}>
              {d['8_ai_observations'].map((o) => <div key={o} className="feed-item"><Sparkles size={15} color="#c4b5fd" style={{ flexShrink: 0, marginTop: 3 }} /><span className="muted">{o}</span></div>)}
              <div className="dim" style={{ fontSize: '.72rem', fontWeight: 700, textTransform: 'uppercase', marginTop: '.5rem' }}>Suggested review topics</div>
              <ul className="md" style={{ paddingLeft: '1.1rem' }}>{d['9_suggested_clinical_topics'].map((t) => <li key={t}>{t}</li>)}</ul>
            </div>
          )}
        </Card>
      </div>

      <div className="grid g-2">
        <AiBriefing />
        <Proposals />
      </div>

      <Card title="Daily vitals log" sub={`${rows.length} days · orange = warning, red = danger`}>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Day</th><th>Date</th><th>Phase</th><th>BP</th><th>HR</th><th>Glucose</th><th>Weight</th><th>Sleep</th><th>Meds</th><th>Social</th><th>Mood</th><th>Symptoms</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.day}>
                  <td style={{ color: 'var(--text)', fontWeight: 600 }}>{r.day}</td>
                  <td>{r.date}</td>
                  <td><Badge tone={{ stable: 'green', deteriorating: 'amber', dangerous: 'orange', intervention: 'red' }[r.phase]}>{r.phase}</Badge></td>
                  <td className={r.bp_systolic >= 160 ? 'c-crit' : r.bp_systolic >= 150 ? 'c-warn' : ''}>{r.bp_systolic}/{r.bp_diastolic}</td>
                  <td>{r.heart_rate}</td>
                  <td className={r.blood_glucose >= 300 ? 'c-crit' : r.blood_glucose >= 250 ? 'c-warn' : ''}>{r.blood_glucose}</td>
                  <td>{r.weight}</td>
                  <td>{r.sleep_hours}h</td>
                  <td className={r.medication_taken ? 'c-ok' : 'c-crit'}>{r.medication_taken ? 'Taken' : 'Missed'}</td>
                  <td className={r.social_interaction ? 'c-ok' : 'c-warn'}>{r.social_interaction ? 'Yes' : 'Isolated'}</td>
                  <td>{'★'.repeat(r.mood)}<span className="dim">{'★'.repeat(5 - r.mood)}</span></td>
                  <td style={{ whiteSpace: 'normal', minWidth: 160 }}>{r.symptoms?.join(', ') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Latest doctor report" icon={<FileText size={17} color="#93b4ff" />} sub="Generated by python main.py into reports/"
        actions={<button className="btn btn-ghost btn-sm" onClick={() => setShowReport((s) => !s)}>{showReport ? 'Hide' : 'Show'} report</button>}>
        <ErrorBox error={report.error} />
        {showReport && (report.data ? <Markdown text={report.data.report_markdown} /> : <Loading />)}
      </Card>
    </>
  )
}
