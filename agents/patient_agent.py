"""
agents/patient_agent.py
Patient Agent (Asha) — the primary conversational interface with the elderly patient.
Handles proactive multilingual check-ins (Hindi, Marathi, English), medicine tracking,
vitals logging, symptom triage, memory-informed dialogue, and voice interaction.
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from agents.base_agent import BaseAgent
from core.care_plan import CarePlan
from core.event_bus import EventBus, EventType
from core.memory import PatientMemory
from config.settings import (
    VITAL_THRESHOLDS,
    PATIENT_PROFILE,
    MEDICATION_SCHEDULE,
    AGENT_CONFIG,
)
from nlp.language_handler import LanguageHandler
from api.mock_integrations import MockVoiceCall, MockWhatsApp

logger = logging.getLogger(__name__)


class PatientAgent(BaseAgent):
    """
    Asha proactively checks in with the patient on schedule,
    communicates in preferred languages (Hindi, Marathi, English),
    logs vitals and symptoms into longitudinal memory, and adapts to responses.
    """

    def __init__(
        self,
        care_plan: CarePlan,
        memory: PatientMemory,
        event_bus: EventBus,
    ):
        super().__init__(
            name=AGENT_CONFIG["patient_agent"]["name"],
            care_plan=care_plan,
            memory=memory,
            event_bus=event_bus,
        )
        self.lang_handler = LanguageHandler()
        self.voice = MockVoiceCall()
        self.whatsapp = MockWhatsApp()
        self.patient_id = PATIENT_PROFILE["id"]
        self.patient_name = PATIENT_PROFILE["name"]
        self.isolation_threshold = AGENT_CONFIG["patient_agent"]["isolation_threshold_days"]
        self._checkin_count = 0

    # ─── Main Daily Check-in Runner ────────────────────────────────────────

    def run_check_in(self, patient_data: Dict[str, Any]) -> str:
        """
        Executes daily scheduled check-in.
        Selects voice/WhatsApp channel, logs metrics, and fires events.
        """
        day = patient_data.get("day", 0)
        self.care_plan.current_day = day
        self._checkin_count += 1

        use_voice = self._should_use_voice(patient_data)
        checkin_message = self.conduct_checkin(patient_data)
        simulated_response = self._simulate_patient_response(patient_data)
        analysis = self.analyze_response(simulated_response, patient_data)

        # Log vitals into longitudinal memory
        self.memory.log_vitals(
            patient_id=self.patient_id,
            day=day,
            bp_systolic=patient_data.get("bp_systolic", 135),
            bp_diastolic=patient_data.get("bp_diastolic", 85),
            heart_rate=patient_data.get("heart_rate", 72),
            blood_glucose=patient_data.get("blood_glucose", 150),
            weight=patient_data.get("weight", 72.0),
            sleep_hours=patient_data.get("sleep_hours", 7.0),
            activity_minutes=patient_data.get("activity_minutes", 30),
        )

        # Log checkin record
        self.memory.log_checkin(
            patient_id=self.patient_id,
            day=day,
            mood=analysis["mood"],
            energy=analysis["energy"],
            pain_level=analysis["pain_level"],
            symptoms=patient_data.get("symptoms", []),
            notes=simulated_response,
            agent_response=checkin_message,
            language=PATIENT_PROFILE.get("primary_language", "Hindi"),
        )

        # Log medications
        med_taken = patient_data.get("medication_taken", True)
        for slot, meds in MEDICATION_SCHEDULE.items():
            for med in meds:
                self.memory.log_medication(
                    patient_id=self.patient_id,
                    day=day,
                    med_name=med["name"],
                    dose=med["dose"],
                    scheduled_time=med["time"],
                    taken=med_taken,
                )

        # Log social interaction
        social = patient_data.get("social_interaction", True)
        self.memory.log_social(
            patient_id=self.patient_id,
            day=day,
            had_interaction=social,
            interaction_type="family" if social else "none",
            duration_minutes=30 if social else 0,
            mood_after=analysis["mood"],
        )

        # Update shared care plan state
        self.care_plan.update_vitals(patient_data)
        adherence_stats = self.memory.get_medication_adherence(self.patient_id, days=day)
        self.care_plan.update_adherence(adherence_stats["adherence_pct"])
        social_summary = self.memory.get_social_summary(self.patient_id, days=7)
        social_score = max(1.0, 5.0 - social_summary["isolation_days"])
        self.care_plan.update_social_score(social_score)

        # Publish coordination events
        self._fire_events(day, patient_data, analysis)

        # Publish CHECKIN_COMPLETED for RiskAnalysisAgent and SocialWellbeingAgent
        self.event_bus.publish(
            event_type=EventType.CHECKIN_COMPLETED,
            data=patient_data,
            source=self.name,
            day=day,
        )

        summary = (
            f"[Day {day}] Check-in via {'📞 Voice Call' if use_voice else '💬 WhatsApp'} | "
            f"Mood: {analysis['mood']}/5 | "
            f"Meds: {'✅' if med_taken else '❌ MISSED'} | "
            f"Social: {'✅' if social else '⚠️ Isolated'} | "
            f"BP: {patient_data.get('bp_systolic')}/{patient_data.get('bp_diastolic')} | "
            f"Glucose: {patient_data.get('blood_glucose')}"
        )
        return summary

    # ─── Multilingual Interactive Chat (Voice / Text) ──────────────────────

    def chat(self, user_message: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Interactive conversational interface used by web patient portal and voice assistant.
        Retrieves longitudinal memory context first before responding.
        """
        lang = self.lang_handler._normalize_language(language or PATIENT_PROFILE.get("primary_language", "Hindi"))
        context = self.memory.get_context_for_agent(self.patient_id)
        msg_lower = user_message.lower()

        # Check for urgent symptom complaints
        symptoms_detected = []
        for sym in ["chest pain", "सीने में दर्द", "छातीत दुखणे", "dizziness", "चक्कर", "headache", "सिरदर्द", "डोकेदुखी", "breathlessness", "सांस फूलना"]:
            if sym in msg_lower:
                symptoms_detected.append(sym)

        # Generate contextual prompt if Gemini available
        if self._llm_available:
            prompt = f"""You are Asha, a warm elderly-care AI companion for {self.patient_name} (78M, Hypertension + T2 Diabetes).
Patient language preference: {lang}.
Patient context:
- 7-day Systolic BP Avg: {context.get('bp_systolic_7d_avg')} mmHg (Trend: {context.get('bp_trend_direction')})
- Medication Adherence: {context.get('adherence_7d_pct')}%
- Recent symptoms: {context.get('recent_symptoms')}
- Current Escalation Level: {self.care_plan.escalation_level}/3

User message: "{user_message}"

Instructions:
1. Respond with warmth, respect, and clear reassurance in {lang} (use Devanagari script for Hindi/Marathi, with English translation in parentheses).
2. If patient reports chest pain, extreme dizziness or breathlessness, urge them to sit immediately and state that Suresh and doctor are notified.
3. Keep response concise (under 75 words).
"""
            reply = self._call_llm(prompt)
        else:
            # High-quality deterministic fallback
            reply = self._get_fallback_chat_reply(msg_lower, lang, context)

        # Trigger event if danger symptoms mentioned
        if any(k in msg_lower for k in ["chest", "सीने", "छातीत"]):
            self.event_bus.publish(
                event_type=EventType.EMERGENCY_TRIGGERED,
                data={"symptom": "chest pain", "message": user_message},
                source=self.name,
                day=self.care_plan.current_day,
            )

        return {
            "reply": reply,
            "language": lang,
            "symptoms_detected": symptoms_detected,
            "escalation_level": self.care_plan.escalation_level,
        }

    def _get_fallback_chat_reply(self, msg_lower: str, lang: str, context: Dict[str, Any]) -> str:
        if any(k in msg_lower for k in ["chest", "सीने में दर्द", "छातीत"]):
            if lang == "Marathi":
                return "⚠️ रमेश जी, छातीत दुखणे गंभीर लक्षण असू शकते! कृपया त्वरित बसा आणि पाणी प्या। मी सुरेश यांना तात्काळ सूचना दिली आहे।"
            elif lang == "Hindi":
                return "⚠️ रमेश जी, सीने में दर्द गंभीर हो सकता है! कृपया तुरंत बैठ जाएं। मैंने सुरेश और डॉक्टर को आपातकालीन अलर्ट भेज दिया है।"
            return "⚠️ Ramesh ji, chest pain can be serious! Please sit down immediately. I have notified Suresh and Dr. Sharma."

        if any(k in msg_lower for k in ["चक्कर", "dizzy", "headache", "सिरदर्द", "डोके"]):
            if lang == "Marathi":
                return "रमेश जी, चक्कर किंवा डोकेदुखी रक्तदाब वाढल्याचे लक्षण असू शकते। शांत बसा आणि विश्रांती घ्या। आजची औषधे घेतली आहेत का?"
            elif lang == "Hindi":
                return "रमेश जी, चक्कर या सिरदर्द बीपी बढ़ने का संकेत हो सकता है। कृपया आराम से बैठें, पानी पिएं और अपना बीपी चेक करें।"
            return "Ramesh ji, dizziness or headache can indicate elevated blood pressure. Please rest and check your BP."

        if any(k in msg_lower for k in ["दवाई", "औषध", "medicine", "tablet"]):
            if lang == "Marathi":
                return "💊 रमेश जी, तुमची सकाळची औषधे (Amlodipine आणि Metformin) अत्यंत महत्त्वाची आहेत। कृपया नियमित वेळेवर घ्या।"
            elif lang == "Hindi":
                return "💊 रमेश जी, आपकी बीपी और शुगर की दवाइयाँ नियमित लेना बहुत ज़रूरी है। कृपया समय पर खुराक लें।"
            return "💊 Ramesh ji, taking your prescribed BP and diabetes medications on time is essential for your stability."

        if any(k in msg_lower for k in ["नमस्ते", "नमस्कार", "hello", "hi", "प्रणाम"]):
            return self.lang_handler.get_greeting(lang, "morning") + " रमेश जी, आज कशी प्रकृती आहे? / आज कैसा महसूस हो रहा है?"

        return "धन्यवाद रमेश जी! 🙏 मी ही नोंद तुमच्या आरोग्य पुस्तिकेत ठेवली आहे। काळजी घ्या आणि नियमित पाणी प्या!"

    # ─── Channel & Proactivity Helpers ─────────────────────────────────────

    def _should_use_voice(self, patient_data: Dict[str, Any]) -> bool:
        """Use voice call for critical days or low mood to ensure elderly accessibility."""
        day = patient_data.get("day", 0)
        mood = patient_data.get("mood", 3)
        bp_sys = patient_data.get("bp_systolic", 130)
        return day in [22, 28] or mood <= 2 or bp_sys >= 165

    def conduct_checkin(self, patient_data: Dict[str, Any]) -> str:
        day = patient_data.get("day", 0)
        lang = PATIENT_PROFILE.get("primary_language", "Hindi")
        time_of_day = "morning" if day % 2 == 0 else "evening"

        if not patient_data.get("medication_taken", True):
            return self.lang_handler.get_medication_reminder(lang, "Amlodipine 5mg & Metformin")
        return self.lang_handler.get_checkin_message(lang, self.patient_name)

    def _simulate_patient_response(self, patient_data: Dict[str, Any]) -> str:
        symptoms = patient_data.get("symptoms", [])
        med_taken = patient_data.get("medication_taken", True)
        if symptoms:
            return f"Aaj thoda {', '.join(symptoms)} lag raha hai."
        if not med_taken:
            return "Subah dawai lena bhool gaya tha."
        return "Sab theek hai, BP check kar liya hai."

    def analyze_response(self, response_text: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "mood": patient_data.get("mood", 3),
            "energy": 3 if patient_data.get("mood", 3) >= 3 else 2,
            "pain_level": 5 if "chest" in response_text else (2 if "headache" in response_text else 0),
        }

    def _fire_events(self, day: int, patient_data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
        bp_sys = patient_data.get("bp_systolic", 130)
        gluc = patient_data.get("blood_glucose", 140)

        # Vital alert
        if bp_sys >= VITAL_THRESHOLDS["bp_systolic"]["warning_high"] or gluc >= VITAL_THRESHOLDS["blood_glucose"]["warning_high"]:
            self.event_bus.publish(
                event_type=EventType.VITALS_ALERT,
                data=patient_data,
                source=self.name,
                day=day,
            )

        # Medication missed
        if not patient_data.get("medication_taken", True):
            self.event_bus.publish(
                event_type=EventType.MEDICATION_MISSED,
                data={"day": day, "patient_name": self.patient_name},
                source=self.name,
                day=day,
            )

        # Social isolation
        if not patient_data.get("social_interaction", True):
            social_summary = self.memory.get_social_summary(self.patient_id, days=self.isolation_threshold)
            if social_summary["isolation_days"] >= self.isolation_threshold:
                self.event_bus.publish(
                    event_type=EventType.SOCIAL_ISOLATION_DETECTED,
                    data={"isolation_days": social_summary["isolation_days"]},
                    source=self.name,
                    day=day,
                )
