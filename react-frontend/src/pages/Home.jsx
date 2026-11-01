import { Link } from 'react-router-dom'
import {
  ArrowRight, Bell, BrainCircuit, Database, Droplet, FileText, HeartHandshake, HeartPulse,
  Languages, MessageCircleHeart, Pill, Radio, ShieldAlert, Stethoscope, Users,
} from 'lucide-react'
import { Brand, LlmPill } from '../components/Layout'
import { Badge, EscalationLadder } from '../components/ui'

const AGENTS = [
  { icon: MessageCircleHeart, color: '#5b8cff', name: 'Asha', role: 'Patient Agent', text: 'Proactive daily check-ins over voice or WhatsApp in Hindi, Marathi and English. Logs vitals, meds and mood into long-term memory.' },
  { icon: ShieldAlert, color: '#f97316', name: 'RiskAnalysisAgent', role: 'Triage', text: 'Rule-based clinical triage that never depends on the LLM for emergencies. Compares each reading against a 7-day baseline.' },
  { icon: Users, color: '#ec4899', name: 'SocialWellbeingAgent', role: 'Healthy ageing', text: 'Spots isolation after 3+ days without contact, nudges the patient and asks family to reconnect.' },
  { icon: HeartHandshake, color: '#10b981', name: 'ConnectAgent', role: 'Caregiver Agent', text: 'Keeps the son in the loop with urgency-tiered WhatsApp and SMS alerts and weekly summaries.' },
  { icon: Stethoscope, color: '#8b5cf6', name: 'MedInsightAgent', role: 'Clinician Agent', text: 'Builds the 10-point doctor briefing, an AI-written pre-visit summary, and gates care-plan changes behind approval.' },
]

const PHASES = [
  { c: 'var(--green)', t: 'Days 1–10 · Stable', d: 'BP ~140/88, glucose ~175, 95% adherence. Weekly summary to family on day 7.' },
  { c: 'var(--amber)', t: 'Days 11–20 · Drifting', d: 'BP and glucose creep up and doses get missed. Risk agent flags the 7-day upward trend.' },
  { c: 'var(--orange)', t: 'Days 21–27 · Dangerous', d: 'BP 160+, glucose 280+. Escalation to Level 2 and isolation detected. Doctor and son alerted.' },
  { c: 'var(--red)', t: 'Days 28–30 · Intervention', d: 'Level 3 critical voice call, then family visits and vitals settle. Pre-visit report generated.' },
]

export default function Home() {
  return (
    <div className="landing">
      <header className="l-nav">
        <Brand />
        <nav aria-label="Sections">
          <a href="#agents">Agents</a>
          <a href="#flow">30-day flow</a>
          <a href="#stack">How it works</a>
        </nav>
        <div className="row">
          <LlmPill />
          <Link to="/agents" className="btn btn-primary btn-sm">Open app <ArrowRight size={15} /></Link>
        </div>
      </header>

      <div className="l-wrap">
        <section className="hero">
          <div>
            <span className="eyebrow">Track 4 · HEALTH-01 · Codekshetra</span>
            <h1>Chronic care that <span className="grad-text">reaches out first.</span></h1>
            <p className="lead">
              Five coordinating AI agents watch over an elderly patient between doctor visits.
              They catch a deteriorating trend early, keep the family informed, and brief the
              doctor before the next appointment. All of them share one evolving care plan.
            </p>
            <div className="hero-cta">
              <Link to="/agents" className="btn btn-primary btn-lg">Run the agents live <ArrowRight size={17} /></Link>
              <Link to="/patient" className="btn btn-ghost btn-lg">Talk to Asha</Link>
            </div>
            <div className="row wrap" style={{ marginTop: '2rem', gap: '1.75rem' }}>
              {[['5', 'AI agents'], ['30', 'day timeline'], ['3', 'languages'], ['18', 'REST APIs']].map(([v, l]) => (
                <div key={l}><div className="stat-big grad-text">{v}</div><div className="dim" style={{ fontSize: '.8rem' }}>{l}</div></div>
              ))}
            </div>
          </div>

          <div className="hero-card" aria-hidden="true">
            <div className="card">
              <div className="row between" style={{ marginBottom: '1rem' }}>
                <div className="row"><span className="dot pulse" style={{ color: 'var(--green)' }} /><span className="muted" style={{ fontSize: '.8rem' }}>Ramesh Kumar · Day 28</span></div>
                <Badge tone="red" dot pulse>Level 3</Badge>
              </div>
              <div className="grid g-2" style={{ gap: '.7rem' }}>
                {[[HeartPulse, '#ef4444', '170/105', 'BP mmHg'], [Droplet, '#f59e0b', '322', 'Glucose mg/dL'], [Pill, '#8b5cf6', '70%', 'Adherence'], [Users, '#ec4899', '5 days', 'Isolated']].map(([I, c, v, l]) => (
                  <div key={l} style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 12, padding: '.75rem' }}>
                    <I size={16} color={c} />
                    <div style={{ fontWeight: 800, fontSize: '1.2rem', marginTop: '.25rem' }}>{v}</div>
                    <div className="dim" style={{ fontSize: '.7rem' }}>{l}</div>
                  </div>
                ))}
              </div>
              <div style={{ margin: '1rem 0 .4rem' }}><EscalationLadder level={3} /></div>
              <div className="feed" style={{ marginTop: '.8rem' }}>
                <div className="feed-item"><Bell size={15} color="var(--red)" /><div><strong>ConnectAgent → Suresh</strong><div className="meta">WhatsApp + SMS · BP 170/105, please check on Papa</div></div></div>
                <div className="feed-item"><Stethoscope size={15} color="var(--violet)" /><div><strong>MedInsightAgent → Dr. Sharma</strong><div className="meta">Escalation brief · urgent review within 2h</div></div></div>
              </div>
            </div>
          </div>
        </section>

        <section className="section" style={{ paddingTop: '1rem' }} aria-labelledby="who">
          <div className="section-head" style={{ marginBottom: '1.5rem' }}>
            <span className="eyebrow">Start here</span>
            <h2 id="who">Who are you?</h2>
          </div>
          <div className="grid g-4">
            {[
              ['/patient', MessageCircleHeart, '#5b8cff', 'I’m the patient', 'Talk to Asha, log today’s BP and sugar, call for help.'],
              ['/caregiver', HeartHandshake, '#10b981', 'I’m family', 'See alerts about Papa and log what you did.'],
              ['/clinician', Stethoscope, '#8b5cf6', 'I’m the doctor', '30-day trends, AI briefing, approve care-plan changes.'],
              ['/agents', Radio, '#f59e0b', 'I’m judging the demo', 'Run the 30 days live and watch the agents coordinate.'],
            ].map(([to, I, c, t, d]) => (
              <Link key={to} to={to} className="card feature lift" style={{ display: 'block' }}>
                <div className="feature-icon" style={{ background: `${c}1f`, border: `1px solid ${c}40` }}><I size={21} color={c} /></div>
                <h3 className="row between">{t} <ArrowRight size={16} color="var(--dim)" /></h3>
                <p>{d}</p>
              </Link>
            ))}
          </div>
        </section>

        <section className="section" id="agents">
          <div className="section-head">
            <span className="eyebrow">The agent network</span>
            <h2>Five agents, one shared care plan</h2>
            <p className="muted">They coordinate over a pub/sub event bus and read from one SQLite memory of the patient.</p>
          </div>
          <div className="grid g-3">
            {AGENTS.map(({ icon: I, color, name, role, text }) => (
              <article key={name} className="card feature lift">
                <div className="feature-icon" style={{ background: `${color}1f`, border: `1px solid ${color}40` }}><I size={21} color={color} /></div>
                <div className="row between"><h3>{name}</h3><Badge tone="gray">{role}</Badge></div>
                <p>{text}</p>
              </article>
            ))}
            <article className="card feature lift" style={{ background: 'linear-gradient(135deg, rgba(91,140,255,.12), rgba(139,92,246,.08))' }}>
              <div className="feature-icon" style={{ background: 'rgba(255,255,255,.06)' }}><Radio size={21} color="#93b4ff" /></div>
              <h3>Event bus coordination</h3>
              <p className="mono" style={{ fontSize: '.75rem', lineHeight: 1.9 }}>
                VITALS_ALERT → Risk, Clinician<br />MEDICATION_MISSED → Caregiver<br />RISK_ALERT_ISSUED → Caregiver, Clinician<br />SOCIAL_ISOLATION → Caregiver
              </p>
            </article>
          </div>
        </section>

        <section className="section" id="flow">
          <div className="section-head">
            <span className="eyebrow">Demo storyline</span>
            <h2>A 30-day deterioration, caught in time</h2>
          </div>
          <div className="grid g-4">
            {PHASES.map((p) => (
              <div key={p.t} className="card lift"><div className="phase" style={{ borderColor: p.c }}><h3 style={{ fontSize: '.95rem', marginBottom: '.4rem' }}>{p.t}</h3><p className="muted" style={{ fontSize: '.85rem' }}>{p.d}</p></div></div>
            ))}
          </div>
        </section>

        <section className="section" id="stack">
          <div className="section-head">
            <span className="eyebrow">Under the hood</span>
            <h2>Built so it works with or without the LLM</h2>
          </div>
          <div className="grid g-3">
            {[
              [BrainCircuit, '#5b8cff', 'Gemini via REST', 'Model fallback chain with timeouts and live diagnostics at /api/llm/status. Safety triage stays rule-based.'],
              [Database, '#10b981', 'Longitudinal memory', 'SQLite stores vitals, check-ins, meds, social logs, events and caregiver actions across the whole timeline.'],
              [Languages, '#ec4899', 'Multilingual', 'Real Devanagari Hindi and Marathi templates, plus Gemini replies in the patient’s language.'],
              [FileText, '#8b5cf6', 'Doctor reports', 'Markdown pre-visit summary with a vitals table, adherence, isolation days and recommendations.'],
              [ShieldAlert, '#f97316', 'Safe escalation', 'Levels 0 to 3, deduplicated alerts, and medication changes that need clinician approval.'],
              [Radio, '#22d3ee', 'Proactive scheduler', 'Four daily jobs (08:00, 09:00, 13:00, 19:00) run the agents with no user prompt needed.'],
            ].map(([I, c, t, d]) => (
              <div key={t} className="card feature lift">
                <div className="feature-icon" style={{ background: `${c}1f`, border: `1px solid ${c}40` }}><I size={21} color={c} /></div>
                <h3>{t}</h3><p>{d}</p>
              </div>
            ))}
          </div>
          <div style={{ textAlign: 'center', marginTop: '3rem' }}>
            <Link to="/agents" className="btn btn-primary btn-lg">Open the Agent Control Room <ArrowRight size={17} /></Link>
          </div>
        </section>
      </div>
      <footer className="footer">CareSync AI · Proactive agents for chronic care and healthy ageing · Not a medical device: demo data only</footer>
    </div>
  )
}
