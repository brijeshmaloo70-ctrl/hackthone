# 🏥 AI Proactive Chronic Care Management System

> **Hackathon Track 4: Healthcare & Social Impact — HEALTH-01**  
> *Proactive Agents for Chronic Care and Healthy Ageing*

---

## 🎯 Problem Statement

Elderly patients with chronic conditions like hypertension and diabetes often go weeks without proactive care monitoring between doctor visits. Family caregivers are out of the loop. Doctors see patients too infrequently to catch dangerous deteriorating trends early. This leads to preventable hospitalisations and crises.

## 💡 Our Solution

A **network of three coordinating AI agents** built around an elderly patient — all sharing one evolving care plan — that proactively manages chronic care 24/7:

| Agent | Role |
|-------|------|
| 🤖 **Asha (Patient Agent)** | Calls/messages the patient in Hindi/English, tracks medicines, vitals, mood, social connection |
| 👨‍👩‍👦 **ConnectAgent (Caregiver Agent)** | Keeps family in the loop with smart alerts and weekly summaries |
| 🩺 **MedInsightAgent (Clinician Agent)** | Monitors trends, prepares doctors before visits, escalates dangerous patterns |

All three share a **single evolving Care Plan** object — the single source of truth.

---

## 🏗️ Architecture

```
codekshetra/
├── main.py                     # Entry point — runs full 30-day simulation in terminal
├── server.py                   # Web server & REST API for interactive frontend
├── requirements.txt
├── .env.example
│
├── frontend/                   # Modern Web Application & Clinical Dashboard
│   ├── index.html              # Landing page (hero, agents, architecture, demo flow)
│   ├── dashboard.html          # Clinical Dashboard (30-day vitals, charts, player, chat)
│   ├── styles.css              # Landing page styling & design tokens
│   ├── dashboard.css           # Dashboard layout, metrics cards & dark theme
│   ├── main.js                 # Landing page interactions & counters
│   └── dashboard.js            # Chart.js charts, playback simulation engine & Asha AI chat
│
├── config/
│   └── settings.py             # Patient profile, thresholds, medication schedule
│
├── core/
│   ├── care_plan.py            # Shared CarePlan dataclass (singleton)
│   ├── memory.py               # SQLite-backed long-term patient memory
│   └── event_bus.py            # Pub/sub event bus for agent coordination
│
├── agents/
│   ├── base_agent.py           # BaseAgent with Gemini LLM + fallback
│   ├── patient_agent.py        # Patient check-ins, vitals, isolation detection
│   ├── caregiver_agent.py      # Family notifications, weekly summaries
│   └── clinician_agent.py      # Trend analysis, escalation, doctor briefings
│
├── simulation/
│   ├── patient_data.py         # Realistic 30-day timeline generator
│   └── demo_runner.py          # Orchestrates the 30-day demo
│
├── nlp/
│   └── language_handler.py     # Hindi (Devanagari) + English message templates
│
├── api/
│   └── mock_integrations.py    # Mock WhatsApp, Voice Call, SMS APIs
│
├── dashboard/
│   └── report_generator.py     # Doctor-facing HTML/markdown report
│
├── data/                       # Auto-created: SQLite DB + logs + enriched timeline
└── reports/                    # Auto-created: generated doctor pre-visit reports
```

---

## 🚀 Quick Start

### 1. Clone / Open the project
```bash
cd hackthone
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Set Gemini API Key for LLM responses
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```
> **Without a key:** The system runs in template mode with pre-written multilingual responses. All simulation logic and demo flow still works perfectly.

### 4. Run the 30-day simulation
```bash
python main.py
```

---

## 🎬 Demo Flow (30-Day Simulation)

The simulation runs through four phases, showing all four demo requirements:

### Phase 1: Stable (Days 1–10) ✅
- **Asha** conducts daily multilingual check-ins (Hindi + English)
- Vitals logged: BP ~140/90, glucose ~175 mg/dL
- 95% medication adherence
- Social interactions regular
- Weekly summary sent to Suresh (caregiver) on Day 7

### Phase 2: Gradual Deterioration (Days 11–20) 📈
- BP begins rising (140 → 155 mmHg)
- Glucose climbing (175 → 220 mg/dL)
- Medication adherence dropping
- **Clinician Agent** detects upward BP trend on Day 14
- Medication adherence alert fired on Day 19

### Phase 3: Dangerous Trend (Days 21–27) ⚠️
- **Day 22: ESCALATION TRIGGERED** — BP 165-175, glucose 280-310
  - Clinician Agent escalates to Level 2
  - Doctor alerted via WhatsApp
  - Caregiver alerted urgently
- **Day 24: ISOLATION DETECTED** — 5 consecutive days without social contact
  - Patient Agent nudges patient to reconnect
  - Caregiver Agent sends family alert
- Day 27: Doctor visit preparation begins

### Phase 4: Intervention (Days 28–30) 🆘→🏥
- **Day 28: CRITICAL ESCALATION Level 3**
  - Emergency voice call to patient
  - SMS + WhatsApp to family
  - Clinical escalation alert to doctor
- Days 29-30: Family visits, vitals begin stabilising
- **Day 30: DOCTOR VISIT** — full 30-day pre-visit report generated

---

## 🌟 Key Features

### 🤖 Patient Agent (Asha)
- Proactive daily check-ins via voice call or WhatsApp
- **Multilingual**: Hindi (Devanagari script) + English
- Detects social isolation from 3+ consecutive non-interaction days
- Tracks medication adherence and fires missed-medication events
- Analyses mood, energy, and symptom patterns
- Smart channel selection: voice call for critical/low-mood days

### 👨‍👩‍👦 Caregiver Agent (ConnectAgent)
- Subscribes to all alert events and notifies family instantly
- Weekly health summary every 7 days
- Urgency-based notifications: info / moderate / critical
- Critical alerts sent via both WhatsApp AND SMS

### 🩺 Clinician Agent (MedInsightAgent)
- Runs trend analysis every 3 days
- Detects deteriorating vs improving vs stable trends
- Generates structured escalation alerts for doctors
- Prepares comprehensive 30-day pre-visit briefings
- Manages escalation levels 0-3 with reasons

### 🗄️ Shared Infrastructure
- **CarePlan**: Singleton shared state — all agents read/write the same object
- **PatientMemory**: SQLite persistence — 5 tables for vitals, check-ins, meds, social, events
- **EventBus**: Synchronous pub/sub — agents coordinate via named event types
- **LanguageHandler**: Real Devanagari Hindi messages, not transliterations

---

## 📊 Event Types

| Event | Publisher | Subscriber(s) |
|-------|-----------|---------------|
| `VITALS_ALERT` | Patient Agent | Clinician Agent |
| `MEDICATION_MISSED` | Patient Agent | Caregiver Agent |
| `SOCIAL_ISOLATION_DETECTED` | Patient Agent | Caregiver Agent |
| `ESCALATION_NEEDED` | Clinician Agent | Caregiver Agent, Doctor |
| `FAMILY_NOTIFICATION` | Any | Caregiver Agent |
| `DOCTOR_VISIT_APPROACHING` | Clinician Agent | (Triggers report prep) |

---

## 🧠 LLM Integration

- Uses **Google Gemini 1.5 Flash** via `google-generativeai`
- Each agent has a specialised, context-rich prompt
- **Graceful fallback**: If `GEMINI_API_KEY` is not set, the system uses detailed template-based responses with real Hindi text
- All LLM calls include: patient vitals context, care plan state, escalation level, medication adherence

---

## 🌐 Multilingual Support

Hindi messages in Devanagari script are included for:
- Morning/afternoon/evening greetings
- Check-in messages
- Medication reminders  
- Family alerts (isolation, medication, critical)
- Symptom responses (chest pain, dizziness, breathlessness)
- Social nudges

Example:
> **नमस्ते राजी! सुप्रभात। 🌅**  
> **रमेश जी, आशा यहाँ से बात कर रही हूँ। आज कैसा महसूस हो रहा है?**

---

## 📋 Output Files

After running the simulation:
- `data/patient_memory.db` — SQLite database with all 30 days of data
- `data/app.log` — Application logs
- `reports/doctor_report_YYYYMMDD_HHMMSS.md` — Doctor pre-visit report

---

## 🔧 Configuration

Edit `config/settings.py` to customise:
- Patient name, age, language, conditions
- Vital thresholds (BP, glucose, heart rate)
- Medication schedule (morning/afternoon/evening)
- Agent check-in frequencies
- Escalation triggers

---

## 📦 Dependencies

```
google-generativeai>=0.8.0   # Gemini LLM API
python-dotenv>=1.0.0         # Environment variable loading
rich>=13.0.0                 # Beautiful terminal UI
colorama>=0.4.6              # Terminal colours (Windows support)
jinja2>=3.1.0                # Template rendering
faker>=20.0.0                # Realistic data generation
schedule>=1.2.0              # Task scheduling utilities
```

---

## 🏆 Hackathon Demo Checklist

- [x] **Patient agent initiates voice/WhatsApp check-ins on its own schedule**
- [x] **Simulated 30-day patient timeline** with realistic deteriorating trend
- [x] **Agents catch deteriorating trend and escalate** (Day 14, 22, 28)
- [x] **Doctor-facing summary** of everything between visits (Day 30)
- [x] **Social wellbeing behaviour** — isolation detection + family/community nudge (Day 24)
- [x] **Agent-to-agent coordination** via shared event bus
- [x] **Multilingual (Hindi/English)** with Devanagari script
- [x] **Gemini LLM integration** with graceful template fallback

---

## 👥 Team

Built for **Track 4: Healthcare & Social Impact — HEALTH-01**  
*Proactive Agents for Chronic Care and Healthy Ageing*

---

## 📄 License

MIT License — built for the hackathon demo.


---

## 💻 Frontend Web Application & Live Dashboard

CareSync AI features a production-grade, responsive Web Application and Clinical Dashboard located in the `frontend/` directory.

### ✨ Key Frontend Features

1. **🏥 Dual-View Experience**:
   - **Landing Page (`frontend/index.html`)**: Introduces the problem statement, life expectancy gap in India (71 yrs life expectancy vs 60.6 yrs healthy life), multi-agent architecture, event bus coordination, interactive vitals ticker, 30-day timeline walkthrough, and impact metrics.
   - **Clinical Dashboard (`frontend/dashboard.html`)**: Rich doctor and caregiver dashboard with real-time analytics, KPIs, Chart.js graphs, vitals table, and escalation status.

2. **📊 Five Interactive Chart.js Visualizations**:
   - **Blood Pressure Trend**: Systolic & Diastolic lines over 30 days with 160/100 danger threshold references.
   - **Escalation Timeline**: Color-coded alert levels (Level 0 green, Level 1 yellow, Level 2 orange, Level 3 red).
   - **Blood Glucose Trend**: Continuous glycaemic monitoring with warning (250 mg/dL) and critical (300 mg/dL) indicators.
   - **Heart Rate & Weight (Dual-Axis)**: Left-axis bpm tracking alongside right-axis kg weight drift.
   - **Mood & Social Score**: Combines daily patient emotional wellbeing (1–5 scale) with social interaction indicators.

3. **🎛️ Interactive Phase Filtering & Sparklines**:
   - Seamless one-click filtering for **Phase 1 (Days 1–10)**, **Phase 2 (Days 11–20)**, **Phase 3 (Days 21–27)**, **Phase 4 (Days 28–30)**, or **All 30 Days**.
   - Dynamically re-aggregates averages (BP, Glucose, HR, Medication Adherence %) on the fly with live canvas sparkline redraws.

4. **▶️ Day-by-Day Simulation Playback Player**:
   - Watch the 30-day chronic care journey unfold with Play / Pause / Reset controls and variable playback speed (`0.5x`, `1x`, `2x`).
   - Automatically highlights and scrolls each day in the vitals table.
   - Triggers live on-screen toast notifications at key clinical milestones:
     - **Day 7**: Weekly summary sent to Suresh Kumar (Caregiver).
     - **Day 14**: MedInsightAgent detects rising BP trend. Escalation to Level 1.
     - **Day 19**: Medication adherence drop alert! Caregiver notified via WhatsApp.
     - **Day 22**: Level 2 Warning! BP 161/101 & glucose 285 mg/dL. Dr. Anjali Sharma alerted.
     - **Day 24**: Social Isolation detected (5 days alone). Asha nudged patient; family alert sent.
     - **Day 28**: CRITICAL Level 3! Emergency voice call to Ramesh ji. Family & doctor dispatched.
     - **Day 30**: Doctor visit day! Comprehensive 30-day clinical report generated.

5. **🔍 30-Day Vitals Table with Search & CSV Export**:
   - Color-coded rows (`.tr-stable`, `.tr-deteriorating`, `.tr-dangerous`, `.tr-intervention`) and vital flags.
   - Instant real-time text search filtering across day, date, phase, symptoms, and status.
   - One-click **"Export CSV ⤓"** downloads the full 30-day dataset.

6. **🔍 Interactive Day Inspector Modal**:
   - Click on any day row to view a comprehensive modal breakdown:
     - Exact physiological metrics (BP, glucose, HR, weight, sleep, activity)
     - Prescribed medications list and adherence status
     - Asha's voice/WhatsApp check-in transcript in genuine Devanagari Hindi with English translation
     - ConnectAgent's family coordination action
     - MedInsightAgent's clinical diagnostic assessment

7. **📄 Pre-Visit Clinical Doctor Report Viewer**:
   - Full 30-day pre-visit report viewer with markdown rendering and one-click print capability.

8. **🤖 Interactive Asha AI Chat Assistant**:
   - Floating companion widget allowing judges and users to converse directly with Asha in Hindi or English.
   - Clinical triage for emergency chest pain, dizziness, missed medicines, loneliness, and vitals status inquiries.
   - Real-time simulation of event bus triggers and caregiver alert notifications.

---

## 🚀 Steps to Execute the Project

### Prerequisites
- Python 3.9 or higher installed
- Modern web browser (Chrome, Edge, Firefox, or Safari)

---

### Step 1: Install Dependencies
Open your terminal in the project root directory and run:
```bash
pip install -r requirements.txt
```

---

### Step 2: (Optional) Configure Gemini LLM API Key
CareSync AI works completely out of the box with intelligent multilingual template responses. To enable Google Gemini 1.5 Flash for dynamic agent replies:
```bash
cp .env.example .env
# Open .env and add your key:
# GEMINI_API_KEY=your_gemini_api_key_here
```

---

### Step 3: Execution Methods

You can experience CareSync AI in three different ways:

#### 🌟 Method 1: Interactive Web Application (Recommended for Demo & Judges)
Launch the CareSync local server:
```bash
python server.py
```
Then open your web browser to:
- **Landing Page**: [http://localhost:8000/](http://localhost:8000/) or [http://localhost:8000/index.html](http://localhost:8000/index.html)
- **Clinical Dashboard**: [http://localhost:8000/dashboard.html](http://localhost:8000/dashboard.html)

*Features active in this mode:*
- Full landing page and live interactive clinical dashboard
- Interactive Day-by-Day Simulation Playback with speed toggles
- Dynamic Chart.js charts and phase filters
- Clickable day rows with detailed Day Inspector Modal
- Pre-Visit Doctor Clinical Report viewer
- Live Asha conversational AI chat with backend REST API integration!

#### 🖥️ Method 2: 30-Day Terminal Simulation Demo
Run the complete multi-agent 30-day CLI simulation in your terminal:
```bash
python main.py
```
*What happens:*
- Boots the SQLite memory store, shared CarePlan, and EventBus.
- Initializes Asha (Patient Agent), ConnectAgent (Caregiver Agent), and MedInsightAgent (Clinician Agent).
- Runs day-by-day with rich color-coded terminal panels.
- Demonstrates Day 7 summary, Day 14 BP trend detection, Day 19 adherence alert, Day 22 escalation, Day 24 isolation detection, Day 28 emergency call, and Day 30 doctor visit report generation.
- Outputs generated report to `reports/doctor_report_YYYYMMDD_HHMMSS.md` and database to `data/patient_memory.db`.

#### 🌐 Method 3: Direct Browser Opening (Zero-Install Alternative)
You can also open the frontend directly in your browser without running any server:
1. Double-click or open `frontend/index.html` in your browser.
2. Click **"Live Dashboard →"** or open `frontend/dashboard.html`.
3. All 30 days of data, Chart.js visualizations, phase filters, day playback, modals, and client-side conversational AI chat will run smoothly offline!
