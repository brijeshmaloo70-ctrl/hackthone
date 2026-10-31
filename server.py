"""
server.py
Lightweight HTTP and REST API server for CareSync AI Multi-Agent Healthcare Platform.
Serves role-based frontend portals and provides comprehensive APIs for:
- Patient interactive check-ins, multilingual chat, and one-touch emergency SOS
- Caregiver dashboard, alert acknowledgments, and action logging
- Clinician 10-point structured dashboard and care plan proposal review/approval
- Live Event Bus stream and WhatsApp communication gateway simulator
- Autonomous proactive scheduler execution
"""

from __future__ import annotations
import os
import sys
import json
import logging
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import glob

# Ensure UTF-8 stdout encoding for Windows terminals
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr.encoding != "utf-8":
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Environment setup
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CareSyncServer")

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
DB_PATH = os.path.join(DATA_DIR, "patient_memory.db")

# Import Core Multi-Agent Infrastructure
from core.event_bus import EventBus, EventType
from core.care_plan import CarePlan
from core.memory import PatientMemory
from core.scheduler import AutonomousScheduler
from api.mock_integrations import MockWhatsApp, MockSMSGateway, MockVoiceCall
from agents.patient_agent import PatientAgent
from agents.caregiver_agent import CaregiverAgent
from agents.clinician_agent import ClinicianAgent
from agents.risk_agent import RiskAnalysisAgent
from agents.social_agent import SocialWellbeingAgent
from config.settings import PATIENT_PROFILE, CAREGIVER_PROFILE, CLINICIAN_PROFILE, VITAL_THRESHOLDS
from nlp.language_handler import LanguageHandler
from nlp.conversational_ai import AshaConversationalEngine

# ─── Singleton Agent Ecosystem ──────────────────────────────────────────────
event_bus = EventBus()
care_plan = CarePlan(patient_id=PATIENT_PROFILE["id"], patient_name=PATIENT_PROFILE["name"])
memory = PatientMemory(db_path=DB_PATH)
lang_handler = LanguageHandler()
whatsapp = MockWhatsApp()

patient_agent = PatientAgent(care_plan=care_plan, memory=memory, event_bus=event_bus)
risk_agent = RiskAnalysisAgent(care_plan=care_plan, memory=memory, event_bus=event_bus)
social_agent = SocialWellbeingAgent(care_plan=care_plan, memory=memory, event_bus=event_bus)
caregiver_agent = CaregiverAgent(care_plan=care_plan, memory=memory, event_bus=event_bus)
clinician_agent = ClinicianAgent(care_plan=care_plan, memory=memory, event_bus=event_bus)

scheduler = AutonomousScheduler(
    event_bus=event_bus,
    care_plan=care_plan,
    memory=memory,
    patient_agent=patient_agent,
    risk_agent=risk_agent,
    social_agent=social_agent,
    caregiver_agent=caregiver_agent,
)

# Seed an initial care plan proposal if none exists for demonstration
if not care_plan.proposals:
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

# ─── LLM Setup ─────────────────────────────────────────────────────────────
_gemini_client = None
_gemini_enabled = False
api_key = os.environ.get("GEMINI_API_KEY", "").strip()
if api_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _gemini_client = genai.GenerativeModel("gemini-1.5-flash")
        _gemini_enabled = True
        logger.info("✅ Gemini LLM initialized for live Asha conversational agent.")
    except Exception as e:
        logger.warning(f"Could not initialize Gemini: {e}")


def get_latest_report_text() -> str:
    """Fetch the latest doctor report markdown."""
    report_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "doctor_report_*.md")), reverse=True)
    if report_files:
        try:
            with open(report_files[0], "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return "# Pre-Visit Clinical Summary\n\nNo report generated yet. Run python main.py or trigger via demo dashboard."


def get_timeline_json():
    """Load the 30-day timeline."""
    path = os.path.join(DATA_DIR, "timeline_enriched.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def generate_asha_reply(user_message: str, day: int = 1, lang: str = "hi") -> dict:
    """Generate rich, empathetic, and clinical reply for Asha AI companion."""
    engine = AshaConversationalEngine(gemini_client=_gemini_client if _gemini_enabled else None)
    res = engine.reply(user_message=user_message, lang=lang, day=day)
    
    # Trigger appropriate agent events & notifications if risk detected
    if res.get("alert_level") == 3:
        event_bus.publish(
            event_type=EventType.EMERGENCY_TRIGGERED,
            data={"reason": "Acute discomfort / chest pain reported in chat", "day": day},
            source="AshaChat",
            day=day,
        )
        whatsapp.send_message(
            recipient=CAREGIVER_PROFILE["phone"],
            message=f"🚨 EMERGENCY ALERT: Ramesh-ji reported acute chest distress during chat. Please contact him or 108 immediately!",
            sender_name="CareSync Emergency",
            message_type="urgent_alert",
        )
    elif res.get("alert_level") == 2:
        event_bus.publish(
            event_type=EventType.RISK_ALERT_ISSUED,
            data={"risk_level": "Moderate Concern", "reason": "Dizziness / headache reported in chat", "day": day},
            source="AshaChat",
            day=day,
        )

    return res


# ─── HTTP Request Handler ────────────────────────────────────────────────────
class CareSyncHandler(SimpleHTTPRequestHandler):
    """Custom request handler with full REST APIs and static file serving."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        # 1. System Status & Agent Registry
        if parsed.path == "/api/status":
            self._send_json({
                "status": "online",
                "patient": PATIENT_PROFILE,
                "caregiver": CAREGIVER_PROFILE,
                "clinician": CLINICIAN_PROFILE,
                "escalation_level": care_plan.escalation_level,
                "current_day": care_plan.current_day or 30,
                "gemini_active": _gemini_enabled,
                "agents": [
                    {"name": "Asha", "role": "Patient Conversational Companion", "status": "active"},
                    {"name": "ConnectAgent", "role": "Caregiver Coordination Agent", "status": "active"},
                    {"name": "MedInsightAgent", "role": "Clinician Surveillance & Briefing Agent", "status": "active"},
                    {"name": "RiskAnalysisAgent", "role": "Continuous Health Risk & Deterministic Triage Agent", "status": "active"},
                    {"name": "SocialWellbeingAgent", "role": "Social Engagement & Healthy Ageing Agent", "status": "active"},
                ],
            })
            return

        # 2. Timeline
        if parsed.path == "/api/timeline":
            data = get_timeline_json()
            self._send_json(data)
            return

        # 3. Doctor Pre-Visit Clinical Report
        if parsed.path == "/api/report":
            text = get_latest_report_text()
            self._send_json({"report_markdown": text})
            return

        # 4. Caregiver Scoped Dashboard
        if parsed.path == "/api/caregiver/dashboard":
            data = caregiver_agent.get_caregiver_dashboard_data()
            self._send_json(data)
            return

        # 5. Clinician 10-Point Structured Dashboard
        if parsed.path == "/api/clinician/dashboard":
            data = clinician_agent.get_structured_clinician_dashboard(days=30)
            self._send_json(data)
            return

        # 6. Central Care Plan
        if parsed.path == "/api/care-plan":
            self._send_json(care_plan.to_dict())
            return

        # 7. Autonomous Proactive Scheduler
        if parsed.path == "/api/schedule":
            self._send_json({
                "schedules": scheduler.get_upcoming_schedule(),
                "history": scheduler.get_execution_history(limit=25),
            })
            return

        # 8. WhatsApp Message Store & Inspection
        if parsed.path == "/api/whatsapp/messages":
            limit = int(query.get("limit", [50])[0])
            messages = MockWhatsApp.get_messages(limit=limit)
            self._send_json({"messages": messages, "total": len(messages)})
            return

        # 9. Real-Time Event Bus Chronicle
        if parsed.path == "/api/events":
            limit = int(query.get("limit", [100])[0])
            event_type = query.get("type", [None])[0]
            events = event_bus.get_history(limit=limit, event_type=event_type)
            self._send_json({"events": events, "count": len(events)})
            return

        # Static file fallback
        if parsed.path in ["", "/"]:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            payload = json.loads(post_body.decode("utf-8"))
        except Exception:
            payload = {}

        # 1. Live Asha Multilingual Chat
        if parsed.path == "/api/chat":
            user_msg = payload.get("message", "")
            day = int(payload.get("day", care_plan.current_day or 1))
            lang = payload.get("language", "hi")
            response = generate_asha_reply(user_msg, day=day, lang=lang)
            self._send_json(response)
            return

        # 2. Caregiver Alert Acknowledgment
        if parsed.path == "/api/caregiver/acknowledge":
            alert_id = payload.get("alert_id", "alert_001")
            action_taken = payload.get("action_taken", "Called patient")
            notes = payload.get("notes", "Checked on papa, he is resting comfortably.")
            caregiver_agent.acknowledge_alert(alert_id=alert_id, action_taken=action_taken, notes=notes)
            self._send_json({
                "success": True,
                "message": f"Alert {alert_id} acknowledged by Suresh Kumar.",
                "action_recorded": action_taken,
                "timestamp": datetime.now().isoformat(),
            })
            return

        # 3. Care Plan Clinical Proposal Review (Doctor Authorization)
        if parsed.path == "/api/care-plan/review":
            proposal_id = payload.get("proposal_id", "")
            approve = bool(payload.get("approve", True))
            notes = payload.get("notes", "Reviewed and approved based on 30-day vitals trend.")
            success = clinician_agent.review_care_plan_proposal(
                proposal_id=proposal_id,
                approve=approve,
                notes=notes,
            )
            self._send_json({
                "success": success,
                "proposal_id": proposal_id,
                "status": "approved" if approve and success else ("rejected" if not approve else "failed"),
                "notes": notes,
                "reviewer": CLINICIAN_PROFILE["name"],
            })
            return

        # 4. Propose Care Plan Update
        if parsed.path == "/api/care-plan/propose":
            agent_name = payload.get("proposed_by", payload.get("agent_name", "Doctor"))
            category = payload.get("category", "medications")
            proposed_val = payload.get("proposed_value", "")
            reason = payload.get("reason", "Clinical adjustment")
            requires_approval = bool(payload.get("requires_clinical_approval", True))
            proposal = care_plan.propose_update(
                agent_name=agent_name,
                category=category,
                proposed_value=proposed_val,
                reason=reason,
                requires_clinical_approval=requires_approval,
            )
            self._send_json({"success": True, "proposal": proposal})
            return

        # 5. One-Touch Emergency SOS Protocol
        if parsed.path == "/api/emergency":
            day = int(payload.get("day", care_plan.current_day or 1))
            trigger_source = payload.get("trigger_source", "Patient SOS Button")
            notes = payload.get("notes", "Patient pressed emergency SOS alert.")

            # Escalate care plan
            care_plan.update_escalation(3, f"🚨 EMERGENCY: {trigger_source} activated: {notes}", day=day)

            # Fire canonical event
            event_bus.publish(
                event_type=EventType.EMERGENCY_TRIGGERED,
                data={"source": trigger_source, "notes": notes, "day": day},
                source="EmergencySOS",
                day=day,
            )

            # Dispatch high-priority simulated WhatsApp & SMS
            msg_text = (
                f"🚨 EMERGENCY ALERT: Ramesh Kumar has pressed the SOS Emergency Button! "
                f"Location: C-14, Sector 22, Noida. Please contact him or call 108 immediately!"
            )
            whatsapp.send_message(
                recipient=CAREGIVER_PROFILE["phone"],
                message=msg_text,
                sender_name="CareSync Emergency",
                message_type="urgent_alert",
            )
            whatsapp.send_message(
                recipient=CLINICIAN_PROFILE["phone"],
                message=f"🚨 CLINICAL EMERGENCY: Patient Ramesh Kumar (78M) triggered SOS emergency alert.",
                sender_name="CareSync Emergency",
                message_type="urgent_alert",
            )

            # Log caregiver action via memory
            memory.log_caregiver_action(
                patient_id=PATIENT_PROFILE["id"],
                caregiver_name=CAREGIVER_PROFILE["name"],
                action_taken="Emergency Dispatched",
                notes="Automatic emergency notification dispatched to son and doctor.",
                day=day,
            )

            self._send_json({
                "status": "emergency_triggered",
                "escalation_level": 3,
                "dispatched_to": [CAREGIVER_PROFILE["name"], CLINICIAN_PROFILE["name"]],
                "message": msg_text,
                "timestamp": datetime.now().isoformat(),
            })
            return

        # 6. Live Patient Check-in Submission
        if parsed.path == "/api/patient/checkin":
            day = int(payload.get("day", (care_plan.current_day or 0) + 1))
            bp_systolic = float(payload.get("bp_systolic", 140))
            bp_diastolic = float(payload.get("bp_diastolic", 85))
            blood_glucose = float(payload.get("blood_glucose", 140))
            heart_rate = float(payload.get("heart_rate", 76))
            medication_taken = bool(payload.get("medication_taken", True))
            mood = payload.get("mood", "calm")
            symptoms = payload.get("symptoms", [])

            checkin_data = {
                "day": day,
                "bp_systolic": bp_systolic,
                "bp_diastolic": bp_diastolic,
                "blood_glucose": blood_glucose,
                "heart_rate": heart_rate,
                "medication_taken": medication_taken,
                "mood": mood,
                "symptoms": symptoms,
                "social_interaction": True,
            }

            # Run deterministic Risk Agent evaluation
            risk_result = risk_agent.evaluate_health_record(checkin_data, day=day)

            # Persist to longitudinal SQLite memory
            memory.log_vitals(
                patient_id=PATIENT_PROFILE["id"],
                day=day,
                bp_systolic=int(bp_systolic),
                bp_diastolic=int(bp_diastolic),
                heart_rate=int(heart_rate),
                blood_glucose=float(blood_glucose),
                weight=0.0,
                sleep_hours=0.0,
                activity_minutes=0,
            )
            memory.log_medication(
                patient_id=PATIENT_PROFILE["id"],
                day=day,
                med_name="Amlodipine / Metformin",
                dose="as prescribed",
                scheduled_time="08:00",
                taken=medication_taken,
            )
            mood_score = {"happy": 5, "calm": 4, "tired": 2, "dizzy": 1}.get(mood, 3)
            memory.log_checkin(
                patient_id=PATIENT_PROFILE["id"],
                day=day,
                mood=mood_score,
                energy=mood_score,
                pain_level=2 if "dizzy" in (symptoms or []) else 0,
                symptoms=symptoms or [],
            )

            # Advance care plan current day
            care_plan.current_day = max(care_plan.current_day, day)

            self._send_json({
                "success": True,
                "day": day,
                "risk_analysis": risk_result,
                "current_escalation": care_plan.escalation_level,
                "message": "Check-in analyzed and saved to longitudinal patient memory.",
            })
            return

        # 7. Execute Autonomous Scheduled Day
        if parsed.path == "/api/schedule/run-day":
            day = int(payload.get("day", 1))
            day_data = payload.get("data", {
                "day": day,
                "bp_systolic": 138,
                "bp_diastolic": 84,
                "blood_glucose": 145,
                "heart_rate": 74,
                "medication_taken": True,
                "mood": "happy",
                "symptoms": [],
                "social_interaction": True,
            })
            results = scheduler.execute_scheduled_day(day, day_data)
            self._send_json({"day": day, "scheduled_results": results})
            return

        # 8. Simulate Inbound WhatsApp Message
        if parsed.path == "/api/whatsapp/simulate-inbound":
            from_num = payload.get("from_number", CAREGIVER_PROFILE["phone"])
            message_text = payload.get("message", "Papa had breakfast and took his medicines.")
            inbound = whatsapp.receive_inbound(from_number=from_num, message=message_text)
            self._send_json({"success": True, "inbound": inbound})
            return

        self.send_error(404, "API endpoint not found")

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = 8000, host: str = "0.0.0.0"):
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, CareSyncHandler)

    print()
    print("=" * 72)
    print("  CareSync AI — Multi-Agent Healthcare Management Platform")
    print("  Track 4: HEALTH-01 — Proactive Agents for Chronic Care & Healthy Ageing")
    print("=" * 72)
    print(f"  * Landing Page:       http://localhost:{port}/index.html")
    print(f"  * Elderly Patient UI: http://localhost:{port}/patient.html")
    print(f"  * Caregiver Portal:   http://localhost:{port}/caregiver.html")
    print(f"  * Clinician Board:    http://localhost:{port}/dashboard.html")
    print(f"  * Demo / System Hub:  http://localhost:{port}/demo.html")
    print(f"  * LLM Status:         {'Gemini 1.5 Flash (Active)' if _gemini_enabled else 'Intelligent Multilingual Fallback'}")
    print("=" * 72)
    print("  Press Ctrl+C to terminate the server.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[CareSync] Shutting down server gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port=port)
