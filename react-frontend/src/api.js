// Thin client for the Python backend (server.py). All paths are relative so they
// work through the Vite dev proxy and when server.py serves the built app.

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const text = await res.text()
  let data
  try {
    data = text ? JSON.parse(text) : {}
  } catch {
    throw new Error(`Invalid JSON from ${path} (HTTP ${res.status})`)
  }
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status} on ${path}`)
  return data
}

const get = (path) => request(path)
// Every successful write tells the layout to refresh its badges (alert count, escalation)
const post = async (path, body) => {
  const data = await request(path, { method: 'POST', body: JSON.stringify(body ?? {}) })
  window.dispatchEvent(new Event('caresync:changed'))
  return data
}

export const api = {
  status: () => get('/api/status'),
  llmStatus: (test = false) => get(`/api/llm/status${test ? '?test=1' : ''}`),
  timeline: () => get('/api/timeline'),
  report: () => get('/api/report'),
  carePlan: () => get('/api/care-plan'),
  clinicianDashboard: () => get('/api/clinician/dashboard'),
  aiBriefing: () => get('/api/clinician/ai-briefing'),
  caregiverDashboard: () => get('/api/caregiver/dashboard'),
  schedule: () => get('/api/schedule'),
  whatsapp: (limit = 50) => get(`/api/whatsapp/messages?limit=${limit}`),
  events: (limit = 100) => get(`/api/events?limit=${limit}`),

  chat: (message, language, day) => post('/api/chat', { message, language, day }),
  checkin: (payload) => post('/api/patient/checkin', payload),
  emergency: (day) => post('/api/emergency', { day, trigger_source: 'Patient SOS Button' }),
  acknowledge: (alert_id, action_taken, notes) => post('/api/caregiver/acknowledge', { alert_id, action_taken, notes }),
  reviewProposal: (proposal_id, approve, notes) => post('/api/care-plan/review', { proposal_id, approve, notes }),
  runDay: (day, data) => post('/api/schedule/run-day', { day, data }),
  resetLive: () => post('/api/demo/reset', {}),

  /** Replay a range of timeline days through the live scheduler (e.g. 21–28 = the dangerous phase). */
  async runDays(from, to) {
    const tl = await get('/api/timeline')
    const days = tl.filter((d) => d.day >= from && d.day <= to)
    if (!days.length) throw new Error('No timeline data. Run "python main.py" first.')
    for (const d of days) await post('/api/schedule/run-day', { day: d.day, data: d })
    return days.length
  },
}
