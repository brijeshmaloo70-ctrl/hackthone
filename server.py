"""
server.py
Lightweight HTTP and API server for CareSync AI Web Dashboard.
Serves the frontend application and provides interactive REST APIs
for patient timeline, pre-visit clinical report, and live Asha AI chat.
"""

from __future__ import annotations
import os
import sys
import json
import logging
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import glob

# Try loading environment variables
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

# LLM setup
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
    return "# Pre-Visit Clinical Summary\n\nNo report generated yet. Run python main.py to generate."


def get_timeline_json():
    """Load the 30-day timeline."""
    path = os.path.join(DATA_DIR, "timeline_enriched.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def generate_asha_reply(user_message: str, day: int = 1) -> dict:
    """Generate reply using Gemini if configured, otherwise rule-based multilingual fallback."""
    msg_lower = user_message.lower()
    alert_level = 0
    caregiver_alert = ""

    # Clinical symptom detection
    if any(k in msg_lower for k in ["सीने में दर्द", "chest pain", "tightness", "heart"]):
        alert_level = 3
        caregiver_alert = "🚨 Emergency alert sent to Suresh Kumar: Ramesh reported chest pain."
    elif any(k in msg_lower for k in ["चक्कर", "dizzy", "dizziness", "सिरदर्द", "headache"]):
        alert_level = 2
        caregiver_alert = "⚠️ Caregiver alerted: Ramesh reported dizziness/headache."
    elif any(k in msg_lower for k in ["दवाई", "medicine", "tablet", "भूल", "missed"]):
        alert_level = 1
        caregiver_alert = "💊 Medication reminder sent to caregiver."

    if _gemini_enabled and _gemini_client is not None:
        try:
            prompt = f"""You are Asha, a compassionate and expert AI healthcare companion for Ramesh Kumar (78M, with Hypertension and Type 2 Diabetes).
Patient is on Day {day} of care monitoring.
Patient message: "{user_message}"

Guidelines:
1. Respond warmly and respectfully using Devanagari Hindi, followed by English translation in parentheses.
2. If patient mentions chest pain, severe dizziness, or shortness of breath, urgently instruct them to sit down, stay calm, and state that Suresh (son) and Dr. Anjali Sharma are alerted.
3. If they missed medicines, gently remind them of their importance.
4. Keep the response concise, caring, and under 90 words.
"""
            res = _gemini_client.generate_content(prompt)
            return {
                "reply": res.text.strip(),
                "alert_level": alert_level,
                "caregiver_alert": caregiver_alert,
                "llm_used": True
            }
        except Exception as err:
            logger.warning(f"Gemini generation error: {err}")

    # Intelligent fallback
    if alert_level == 3:
        reply = (
            "⚠️ **रमेश जी, सीने में दर्द को बिल्कुल नज़रअंदाज़ न करें!**<br/>"
            "कृपया तुरंत बैठ जाइए, ढीले कपड़े पहनें और पानी पिएं। मैंने आपके बेटे सुरेश को आपातकालीन कॉल कर दी है "
            "और डॉक्टर अंजलि शर्मा को सूचित कर दिया है। यदि दर्द बढ़े तो तुरंत 108 बुलाएं।"
        )
    elif alert_level == 2:
        reply = (
            "रमेश जी, चक्कर या सिरदर्द हाई ब्लड प्रेशर का लक्षण हो सकता है। 🩺<br/>"
            "कृपया आराम से बैठें, अपनी आँखें बंद करें और बीपी चेक करें। क्या आपने आज की दवाई ली थी? "
            "मैंने सुरेश जी को स्थिति से अवगत करा दिया है।"
        )
    elif alert_level == 1:
        reply = (
            "💊 रमेश जी, आपकी दवाइयाँ (Amlodipine 5mg और Metformin 500mg) समय पर लेना बहुत ज़रूरी है।<br/>"
            "कृपया अभी एक गिलास पानी के साथ अपनी खुराक ले लीजिए। नियमितता ही आपको स्वस्थ रखेगी।"
        )
    elif any(k in msg_lower for k in ["अकेला", "lonely", "उदासी", "sad", "मन नहीं लग रहा"]):
        reply = (
            "रमेश जी, मैं हमेशा आपके साथ हूँ। 💙 अकेलापन महसूस होना स्वाभाविक है। "
            "क्या आप चाहेंगे कि मैं सुरेश जी को संदेश भेजूं ताकि वे आज शाम आपसे बात कर सकें?"
        )
    else:
        reply = (
            "नमस्ते रमेश जी! 🙏 मैं आपकी बात समझ गई हूँ और इसे आपके दैनिक हेल्थ रिकॉर्ड में दर्ज कर लिया है।<br/>"
            "समय पर पानी पीते रहें, हल्का भोजन करें और कोई भी परेशानी हो तो मुझे तुरंत बताएं!"
        )

    return {
        "reply": reply,
        "alert_level": alert_level,
        "caregiver_alert": caregiver_alert,
        "llm_used": False
    }


class CareSyncHandler(SimpleHTTPRequestHandler):
    """Custom request handler with API endpoints and static file serving."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/timeline":
            data = get_timeline_json()
            self._send_json(data)
            return

        if parsed.path == "/api/report":
            text = get_latest_report_text()
            self._send_json({"report_markdown": text})
            return

        if parsed.path == "/api/status":
            self._send_json({
                "status": "online",
                "patient": "Ramesh Kumar (78M)",
                "gemini_active": _gemini_enabled,
                "agents": ["Asha (Patient Agent)", "ConnectAgent (Caregiver)", "MedInsightAgent (Clinician)"]
            })
            return

        # Default static file serving (index.html for root)
        if parsed.path in ["", "/"]:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/chat":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            try:
                payload = json.loads(post_body.decode("utf-8"))
            except Exception:
                payload = {}

            user_msg = payload.get("message", "")
            day = payload.get("day", 1)
            response = generate_asha_reply(user_msg, day=day)
            self._send_json(response)
            return

        self.send_error(404, "API endpoint not found")

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = 8000, host: str = "0.0.0.0"):
    # Ensure stdout handles utf-8 if possible
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, CareSyncHandler)

    print()
    print("=" * 64)
    print("  CareSync AI - Proactive Chronic Care Management Web App")
    print("=" * 64)
    print(f"  * Local URL:      http://localhost:{port}/")
    print(f"  * Landing Page:   http://localhost:{port}/index.html")
    print(f"  * Live Dashboard: http://localhost:{port}/dashboard.html")
    print(f"  * LLM Status:     {'Gemini 1.5 Flash (Active)' if _gemini_enabled else 'Template Mode (No API Key)'}")
    print("=" * 64)
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
