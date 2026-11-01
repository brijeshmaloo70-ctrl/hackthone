import { useEffect, useRef, useState } from 'react'
import { ClipboardPlus, MessageCircleHeart, Mic, Send, Siren, Volume2 } from 'lucide-react'
import { api } from '../api'
import Markdown from '../components/Markdown'
import { PageHint, useToast } from '../components/feedback'
import { Badge, Card, ErrorBox, EscalationBadge } from '../components/ui'

const LANGS = [['hi', 'हिन्दी'], ['en', 'English'], ['mr', 'मराठी']]
const SPEECH_LANG = { hi: 'hi-IN', en: 'en-IN', mr: 'mr-IN' }
const CHIPS = {
  hi: ['नमस्ते आशा', 'मुझे चक्कर आ रहा है', 'आज दवाई लेना भूल गया', 'मैं अकेला महसूस कर रहा हूँ'],
  en: ['Good morning Asha', 'I feel dizzy today', 'I forgot my medicine', 'When is my doctor visit?'],
  mr: ['नमस्कार आशा', 'मला चक्कर येत आहे', 'आज औषध घ्यायला विसरलो', 'मला एकटे वाटते'],
}
const GREETING = {
  hi: 'नमस्ते रमेश जी! 🙏 मैं आशा हूँ, आपकी स्वास्थ्य साथी। आज आप कैसा महसूस कर रहे हैं?',
  en: 'Namaste Ramesh-ji! 🙏 I am Asha, your health companion. How are you feeling today?',
  mr: 'नमस्कार रमेश जी! 🙏 मी आशा, आपली आरोग्य साथी. आज आपली तब्येत कशी आहे?',
}
const ALERT_TONE = ['gray', 'amber', 'orange', 'red']

function speak(text, lang) {
  if (!('speechSynthesis' in window)) return
  const u = new SpeechSynthesisUtterance(text.replace(/[*#<>/]|br/g, ' '))
  u.lang = SPEECH_LANG[lang]
  u.rate = 0.92
  window.speechSynthesis.cancel()
  window.speechSynthesis.speak(u)
}

function Chat() {
  const [lang, setLang] = useState('hi')
  const [msgs, setMsgs] = useState([{ role: 'bot', text: GREETING.hi }])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [listening, setListening] = useState(false)
  const [err, setErr] = useState(null)
  const logRef = useRef(null)
  const toast = useToast()
  const Recognition = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)

  useEffect(() => { logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' }) }, [msgs, sending])

  const switchLang = (l) => { setLang(l); setMsgs((m) => [...m, { role: 'bot', text: GREETING[l] }]) }

  const send = async (text) => {
    const t = (text ?? input).trim()
    if (!t || sending) return
    setInput('')
    setMsgs((m) => [...m, { role: 'user', text: t }])
    setSending(true)
    try {
      const r = await api.chat(t, lang)
      setMsgs((m) => [...m, { role: 'bot', text: r.reply, meta: r }])
      setErr(null)
      if (r.alert_level >= 2) toast(r.alert_level === 3 ? 'Emergency alert sent to Suresh and Dr. Sharma.' : 'Suresh has been asked to check on you.', r.alert_level === 3 ? 'error' : 'info')
    } catch (e) {
      setErr(e.message)
    } finally {
      setSending(false)
    }
  }

  const listen = () => {
    if (!Recognition) return
    const rec = new Recognition()
    rec.lang = SPEECH_LANG[lang]
    rec.onresult = (e) => send(e.results[0][0].transcript)
    rec.onend = () => setListening(false)
    setListening(true)
    rec.start()
  }

  return (
    <Card title="Talk to Asha" icon={<MessageCircleHeart size={17} color="#93b4ff" />} sub="Replies come from Gemini when available, otherwise from the built-in multilingual triage engine"
      actions={<div className="seg" role="tablist" aria-label="Language">{LANGS.map(([k, l]) => <button key={k} role="tab" aria-selected={lang === k} className={lang === k ? 'on' : ''} onClick={() => switchLang(k)}>{l}</button>)}</div>}>
      <div className="chat">
        <div className="chat-log" ref={logRef} aria-live="polite">
          {msgs.map((m, i) => (
            <div key={i} className={`msg ${m.role} fade-in`}>
              {m.role === 'bot' ? <Markdown text={m.text} /> : m.text}
              {m.role === 'bot' && (
                <div className="msg-meta">
                  {m.meta && (m.meta.llm_used ? <Badge tone="green">Gemini · {m.meta.model}</Badge> : <Badge tone="gray" >Fallback engine</Badge>)}
                  {m.meta?.alert_level > 0 && <Badge tone={ALERT_TONE[m.meta.alert_level]} dot>Alert level {m.meta.alert_level}</Badge>}
                  {m.meta?.caregiver_alert && <span className="dim" style={{ fontSize: '.72rem' }}>{m.meta.caregiver_alert}</span>}
                  <button className="btn btn-ghost btn-sm" style={{ padding: '.2rem .5rem' }} onClick={() => speak(m.text, lang)} aria-label="Read aloud"><Volume2 size={13} /></button>
                </div>
              )}
            </div>
          ))}
          {sending && <div className="msg bot"><span className="row"><span className="spinner" /> Asha is typing…</span></div>}
        </div>
        <ErrorBox error={err} />
        <div className="chips">{CHIPS[lang].map((c) => <button key={c} className="chip" onClick={() => send(c)}>{c}</button>)}</div>
        <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send() }}>
          <label className="sr-only" htmlFor="chat-in">Message</label>
          <input id="chat-in" className="input" value={input} onChange={(e) => setInput(e.target.value)} placeholder={lang === 'en' ? 'Type a message…' : 'संदेश लिखें…'} />
          {Recognition && <button type="button" className="btn btn-ghost" onClick={listen} aria-label="Speak" disabled={listening}><Mic size={16} color={listening ? 'var(--red)' : undefined} /></button>}
          <button className="btn btn-primary" disabled={sending || !input.trim()}><Send size={16} /> Send</button>
        </form>
      </div>
    </Card>
  )
}

function Checkin() {
  const [f, setF] = useState({ bp_systolic: 145, bp_diastolic: 90, blood_glucose: 190, heart_rate: 78, medication_taken: true, mood: 'calm', symptoms: '' })
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  const toast = useToast()
  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const payload = { ...f, symptoms: f.symptoms.split(',').map((s) => s.trim()).filter(Boolean) }
      ;['bp_systolic', 'bp_diastolic', 'blood_glucose', 'heart_rate'].forEach((k) => { payload[k] = Number(payload[k]) })
      const r = await api.checkin(payload)
      setRes(r); setErr(null)
      const lvl = r.risk_analysis.risk_level
      toast(lvl === 'Normal' ? 'Check-in saved. Everything looks fine today.' : `Check-in saved: ${lvl}. Your family and doctor were informed.`, lvl === 'Normal' ? 'success' : 'info')
    } catch (e2) { setErr(e2.message) } finally { setBusy(false) }
  }
  const ra = res?.risk_analysis
  const tone = { Normal: 'green', 'Low Concern': 'amber', 'Moderate Concern': 'orange', 'High Concern': 'red', Emergency: 'red' }

  return (
    <Card title="Daily check-in" icon={<ClipboardPlus size={17} color="#6ee7b7" />} sub="Saved to memory. RiskAnalysisAgent triages it and alerts family and doctor if needed.">
      <form onSubmit={submit} className="stack" style={{ gap: '.8rem' }}>
        <div className="grid g-2" style={{ gap: '.7rem' }}>
          {[['bp_systolic', 'Systolic BP'], ['bp_diastolic', 'Diastolic BP'], ['blood_glucose', 'Glucose (mg/dL)'], ['heart_rate', 'Heart rate']].map(([k, l]) => (
            <div className="field" key={k}><label htmlFor={k}>{l}</label><input id={k} className="input" type="number" value={f[k]} onChange={set(k)} required /></div>
          ))}
          <div className="field"><label htmlFor="mood">Mood</label>
            <select id="mood" className="select" value={f.mood} onChange={set('mood')}>{['happy', 'calm', 'tired', 'dizzy'].map((m) => <option key={m}>{m}</option>)}</select>
          </div>
          <div className="field"><label htmlFor="sym">Symptoms (comma separated)</label><input id="sym" className="input" value={f.symptoms} onChange={set('symptoms')} placeholder="e.g. headache, chest pain" /></div>
        </div>
        <label className="row" style={{ fontSize: '.85rem' }}><input type="checkbox" checked={f.medication_taken} onChange={set('medication_taken')} /> I took my morning medicines</label>
        <button className="btn btn-primary" disabled={busy}>{busy ? <span className="spinner" /> : null} Submit check-in</button>
      </form>
      <ErrorBox error={err} />
      {ra && (
        <div className="feed-item fade-in" style={{ flexDirection: 'column', marginTop: '1rem' }}>
          <div className="row between wrap"><Badge tone={tone[ra.risk_level] || 'gray'} dot>{ra.risk_level}</Badge><EscalationBadge level={res.current_escalation} /></div>
          <div className="muted" style={{ fontSize: '.8rem' }}>{ra.reasons.join(' ')}</div>
          <div style={{ fontSize: '.8rem' }}><strong>Next step:</strong> <span className="muted">{ra.recommended_action}</span></div>
        </div>
      )}
    </Card>
  )
}

function Sos() {
  const [state, setState] = useState(null)
  const [busy, setBusy] = useState(false)
  const toast = useToast()
  const trigger = async () => {
    if (!window.confirm('Send an emergency alert to your son and doctor?')) return
    setBusy(true)
    try {
      const r = await api.emergency()
      setState(r)
      toast('Help is on the way. Suresh and Dr. Sharma have been alerted.', 'error')
    } catch (e) { setState({ error: e.message }) } finally { setBusy(false) }
  }
  return (
    <Card title="Emergency" icon={<Siren size={17} color="#fca5a5" />} sub="One tap alerts Suresh and Dr. Sharma, and raises escalation to Level 3">
      <button className="btn btn-danger btn-lg" style={{ width: '100%', padding: '1.2rem' }} onClick={trigger} disabled={busy}>
        {busy ? <span className="spinner" /> : <Siren size={20} />} SOS: I need help
      </button>
      {state?.error && <ErrorBox error={state.error} />}
      {state?.status && <div className="feed-item fade-in" style={{ marginTop: '.8rem' }}><span className="muted" style={{ fontSize: '.82rem' }}>✅ Alert sent to {state.dispatched_to.join(' and ')}. Escalation is now Level {state.escalation_level}.</span></div>}
    </Card>
  )
}

export default function Patient() {
  return (
    <>
      <PageHint id="patient" title="Talking to Asha" steps={[
        'Choose your language at the top of the chat: हिन्दी, English or मराठी.',
        'Type, tap a suggestion, or press the microphone to speak. The speaker icon reads a reply aloud.',
        'If you mention chest pain or dizziness, Asha tells your son and doctor automatically.',
        'Fill in today’s check-in on the right. Press the red SOS button only in an emergency.',
      ]} />
      <div className="grid g-main">
        <Chat />
        <div className="stack"><Sos /><Checkin /></div>
      </div>
    </>
  )
}
