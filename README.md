# CareSync AI: Proactive Multi-Agent Chronic Care

> Hackathon Track 4: Healthcare & Social Impact, HEALTH-01
> *Proactive Agents for Chronic Care and Healthy Ageing*

Elderly patients with hypertension and diabetes get worse in the gaps between doctor visits: missed medicines, unnoticed warning signs, loneliness. CareSync AI puts five coordinating agents around one patient (Ramesh Kumar, 78). They reach out first, catch a deteriorating trend, keep the family informed, and brief the doctor before the next visit. All of them share one evolving care plan.

| Agent | Role |
|---|---|
| **Asha** (Patient Agent) | Proactive check-ins in Hindi, Marathi and English. Logs vitals, meds, mood and social contact to memory. Live chat. |
| **RiskAnalysisAgent** | Rule-based clinical triage (Normal → Emergency) with 7-day baseline comparison. **Never relies on the LLM for safety decisions.** |
| **SocialWellbeingAgent** | Detects isolation (3+ days without contact), nudges the patient, asks family to reconnect. |
| **ConnectAgent** (Caregiver Agent) | Urgency-tiered WhatsApp/SMS alerts and weekly summaries to the son. Alert acknowledgement. |
| **MedInsightAgent** (Clinician Agent) | 10-point doctor dashboard, LLM-written pre-visit briefing, care-plan approval gate. |

---

## Quick start

Requirements: Python 3.9+, Node 18+ (only to build the React frontend).

```bash
# 1. Backend dependencies
pip install -r requirements.txt

# 2. Configure the LLM (optional, everything works without it)
cp .env.example .env          # then set GEMINI_API_KEY=...

# 3. Seed the database + timeline + doctor report (30-day simulation)
python main.py

# 4. Build the React frontend once
cd react-frontend
npm install
npm run build
cd ..

# 5. Start the server: serves the React app AND the REST API
python server.py              # → http://localhost:8000
```

**Frontend development (hot reload):** run `python server.py` in one terminal and `cd react-frontend && npm run dev` in another, then open http://localhost:5173. Vite proxies every `/api/*` request to `:8000`.

> The React app in `react-frontend/` is the only frontend. If it hasn't been built (`react-frontend/dist/` missing), `server.py` still serves the API and shows a "build the frontend" page at `/`.

---

## The React app

| Route | What it does |
|---|---|
| `/` | Landing page: problem, agents, 30-day storyline, architecture |
| `/agents` | **Agent Control Room.** Step through the 30-day timeline one day at a time or auto-play. Each day runs the proactive scheduler, and you watch the event bus, the agents' outbound WhatsApp messages and the escalation level update live. Includes a Gemini live-test button. |
| `/clinician` | KPIs, BP/glucose/mood charts with phase filter, AI observations, **Gemini pre-visit briefing**, care-plan proposal approve/reject, full vitals log, latest doctor report |
| `/caregiver` | Status for the son, alerts from ConnectAgent with acknowledgement and action logging, WhatsApp thread |
| `/patient` | Chat with Asha (हिन्दी / English / मराठी, voice input and read-aloud in Chrome/Edge), daily check-in form triaged by RiskAnalysisAgent, SOS button |

The top bar shows the LLM state on every page: `Gemini · <model>`, `Template mode (no key)`, `Gemini errors` or `Backend offline`. Every portal opens with a short "how to use this page" guide (dismiss it with **Got it**, reopen it from the link that replaces it). The red number on **Caregiver** in the sidebar is the count of alerts still waiting for a response. A red banner appears if the backend is unreachable.

### How the caregiver acknowledges an alert

1. Open **Caregiver**. Alerts that still need a response are under **Needs action**, with urgent ones first.
2. Under an alert, tap what you did: **I called Papa**, **I visited him**, **Reminded him about medicines**, **Booked a doctor visit**. It saves immediately (`POST /api/caregiver/acknowledge`).
3. For anything else, tap **Something else…**, type the action, optionally add a note for the doctor, then **Log action**.
4. The alert moves to **Done** with your action shown on it. It also appears in "What you've done" and as a `CAREGIVER_ACTION_RECORDED` event in the Agent Control Room.
5. **Mark N non-urgent as seen** clears informational alerts in one go. Urgent ones stay open.

Alerts are stored in SQLite (`caregiver_alerts` table), so they survive server restarts. After `python main.py` the hub holds the full 30-day history (about 53 alerts, 14 urgent). Alerts come from ConnectAgent (risk, medication, isolation, escalation), SocialWellbeingAgent nudges, Asha chat red flags and the SOS button.

**Suggested demo:** open `/agents` → click **Jump to day 21** → **Auto-play**. Escalation goes to Level 2, then Level 3 on day 28, and alerts reach the caregiver and doctor. Then check `/caregiver` (acknowledge an alert), `/clinician` (generate the AI briefing, approve the Amlodipine proposal) and `/patient` (type "I have chest pain").

---

## How the API works

`server.py` is a dependency-free Python `ThreadingHTTPServer` on port 8000 that listens on both IPv4 and IPv6. One process holds a single agent network (one `EventBus`, one `CarePlan`, one `PatientMemory` on `data/patient_memory.db`) and exposes it as JSON over REST. It also serves the React app with SPA routing. CORS is open (`*`).

- **Thread safety:** all agent and DB access goes through one lock, because the agents and the single SQLite connection aren't thread-safe and the UI polls several endpoints at once. Gemini calls run outside the lock so a slow LLM reply doesn't freeze the dashboards.
- **Errors are always JSON** `{"error": "...", "status": N}`: `400` bad or missing input, `404` unknown endpoint, alert or proposal, `405` wrong method, `409` proposal already reviewed, `413` body too large, `500` unexpected error (logged with a traceback).
- **On startup** the live escalation level is restored from the latest stored reading (e.g. Level 2 after the 30-day run) instead of always starting at 0.

**Check every endpoint:** with the server running, `python scripts/api_check.py` runs 48 checks covering happy paths, bad input and state changes such as SOS → alert → acknowledge. Add `--no-llm` to skip Gemini calls. It resets the live session at the end. Last run: **48/48 passed**.

### Two entry points, one database

| | `python main.py` | `python server.py` |
|---|---|---|
| Purpose | Batch 30-day simulation in the terminal | Interactive web app + REST API |
| Writes | **Resets** and reseeds `data/patient_memory.db`, writes `data/timeline_enriched.json` and `reports/doctor_report_*.md` | Appends live check-ins to the same DB |
| Agent state | Lives for the run | Event bus and mock WhatsApp log live in server memory and reset on restart. **Caregiver alerts and actions persist in SQLite.** Escalation is restored from the latest stored reading. |

Run `main.py` before the server so `/api/timeline`, `/api/report` and the charts have data.

### Endpoints

All endpoints were verified to return HTTP 200 against a running server.

| Method | Endpoint | What it does | Real or mock |
|---|---|---|---|
| GET | `/api/status` | Agent registry, profiles, escalation level, `gemini_active` | Real |
| GET | `/api/llm/status` | LLM config, call counters and last error. Add `?test=1` to fire a live Gemini request. | Real |
| GET | `/api/timeline` | 30-day timeline from `data/timeline_enriched.json` | Simulated data |
| GET | `/api/report` | Latest `reports/doctor_report_*.md` | Real (generated) |
| GET | `/api/clinician/dashboard` | MedInsightAgent 10-point structured briefing from SQLite | Real |
| GET | `/api/clinician/ai-briefing` | Gemini-written pre-visit narrative from that dashboard. Falls back to rule-based observations without a key. | **LLM** |
| GET | `/api/caregiver/dashboard` | Privacy-scoped caregiver view: persistent alerts (`notifications`), `unacknowledged_count`, `latest_vitals`, 7-day adherence and social contact, logged actions | Real |
| GET | `/api/care-plan` | Shared care plan incl. proposals and audit events | Real |
| GET | `/api/schedule` | Scheduler jobs + execution history | Real |
| GET | `/api/events?limit=&type=` | Event bus history | Real |
| GET | `/api/whatsapp/messages?limit=` | Messages agents "sent" | **Mock** gateway |
| POST | `/api/chat` `{message, language: hi\|en\|mr, day}` | Asha reply. Gemini with patient memory context, else multilingual fallback. Keyword triage fires emergency/risk events. Response includes `llm_used`, `model`, `llm_error`. | **LLM** + rules |
| POST | `/api/patient/checkin` `{bp_systolic, bp_diastolic, blood_glucose, heart_rate, medication_taken, mood, symptoms[]}` | Saves to memory, RiskAnalysisAgent triages, **dispatches alerts and escalates** | Real |
| POST | `/api/schedule/run-day` `{day, data}` | Runs the 4 daily jobs: 08:00 full Asha check-in → 09:00 meds → 13:00 social → 19:00 risk review | Real |
| POST | `/api/emergency` `{day}` | SOS: escalation → Level 3, WhatsApp to son and doctor | Real logic, mock delivery |
| POST | `/api/caregiver/acknowledge` `{alert_id, action_taken, notes?}` | Marks the alert done, logs the caregiver action, publishes `CAREGIVER_ACTION_RECORDED`. `400` if fields are missing, `404` for an unknown alert. | Real |
| POST | `/api/demo/reset` | Resets the live session: clears events and mock messages, rebuilds the agents, restores escalation from the latest reading. DB history is kept. | Real |
| POST | `/api/care-plan/review` `{proposal_id, approve, notes}` | Clinician approves or rejects a proposal | Real |
| POST | `/api/care-plan/propose` | Agent/doctor proposes a care-plan change | Real |
| POST | `/api/whatsapp/simulate-inbound` | Fake an inbound WhatsApp reply | Mock |

**What is mocked:** WhatsApp, SMS and voice calls (`api/mock_integrations.py`) only record messages in memory. No real message leaves the machine. Patient data is simulated (`simulation/patient_data.py`, seed 42).

### Agent coordination (event bus)

| Event | Published by | Handled by |
|---|---|---|
| `VITALS_ALERT` (BP ≥ 150 or glucose ≥ 250) | Asha | RiskAnalysisAgent, MedInsightAgent |
| `CHECKIN_COMPLETED` | Asha | RiskAnalysisAgent |
| `RISK_ALERT_ISSUED` | RiskAnalysisAgent (deduplicated per day/level) | ConnectAgent, MedInsightAgent |
| `MEDICATION_MISSED` | Asha / scheduler | ConnectAgent |
| `SOCIAL_ISOLATION_DETECTED`, `SOCIAL_INTERVENTION_TRIGGERED` | Asha, SocialWellbeingAgent | ConnectAgent |
| `ESCALATION_NEEDED`, `EMERGENCY_TRIGGERED` | MedInsightAgent, SOS, chat | ConnectAgent, MedInsightAgent |

Escalation levels: 0 Normal · 1 Watch · 2 Warning · 3 Critical.

---

## LLM (Gemini) status

**Is it working?** Yes. With the key in `.env` it was verified end to end on Nov 1, 2026: `/api/llm/status?test=1` → `ok`, `/api/chat` (English and Hindi) → `llm_used: true`, `/api/clinician/ai-briefing` → `llm_used: true`, model `gemini-flash-lite-latest`.

### Why it was not working before

The API key was not the problem. These were:

1. **Retired model.** `gemini-1.5-flash` was hardcoded in `agents/base_agent.py` and `server.py`. Google now returns **HTTP 404** for it, and also for `gemini-2.0-flash` and `gemini-2.5-flash` on new keys.
2. **Silent failure.** Every exception was swallowed (`except: pass`) and the template reply was returned, so the app looked fine but never used the LLM. `main.py` printed "Gemini detected" whenever *any* key string existed, without testing it.
3. **Wrong variable name in `.env.example`.** It said `GOOGLE_API_KEY`, but the code reads `GEMINI_API_KEY`.

### How it works now (`core/llm.py`)

- One shared client for all agents, the Asha chat engine and the server. It calls the Gemini REST API directly with the Python stdlib, so the deprecated `google-generativeai` SDK is no longer needed.
- **Model fallback chain**, tried in order: `gemini-flash-lite-latest` → `gemini-3.5-flash-lite` → `gemini-flash-latest`. The `-latest` aliases keep working when Google retires versions. It stops early on 400/401/403 (key problems).
- 20 s timeout per request. Failures are logged and exposed through `/api/llm/status` (`last_error`) and the `llm_error` field of chat/briefing responses.
- `main.py` now performs a real test call at startup and prints `✅ reachable`, `❌ failing — <reason>` or `no key`.

### Where the LLM is (and is not) used

| Feature | Uses Gemini? |
|---|---|
| Asha chat (`/api/chat`) | Yes, with stored patient memory (7-day BP trend, adherence, symptoms, escalation) in the prompt |
| Clinician AI briefing (`/api/clinician/ai-briefing`) | Yes |
| Risk triage, escalation, emergency detection | **No, by design.** Rule-based for safety. |
| Daily check-in messages, family alerts, weekly summaries, the 30-day `main.py` run | No. Curated multilingual templates (`nlp/language_handler.py`), fast and deterministic. |

### Configuration (`.env`)

```ini
GEMINI_API_KEY=your_key            # required for LLM mode; key name must be exactly this
GEMINI_MODEL=gemini-flash-lite-latest,gemini-flash-latest   # optional override (comma-separated)
GEMINI_TIMEOUT=20                  # optional, seconds
```

### Troubleshooting

Open `http://localhost:8000/api/llm/status?test=1`, or click **Run live test** in the Agent Control Room:

| You see | Meaning / fix |
|---|---|
| `configured: false` | `.env` missing, or the key isn't named `GEMINI_API_KEY`. Restart the server after editing `.env`. |
| `HTTP 400/403 API key not valid` | Create a new key at https://aistudio.google.com/app/apikey |
| `HTTP 404 ... no longer available` | Model retired. Set `GEMINI_MODEL` to a model listed by `GET https://generativelanguage.googleapis.com/v1beta/models` |
| `HTTP 429` / `503 high demand` | Quota or overload. The client automatically tries the next model, or wait and retry. |
| `TimeoutError` | Slow model or network. Raise `GEMINI_TIMEOUT` or pick a `-lite` model. |

---

## Bugs fixed in this revision

- LLM never called (retired model, silent errors, `.env.example` key name). See above.
- `POST /api/emergency` crashed: it called the non-existent `care_plan.update_escalation()`. It now uses `escalate()`.
- Live check-ins never alerted anyone: `RiskAnalysisAgent.evaluate_health_record()` only computes a result. Added `assess()` (evaluate + dispatch + escalate), used by `/api/patient/checkin`.
- Scheduler's 08:00 job only built a greeting string, so `run-day` never logged vitals or triggered other agents. It now runs Asha's full check-in pipeline. Mood strings (`"tired"`) are normalised to 1–5.
- Duplicate `RISK_ALERT_ISSUED` per reading, which sent the family two identical alerts. Now deduplicated.
- `main.py` appended another 30 days to the DB on every run (173 rows for 30 days), which skewed every average and adherence figure. It now resets the DB first.
- `main.py` never wrote `data/timeline_enriched.json`, so `/api/timeline` and the charts were empty.
- **Caregiver alerts were empty.** They lived only in server memory (gone on restart, never filled by `main.py`), and SOS and chat emergencies bypassed ConnectAgent. Alerts are now persisted, and every alert source goes through ConnectAgent.
- Acknowledging accepted any alert ID and returned success. Unknown IDs now return 404.
- Any exception (e.g. `"bp_systolic": "abc"`) dropped the connection with no response. Every route now returns JSON errors with proper status codes.
- Every request through `localhost` took about **2 s** on Windows (IPv4-only server, browser tries IPv6 first). With the dual-stack server it's about 5 ms.
- Approving a free-text care-plan proposal replaced the entire medication list (or activity goals) with a string. It's now recorded as an amendment.
- The server's care plan had no medications or goals, and always started at escalation 0 regardless of history.

---

## Project structure

```
codekshetra/
├── main.py                  # 30-day batch simulation → DB, timeline JSON, doctor report
├── server.py                # REST API + serves the built React app (react-frontend/dist)
├── core/
│   ├── llm.py               # Shared Gemini REST client (fallback chain, diagnostics)
│   ├── care_plan.py         # Shared evolving care plan + proposal/approval lifecycle
│   ├── memory.py            # SQLite longitudinal memory (vitals, check-ins, meds, social, events…)
│   ├── event_bus.py         # Synchronous pub/sub between agents
│   └── scheduler.py         # Proactive daily jobs (08:00 / 09:00 / 13:00 / 19:00)
├── agents/                  # base, patient (Asha), risk, social, caregiver, clinician
├── nlp/                     # conversational_ai.py (Asha chat), language_handler.py (hi/mr/en templates)
├── api/mock_integrations.py # Mock WhatsApp / SMS / voice
├── simulation/              # 30-day timeline generator + demo runner
├── dashboard/report_generator.py
├── config/settings.py       # Patient profile, thresholds, medication schedule
├── scripts/api_check.py     # 48-check smoke test of every endpoint (python scripts/api_check.py)
├── react-frontend/          # React 19 + Vite + React Router + Chart.js + lucide-react
│   └── src/{api.js, components/, pages/}
├── data/                    # Generated: patient_memory.db, timeline_enriched.json, app.log
└── reports/                 # Generated doctor pre-visit reports
```

## HEALTH-01 demo checklist

- [x] Patient agent initiates check-ins on its own schedule (`AutonomousScheduler`, voice on critical/low-mood days)
- [x] Simulated 30-day timeline where agents catch the deteriorating trend and escalate (Level 2 → Level 3)
- [x] Doctor-facing summary of everything between visits (10-point dashboard, Gemini briefing, markdown report)
- [x] Social wellbeing: isolation detected, patient nudged, family asked to reconnect
- [x] Agent-to-agent coordination over a shared event bus and one care plan
- [x] Multilingual: Hindi, Marathi, English (Devanagari)
- [x] Safe escalation: rule-based triage, deduplicated alerts, clinician approval for medication changes

*Demo only. Not a medical device. All patient data is synthetic.*
