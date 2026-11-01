"""
server.py
HTTP + REST API server for the CareSync AI multi-agent platform.

- Serves the built React app (react-frontend/dist) with SPA routing.
- Exposes the shared agent network (EventBus, CarePlan, PatientMemory, 5 agents,
  proactive scheduler) as JSON endpoints. See README "How the API works".

Robustness rules applied to every /api route:
- All agent/DB state is guarded by one re-entrant lock (ThreadingHTTPServer runs
  requests in parallel and the agents + the single SQLite connection are not thread-safe).
  Slow Gemini calls run *outside* the lock so polling stays responsive.
- Bad input returns JSON 400, unknown resources 404, unexpected errors JSON 500
  (previously an exception just dropped the connection).
"""

from __future__ import annotations
import glob
import json
import logging
import os
import socket
import sys
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# Ensure UTF-8 stdout encoding for Windows terminals
for _stream in (sys.stdout, sys.stderr):
    if getattr(_stream, "encoding", "utf-8") != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CareSyncServer")

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(_BASE_DIR, "react-frontend", "dist")  # cd react-frontend && npm run build
FRONTEND_BUILT = os.path.isfile(os.path.join(FRONTEND_DIR, "index.html"))
DATA_DIR = os.path.join(_BASE_DIR, "data")
REPORTS_DIR = os.path.join(_BASE_DIR, "reports")
DB_PATH = os.path.join(DATA_DIR, "patient_memory.db")

from core.event_bus import EventBus, EventType
from core.care_plan import initialize_care_plan
from core.memory import PatientMemory
from core.scheduler import AutonomousScheduler
from core.llm import get_llm
from api.mock_integrations import MockWhatsApp, MockSMSGateway, MockVoiceCall
from agents.patient_agent import PatientAgent
from agents.caregiver_agent import CaregiverAgent
from agents.clinician_agent import ClinicianAgent
from agents.risk_agent import RiskAnalysisAgent
from agents.social_agent import SocialWellbeingAgent
from config.settings import (
    PATIENT_PROFILE, CAREGIVER_PROFILE, CLINICIAN_PROFILE, CARE_GOALS, ALL_MEDICATIONS,
)
from nlp.conversational_ai import AshaConversationalEngine

PID = PATIENT_PROFILE["id"]
_STATE_LOCK = threading.RLock()


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


# ─── Singleton agent ecosystem ──────────────────────────────────────────────
event_bus = EventBus()
memory = PatientMemory(db_path=DB_PATH)
whatsapp = MockWhatsApp()
care_plan = None
patient_agent = risk_agent = social_agent = caregiver_agent = clinician_agent = scheduler = None


def _seed_proposals() -> None:
    care_plan.propose_update(
        agent_name="RiskAnalysisAgent",
        category="medications",
        proposed_value="Increase Amlodipine from 5mg to 10mg daily",
        reason="Mean systolic BP (152.5 mmHg) persistently exceeding threshold over 14 days",
        requires_clinical_approval=True,
    )
    care_plan.propose_update(
        agent_name="SocialWellbeingAgent",
        category="activity_goals",
        proposed_value="Daily guided evening walk 15 mins with caregiver check-in",
        reason="Elevated isolation score and reduced activity detected over past 7 days",
        requires_clinical_approval=False,
    )


def build_agent_network() -> None:
    """(Re)create the live agent network. Used at startup and by POST /api/demo/reset."""
    global care_plan, patient_agent, risk_agent, social_agent, caregiver_agent, clinician_agent, scheduler
    event_bus._subscribers.clear()
    event_bus.clear_history()
    # Full care plan (the old server passed no goals/medications → empty clinician med list)
    care_plan = initialize_care_plan(
        patient_id=PID, patient_name=PATIENT_PROFILE["name"],
        goals=CARE_GOALS, medications=list(ALL_MEDICATIONS), vitals_targets=CARE_GOALS["vitals"],
    )
    patient_agent = PatientAgent(care_plan=care_plan, memory=memory, event_bus=event_bus)
    risk_agent = RiskAnalysisAgent(care_plan=care_plan, memory=memory, event_bus=event_bus)
    social_agent = SocialWellbeingAgent(care_plan=care_plan, memory=memory, event_bus=event_bus)
    caregiver_agent = CaregiverAgent(care_plan=care_plan, memory=memory, event_bus=event_bus)
    clinician_agent = ClinicianAgent(care_plan=care_plan, memory=memory, event_bus=event_bus)
    scheduler = AutonomousScheduler(
        event_bus=event_bus, care_plan=care_plan, memory=memory, patient_agent=patient_agent,
        risk_agent=risk_agent, social_agent=social_agent, caregiver_agent=caregiver_agent,
    )
    # Start "today" at the last day stored in memory (30 after python main.py)
    vitals = memory.get_all_vitals(PID)
    care_plan.current_day = max((v["day"] for v in vitals), default=0)
    _restore_escalation(vitals)
    _seed_proposals()


def _restore_escalation(vitals) -> None:
    """The live care plan used to start at Level 0 even when the stored history ended in a
    dangerous state (sidebar said 'Normal' next to 14 urgent alerts). Re-triage the latest
    stored reading — without dispatching new alerts — to set the starting level."""
    if not vitals:
        return
    last = vitals[-1]
    ev = risk_agent.evaluate_health_record(dict(last, symptoms=[], medication_taken=True), day=last["day"])
    level = {"Low Concern": 1, "Moderate Concern": 2, "High Concern": 2, "Emergency": 3}.get(ev["risk_level"], 0)
    if level:
        care_plan.escalate(level, f"Restored from latest stored reading (day {last['day']}): {ev['reasons'][0]}")


build_agent_network()

# ─── LLM ────────────────────────────────────────────────────────────────────
_gemini_client = get_llm()
_gemini_enabled = _gemini_client.configured
if _gemini_enabled:
    logger.info(f"✅ Gemini configured — models: {', '.join(_gemini_client.models)}")
else:
    logger.warning("⚠️ GEMINI_API_KEY not set — Asha chat uses deterministic multilingual fallback.")
_asha_engine = AshaConversationalEngine(gemini_client=_gemini_client if _gemini_enabled else None)


# ─── Helpers ────────────────────────────────────────────────────────────────
def _num(payload: dict, key: str, default, cast=float, lo=None, hi=None):
    """Read a numeric field; 400 on garbage or out-of-range values."""
    raw = payload.get(key, default)
    try:
        val = cast(raw)
    except (TypeError, ValueError):
        raise ApiError(400, f"'{key}' must be a number (got {raw!r})")
    if (lo is not None and val < lo) or (hi is not None and val > hi):
        raise ApiError(400, f"'{key}' must be between {lo} and {hi} (got {val})")
    return val


def _qint(query: dict, key: str, default: int, lo: int = 1, hi: int = 1000) -> int:
    return int(_num({key: query.get(key, [default])[0]}, key, default, int, lo, hi))


def _bool(payload: dict, key: str, default: bool) -> bool:
    v = payload.get(key, default)
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "y")
    return bool(v)


def get_latest_report_text() -> str:
    files = sorted(glob.glob(os.path.join(REPORTS_DIR, "doctor_report_*.md")), reverse=True)
    if files:
        try:
            with open(files[0], "r", encoding="utf-8") as f:
                return f.read()
        except OSError:
            pass
    return "# Pre-Visit Clinical Summary\n\nNo report generated yet. Run `python main.py`."


def get_timeline_json():
    path = os.path.join(DATA_DIR, "timeline_enriched.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def generate_ai_briefing() -> dict:
    """MedInsightAgent: LLM-written narrative briefing from the structured 10-point dashboard."""
    with _STATE_LOCK:
        dash = clinician_agent.get_structured_clinician_dashboard(days=30)
    fallback = "\n".join(f"- {o}" for o in dash["8_ai_observations"])
    if not _gemini_enabled:
        return {"llm_used": False, "briefing": fallback, "llm_error": "GEMINI_API_KEY not configured"}
    compact = {k: v for k, v in dash.items() if k not in ("6_significant_events", "5_symptom_history")}
    prompt = (
        "You are MedInsightAgent, a clinical decision-support assistant preparing a doctor for a visit.\n"
        "Write a concise pre-visit briefing (max 180 words) for Dr. Anjali Sharma in markdown with sections: "
        "**Summary**, **Key Risks**, **Suggested Actions**. Do not invent data; use only this JSON:\n"
        + json.dumps(compact, default=str)[:6000]
    )
    try:  # outside the lock: may take seconds
        r = _gemini_client.generate_content(prompt)
        return {"llm_used": True, "model": r.model, "briefing": r.text}
    except Exception as e:
        return {"llm_used": False, "briefing": fallback, "llm_error": str(e)[:300]}


def generate_asha_reply(user_message: str, day: int, lang: str) -> dict:
    """Asha chat. Triage keywords route alerts through ConnectAgent so the caregiver can acknowledge them."""
    with _STATE_LOCK:
        try:
            context = memory.get_context_for_agent(PID)
        except Exception:
            context = {}
        context["current_escalation_level"] = care_plan.escalation_level

    res = _asha_engine.reply(user_message=user_message, lang=lang, day=day, context=context)  # LLM, unlocked

    level = res.get("alert_level", 0)
    with _STATE_LOCK:
        if level == 3:
            care_plan.escalate(3, f"Chat red-flag symptom reported on day {day}: {user_message[:80]}")
            event_bus.publish(EventType.EMERGENCY_TRIGGERED,
                              {"reason": "Chest pain / breathlessness reported in chat", "message": user_message, "day": day},
                              source="AshaChat", day=day)
            caregiver_agent.notify_family(
                f"🚨 EMERGENCY: Ramesh-ji reported chest pain or breathlessness to Asha: \"{user_message[:120]}\". "
                f"Please call him now or dial 108.", urgency="critical", day=day, source="AshaChat")
            whatsapp.send_message(recipient=CLINICIAN_PROFILE["phone"], sender_name="AshaChat", message_type="urgent_alert",
                                  message=f"🚨 Ramesh Kumar (78M) reported red-flag symptoms in chat on day {day}: \"{user_message[:120]}\"")
        elif level == 2:
            if care_plan.escalation_level < 1:
                care_plan.escalate(1, "Dizziness / headache reported in chat")
            caregiver_agent.notify_family(
                f"⚠️ Ramesh-ji told Asha: \"{user_message[:120]}\". Dizziness or headache can mean high BP. "
                f"Please check on him today.", urgency="moderate", day=day, source="AshaChat")
        elif level == 1:
            caregiver_agent.notify_family(
                f"💊 Ramesh-ji asked Asha about his medicines: \"{user_message[:120]}\". A gentle reminder call may help.",
                urgency="normal", day=day, source="AshaChat")
        res["escalation_level"] = care_plan.escalation_level
    return res


def _reset_live_session() -> dict:
    """Clear in-memory live state (events, messages, escalation, proposals). DB history is kept."""
    MockWhatsApp._message_store.clear()
    MockSMSGateway._sms_logs.clear()
    MockVoiceCall._call_logs.clear()
    build_agent_network()
    return {"success": True, "escalation_level": care_plan.escalation_level,
            "message": f"Live session reset. Events and messages cleared; escalation back to Level "
                       f"{care_plan.escalation_level} (from the latest stored reading)."}


# ─── Route handlers ─────────────────────────────────────────────────────────
def get_status(q):
    return {
        "status": "online",
        "patient": PATIENT_PROFILE,
        "caregiver": CAREGIVER_PROFILE,
        "clinician": CLINICIAN_PROFILE,
        "escalation_level": care_plan.escalation_level,
        "escalation_reason": care_plan.escalation_reason,
        "current_day": care_plan.current_day,
        "gemini_active": _gemini_enabled,
        "frontend_built": FRONTEND_BUILT,
        "agents": [
            {"name": "Asha", "role": "Patient Conversational Companion", "status": "active"},
            {"name": "ConnectAgent", "role": "Caregiver Coordination Agent", "status": "active"},
            {"name": "MedInsightAgent", "role": "Clinician Surveillance & Briefing Agent", "status": "active"},
            {"name": "RiskAnalysisAgent", "role": "Continuous Health Risk & Deterministic Triage Agent", "status": "active"},
            {"name": "SocialWellbeingAgent", "role": "Social Engagement & Healthy Ageing Agent", "status": "active"},
        ],
    }


GET_ROUTES = {
    "/api/status": get_status,
    "/api/timeline": lambda q: get_timeline_json(),
    "/api/report": lambda q: {"report_markdown": get_latest_report_text()},
    "/api/caregiver/dashboard": lambda q: caregiver_agent.get_caregiver_dashboard_data(),
    "/api/clinician/dashboard": lambda q: clinician_agent.get_structured_clinician_dashboard(days=30),
    "/api/care-plan": lambda q: care_plan.to_dict(),
    "/api/schedule": lambda q: {"schedules": scheduler.get_upcoming_schedule(),
                                "history": scheduler.get_execution_history(limit=25)},
    "/api/whatsapp/messages": lambda q: (lambda m: {"messages": m, "total": len(m)})(
        MockWhatsApp.get_messages(limit=_qint(q, "limit", 50))),
    "/api/events": lambda q: (lambda e: {"events": e, "count": len(e)})(
        event_bus.get_history(limit=_qint(q, "limit", 100), event_type=q.get("type", [None])[0])),
}
# Routes that call Gemini manage the lock themselves
GET_UNLOCKED = {
    "/api/llm/status": lambda q: _gemini_client.status(live_test=q.get("test", ["0"])[0] in ("1", "true")),
    "/api/clinician/ai-briefing": lambda q: generate_ai_briefing(),
}


def post_chat(p):
    msg = str(p.get("message", "")).strip()
    if not msg:
        raise ApiError(400, "'message' is required")
    if len(msg) > 1000:
        raise ApiError(400, "'message' is too long (max 1000 characters)")
    day = int(_num(p, "day", care_plan.current_day or 1, int, 0, 365))
    lang = str(p.get("language", "hi"))
    return generate_asha_reply(msg, day=day, lang=lang)


def post_acknowledge(p):
    alert_id = str(p.get("alert_id", "")).strip()
    action = str(p.get("action_taken", "")).strip()
    if not alert_id:
        raise ApiError(400, "'alert_id' is required")
    if not action:
        raise ApiError(400, "'action_taken' is required (e.g. 'Called Papa')")
    result = caregiver_agent.acknowledge_alert(alert_id=alert_id, action_taken=action, notes=str(p.get("notes", "")))
    if result is None:
        raise ApiError(404, f"Alert '{alert_id}' not found")
    return {
        "success": True,
        "message": f"Logged: {action}. The care team can now see this.",
        "alert": memory.get_caregiver_alert(alert_id),
        "action": result,
    }


def post_review(p):
    pid = str(p.get("proposal_id", "")).strip()
    if not pid:
        raise ApiError(400, "'proposal_id' is required")
    existing = next((x for x in care_plan.proposals if x["id"] == pid), None)
    if existing is None:
        raise ApiError(404, f"Proposal '{pid}' not found")
    if existing["status"] != "pending_review":
        raise ApiError(409, f"Proposal is already {existing['status']}")
    approve = _bool(p, "approve", True)
    notes = str(p.get("notes", ""))
    ok = clinician_agent.review_care_plan_proposal(proposal_id=pid, approve=approve, notes=notes)
    return {"success": ok, "proposal_id": pid, "status": "approved" if approve else "rejected",
            "notes": notes, "reviewer": CLINICIAN_PROFILE["name"], "proposal": existing}


def post_propose(p):
    value = p.get("proposed_value")
    if value in (None, ""):
        raise ApiError(400, "'proposed_value' is required")
    proposal = care_plan.propose_update(
        agent_name=str(p.get("proposed_by", p.get("agent_name", "Doctor"))),
        category=str(p.get("category", "medications")),
        proposed_value=value,
        reason=str(p.get("reason", "Clinical adjustment")),
        requires_clinical_approval=_bool(p, "requires_clinical_approval", True),
    )
    return {"success": True, "proposal": proposal}


def post_emergency(p):
    day = int(_num(p, "day", care_plan.current_day or 1, int, 0, 365))
    source = str(p.get("trigger_source", "Patient SOS Button"))
    notes = str(p.get("notes", "Patient pressed emergency SOS alert."))
    care_plan.escalate(3, f"🚨 EMERGENCY: {source} activated: {notes}")
    event_bus.publish(EventType.EMERGENCY_TRIGGERED, {"source": source, "notes": notes, "day": day},
                      source="EmergencySOS", day=day)
    msg = (f"🚨 EMERGENCY: Ramesh Kumar pressed the SOS button. Location: {PATIENT_PROFILE['address']}. "
           f"Please call him now or dial 108.")
    # Through ConnectAgent → WhatsApp + SMS + an alert the caregiver can acknowledge
    alert = caregiver_agent.notify_family(msg, urgency="critical", day=day, source="EmergencySOS")
    whatsapp.send_message(recipient=CLINICIAN_PROFILE["phone"], sender_name="CareSync Emergency",
                          message_type="urgent_alert",
                          message="🚨 CLINICAL EMERGENCY: Ramesh Kumar (78M) triggered the SOS button.")
    return {"status": "emergency_triggered", "escalation_level": 3, "alert_id": alert["alert_id"],
            "dispatched_to": [CAREGIVER_PROFILE["name"], CLINICIAN_PROFILE["name"]],
            "message": msg, "timestamp": datetime.now().isoformat()}


def post_checkin(p):
    if not isinstance(p.get("symptoms", []), list):
        raise ApiError(400, "'symptoms' must be a list of strings")
    day = int(_num(p, "day", (care_plan.current_day or 0) + 1, int, 0, 365))
    data = {
        "day": day,
        "bp_systolic": _num(p, "bp_systolic", 140, float, 50, 260),
        "bp_diastolic": _num(p, "bp_diastolic", 85, float, 30, 160),
        "blood_glucose": _num(p, "blood_glucose", 140, float, 20, 700),
        "heart_rate": _num(p, "heart_rate", 76, float, 25, 220),
        "medication_taken": _bool(p, "medication_taken", True),
        "mood": str(p.get("mood", "calm")),
        "symptoms": [str(s) for s in (p.get("symptoms") or []) if str(s).strip()],
        "social_interaction": True,
    }
    # Persist first so the risk agent's 7-day baseline includes today
    memory.log_vitals(patient_id=PID, day=day, bp_systolic=int(data["bp_systolic"]), bp_diastolic=int(data["bp_diastolic"]),
                      heart_rate=int(data["heart_rate"]), blood_glucose=float(data["blood_glucose"]),
                      weight=0.0, sleep_hours=0.0, activity_minutes=0)
    memory.log_medication(patient_id=PID, day=day, med_name="Amlodipine / Metformin", dose="as prescribed",
                          scheduled_time="08:00", taken=data["medication_taken"])
    mood_score = {"happy": 5, "calm": 4, "tired": 2, "dizzy": 1}.get(data["mood"], 3)
    memory.log_checkin(patient_id=PID, day=day, mood=mood_score, energy=mood_score,
                       pain_level=2 if data["symptoms"] else 0, symptoms=data["symptoms"])
    risk = risk_agent.assess(data, day=day)  # evaluate + alert + escalate
    care_plan.current_day = max(care_plan.current_day, day)
    return {"success": True, "day": day, "risk_analysis": risk, "current_escalation": care_plan.escalation_level,
            "message": "Check-in saved. RiskAnalysisAgent reviewed it."}


def post_run_day(p):
    day = int(_num(p, "day", (care_plan.current_day or 0) + 1, int, 1, 365))
    data = p.get("data") or {
        "day": day, "bp_systolic": 138, "bp_diastolic": 84, "blood_glucose": 145, "heart_rate": 74,
        "medication_taken": True, "mood": "happy", "symptoms": [], "social_interaction": True,
    }
    if not isinstance(data, dict):
        raise ApiError(400, "'data' must be an object with the day's vitals")
    return {"day": day, "scheduled_results": scheduler.execute_scheduled_day(day, data),
            "escalation_level": care_plan.escalation_level}


def post_inbound(p):
    inbound = whatsapp.receive_inbound(
        from_number=str(p.get("from_number", CAREGIVER_PROFILE["phone"])),
        message=str(p.get("message", "Papa had breakfast and took his medicines.")),
    )
    return {"success": True, "inbound": inbound}


POST_ROUTES = {
    "/api/caregiver/acknowledge": post_acknowledge,
    "/api/care-plan/review": post_review,
    "/api/care-plan/propose": post_propose,
    "/api/emergency": post_emergency,
    "/api/patient/checkin": post_checkin,
    "/api/schedule/run-day": post_run_day,
    "/api/whatsapp/simulate-inbound": post_inbound,
    "/api/demo/reset": lambda p: _reset_live_session(),
}
POST_UNLOCKED = {"/api/chat": post_chat}


# ─── HTTP handler ───────────────────────────────────────────────────────────
class CareSyncHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def log_message(self, fmt, *args):  # quieter: only log API calls and errors
        if "/api/" in (args[0] if args else "") or (len(args) > 1 and str(args[1])[:1] in "45"):
            super().log_message(fmt, *args)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _dispatch(self, routes, unlocked, arg):
        path = urlparse(self.path).path.rstrip("/") or "/"
        try:
            if path in unlocked:
                return self._send_json(unlocked[path](arg))
            if path in routes:
                with _STATE_LOCK:
                    return self._send_json(routes[path](arg))
            other = GET_ROUTES.keys() | GET_UNLOCKED.keys() if routes is POST_ROUTES else POST_ROUTES.keys() | POST_UNLOCKED.keys()
            if path in other:
                raise ApiError(405, f"Use {'GET' if routes is POST_ROUTES else 'POST'} for {path}")
            raise ApiError(404, f"API endpoint not found: {path}")
        except ApiError as e:
            self._send_json({"error": e.message, "status": e.status}, status=e.status)
        except Exception as e:  # never drop the connection
            logger.exception(f"Unhandled error on {self.command} {path}")
            self._send_json({"error": f"Internal server error: {type(e).__name__}: {e}", "status": 500}, status=500)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            return self._dispatch(GET_ROUTES, GET_UNLOCKED, parse_qs(parsed.query))

        if not FRONTEND_BUILT:
            body = (b"<h1>CareSync AI API is running</h1><p>The React app is not built yet. Run "
                    b"<code>cd react-frontend &amp;&amp; npm install &amp;&amp; npm run build</code> and restart, "
                    b"or use <code>npm run dev</code> on :5173.</p>")
            self.send_response(503)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Static files + SPA routing (unknown paths → index.html for React Router)
        local = os.path.normpath(os.path.join(FRONTEND_DIR, parsed.path.lstrip("/")))
        if parsed.path in ("", "/") or not local.startswith(FRONTEND_DIR) or not os.path.isfile(local):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if not urlparse(self.path).path.startswith("/api/"):
            return self._send_json({"error": "Not found", "status": 404}, status=404)
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            length = 0
        if length > 1_000_000:
            return self._send_json({"error": "Request body too large", "status": 413}, status=413)
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            payload = json.loads(raw.decode("utf-8")) if raw.strip() else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._send_json({"error": "Body must be valid JSON", "status": 400}, status=400)
        if not isinstance(payload, dict):
            return self._send_json({"error": "Body must be a JSON object", "status": 400}, status=400)
        return self._dispatch(POST_ROUTES, POST_UNLOCKED, payload)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class DualStackServer(ThreadingHTTPServer):
    """Listen on IPv6 and IPv4. On Windows `localhost` resolves to ::1 first; an IPv4-only
    server made every browser request wait ~2 s for the IPv6 attempt to time out."""
    address_family = socket.AF_INET6
    daemon_threads = True

    def server_bind(self):
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except (AttributeError, OSError):
            pass
        super().server_bind()


def run_server(port: int = 8000):
    try:
        httpd = DualStackServer(("::", port), CareSyncHandler)
    except OSError:  # IPv6 unavailable
        httpd = ThreadingHTTPServer(("0.0.0.0", port), CareSyncHandler)
    print()
    print("=" * 72)
    print("  CareSync AI — Multi-Agent Healthcare Management Platform")
    print("  Track 4: HEALTH-01 — Proactive Agents for Chronic Care & Healthy Ageing")
    print("=" * 72)
    if FRONTEND_BUILT:
        print(f"  * Home:               http://localhost:{port}/")
        print(f"  * Agent Control Room: http://localhost:{port}/agents")
        print(f"  * Clinician:          http://localhost:{port}/clinician")
        print(f"  * Caregiver:          http://localhost:{port}/caregiver")
        print(f"  * Patient (Asha):     http://localhost:{port}/patient")
    else:
        print("  * React app NOT built — run: cd react-frontend && npm install && npm run build")
    print(f"  * LLM Status:         {('Gemini configured: ' + _gemini_client.models[0]) if _gemini_enabled else 'Template fallback (no GEMINI_API_KEY)'}")
    print(f"  * LLM Diagnostics:    http://localhost:{port}/api/llm/status?test=1")
    print("=" * 72)
    print("  Press Ctrl+C to terminate the server.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[CareSync] Shutting down server gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8000
    run_server(port=port)
