"""
agents/patient_agent.py
Patient Agent — the primary interface with the patient.
Handles multilingual check-ins, medicine tracking, vitals logging,
mood/social analysis, and isolation detection.
"""

from __future__ import annotations
import logging
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
    The Patient Agent proactively checks in with the patient,
    tracks medicines/vitals, analyses mood and social signals,
    and fires events on the shared event bus.
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

    # ─── Main Entry Point ──────────────────────────────────────────────────

    def run_check_in(self, patient_data: Dict[str, Any]) -> str:
        """
        Called by DemoRunner for each simulation day.
        Decides channel, conducts check-in, analyses response, logs everything.
        """
        day = patient_data.get("day", 0)
        self.care_plan.current_day = day
        self._checkin_count += 1

        # Decide whether to use voice or WhatsApp based on day/risk
        use_voice = self._should_use_voice(patient_data)

        # Build and deliver the check-in message
        checkin_message = self.conduct_checkin(patient_data)

        # Simulate patient response (from simulation data)
        simulated_response = self._simulate_patient_response(patient_data)

        # Analyse response for mood, adherence, social signals
        analysis = self.analyze_response(simulated_response, patient_data)

        # Log vitals into memory
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

        # Log check-in
        self.memory.log_checkin(
            patient_id=self.patient_id,
            day=day,
            mood=analysis["mood"],
            energy=analysis["energy"],
            pain_level=analysis["pain_level"],
            symptoms=patient_data.get("symptoms", []),
            notes=simulated_response,
            agent_response=checkin_message,
            language=PATIENT_PROFILE["primary_language"],
        )

        # Log medication adherence
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

        # Update care plan
        self.care_plan.update_vitals(patient_data)
        adherence_stats = self.memory.get_medication_adherence(self.patient_id, days=day)
        self.care_plan.update_adherence(adherence_stats["adherence_pct"])
        social_summary = self.memory.get_social_summary(self.patient_id, days=7)
        social_score = max(1.0, 5.0 - social_summary["isolation_days"])
        self.care_plan.update_social_score(social_score)

        # Publish events
        self._fire_events(day, patient_data, analysis)

        # Detect isolation
        isolation = self.detect_isolation(
            self.memory.get_social_summary(self.patient_id, days=self.isolation_threshold)
        )

        summary = (
            f"[Day {day}] Check-in via {'📞 Voice' if use_voice else '💬 WhatsApp'} | "
            f"Mood: {analysis['mood']}/5 | "
            f"Meds: {'✅' if med_taken else '❌ MISSED'} | "
            f"Social: {'✅' if social else '⚠️ Isolated'} | "
            f"BP: {patient_data.get('bp_systolic')}/{patient_data.get('bp_diastolic')} | "
            f"Glucose: {patient_data.get('blood_glucose')}"
        )
        return summary

    # ─── Check-in Conversation ─────────────────────────────────────────────

    def initiate_checkin(self, day: int, patient_data: Dict[str, Any]) -> bool:
        """
        Decide whether to proactively initiate a check-in.
        Returns True if check-in was initiated.
        """
        # Always check in; increase frequency when escalation level is high
        if self.care_plan.escalation_level >= 2:
            return True
        return True  # Daily check-ins always on for demo

    def conduct_checkin(self, patient_data: Dict[str, Any]) -> str:
        """
        Build a personalised multilingual check-in message using Gemini (or fallback).
        Returns the message sent to the patient.
        """
        day = patient_data.get("day", 0)
        language = PATIENT_PROFILE["primary_language"]
        time_of_day = "morning" if day % 3 == 0 else ("afternoon" if day % 3 == 1 else "evening")

        # Use Gemini for richer messages when available
        context = {
            "task": "Generate a warm, personalised check-in message for the patient",
            "day": day,
            "language": language,
            "time_of_day": time_of_day,
            "bp": f"{patient_data.get('bp_systolic')}/{patient_data.get('bp_diastolic')} mmHg",
            "glucose_yesterday": f"{patient_data.get('blood_glucose')} mg/dL",
            "medication_taken_yesterday": patient_data.get("medication_taken", True),
            "escalation_level": self.care_plan.escalation_level,
            "include_hindi_greeting": True,
            "symptoms_reported": patient_data.get("symptoms", []),
        }

        if self._llm_available:
            prompt = self._build_patient_prompt(context)
            message = self._call_llm(prompt)
        else:
            message = self._template_checkin(patient_data, language, time_of_day)

        return message

    def _build_patient_prompt(self, context: Dict[str, Any]) -> str:
        """Build a detailed Gemini prompt for the patient check-in."""
        symptoms_str = ", ".join(context.get("symptoms_reported", [])) or "none reported"
        med_status = "Yes ✓" if context.get("medication_taken_yesterday") else "No — MISSED ✗"
        escalation = context.get("escalation_level", 0)

        return f"""
You are Asha, a warm, caring AI health companion for elderly patients in India.
You are calling Ramesh Kumar (78 years old) for his daily health check-in.
He prefers Hindi but also understands English.

CURRENT HEALTH STATUS:
- Day of monitoring: {context['day']}
- BP yesterday: {context['bp']}
- Blood glucose: {context['glucose_yesterday']}
- Medications taken yesterday: {med_status}
- Symptoms reported: {symptoms_str}
- Escalation level: {escalation}/3

TASK: Write a warm, friendly {context['time_of_day']} check-in message in HINGLISH 
(mix of Hindi in Devanagari script and English) that:
1. Greets him appropriately for {context['time_of_day']}
2. Asks how he's feeling
3. Reminds him to take his medicines {'(GENTLE REMINDER - he missed yesterday)' if not context.get('medication_taken_yesterday') else ''}
4. Asks about his BP and sugar readings
5. Asks if he's had any social interaction today
{'6. Gently expresses concern about his rising vitals' if escalation >= 2 else ''}

Keep it under 100 words. Be like a caring family member, not a robot.
Start with a Hindi greeting in Devanagari.
""".strip()

    def _template_checkin(
        self, patient_data: Dict, language: str, time_of_day: str
    ) -> str:
        """Template-based check-in message (Gemini fallback)."""
        greeting = self.lang_handler.get_greeting(language, time_of_day)
        med_reminder = ""
        if not patient_data.get("medication_taken", True):
            med_reminder = self.lang_handler.get_medication_reminder(
                language, "Amlodipine, Metformin"
            )
        symptoms = patient_data.get("symptoms", [])
        symptoms_str = f"Symptoms noted: {', '.join(symptoms)}." if symptoms else ""

        return (
            f"{greeting}\n"
            f"Ramesh ji, aaj kaisa mahsoos ho raha hai? {symptoms_str} "
            f"Kya aapne BP aur sugar check kiya? "
            f"{med_reminder} "
            f"Aur aaj kisi se baat hui? Parivaar mein sab theek? "
            f"\n(How are you feeling today? {symptoms_str} "
            f"Did you check your BP and sugar? {med_reminder} "
            f"Did you talk to anyone today? All well at home?)"
        ).strip()

    # ─── Response Analysis ─────────────────────────────────────────────────

    def analyze_response(
        self, response: str, vitals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract mood, energy, pain level from simulated patient response and vitals.
        Returns a dict with extracted signals.
        """
        mood = vitals.get("mood", 3)
        symptoms = vitals.get("symptoms", [])
        pain_level = 3 if "pain" in symptoms else (2 if "chest pain" in symptoms else 1)
        energy = max(1, min(5, mood - (1 if len(symptoms) > 2 else 0)))

        # Detect social isolation signal from response text
        isolation_keywords = ["alone", "akela", "koi nahi", "bored", "lonely"]
        isolation_hinted = any(kw in response.lower() for kw in isolation_keywords)

        return {
            "mood": mood,
            "energy": energy,
            "pain_level": pain_level,
            "isolation_hinted": isolation_hinted,
            "symptoms_count": len(symptoms),
            "raw_response": response,
        }

    def _simulate_patient_response(self, patient_data: Dict[str, Any]) -> str:
        """Generate a realistic simulated patient response for the demo."""
        mood = patient_data.get("mood", 3)
        symptoms = patient_data.get("symptoms", [])
        social = patient_data.get("social_interaction", True)
        med_taken = patient_data.get("medication_taken", True)
        day = patient_data.get("day", 1)

        if mood >= 4 and not symptoms:
            response = (
                "Haan Asha beti, aaj theek hoon. Subah walk bhi ki. "
                f"BP check kiya — {patient_data.get('bp_systolic')}/{patient_data.get('bp_diastolic')} aaya. "
                "Dawai bhi le li. Beta ka phone bhi aaya tha."
            )
        elif mood == 3 and len(symptoms) <= 1:
            response = (
                f"Theek hoon, bas thoda thaka hua hoon. "
                f"BP {patient_data.get('bp_systolic')} raha aaj. "
                f"{'Dawai le li.' if med_taken else 'Dawai bhool gayi subah.'}"
            )
        elif mood <= 2 or len(symptoms) >= 2:
            sym_str = ", ".join(symptoms) if symptoms else "sir dard"
            response = (
                f"Nahi theek nahi hoon. {sym_str} ho raha hai. "
                f"BP bhi zyada lag raha hai — {patient_data.get('bp_systolic')} aaya. "
                f"{'Dawai nahi li.' if not med_taken else 'Dawai li.'} "
                f"{'Koi aaya nahi aaj.' if not social else 'Suresh aa gaya tha.'}"
            )
        else:
            response = (
                f"Asha, aaj thoda uncomfortable hoon. "
                f"Sugar {patient_data.get('blood_glucose')} aayi. "
                f"{'Akela mehsoos ho raha hoon.' if not social else 'Pooja ji se baat ki.'}"
            )

        return response

    # ─── Isolation Detection ───────────────────────────────────────────────

    def detect_isolation(self, social_summary: Dict[str, Any]) -> bool:
        """
        Check if patient has been socially isolated.
        Publishes SOCIAL_ISOLATION_DETECTED if isolation is detected.
        Returns True if isolation detected.
        """
        isolation_days = social_summary.get("isolation_days", 0)
        total_days = social_summary.get("total_days", 1)

        if isolation_days >= self.isolation_threshold or (
            total_days >= 5 and social_summary.get("isolation_pct", 0) >= 60
        ):
            day = self.care_plan.current_day
            self.event_bus.publish(
                event_type=EventType.SOCIAL_ISOLATION_DETECTED,
                data={
                    "patient_name": self.patient_name,
                    "isolation_days": isolation_days,
                    "total_days_checked": total_days,
                    "isolation_pct": social_summary.get("isolation_pct", 0),
                    "message": (
                        f"{self.patient_name} has had no social interaction for "
                        f"{isolation_days} of the last {total_days} days."
                    ),
                },
                source=self.name,
                day=day,
            )
            self.care_plan.add_event(
                event_type="SOCIAL_ISOLATION",
                description=f"Social isolation detected: {isolation_days}/{total_days} days without interaction.",
                severity="warning",
            )
            logger.warning(f"[{self.name}] Social isolation detected: {isolation_days} days.")
            return True
        return False

    # ─── Event Publishing ──────────────────────────────────────────────────

    def _fire_events(
        self,
        day: int,
        patient_data: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> None:
        """Evaluate vitals and publish appropriate events."""
        bp_sys = patient_data.get("bp_systolic", 130)
        bp_dia = patient_data.get("bp_diastolic", 85)
        glucose = patient_data.get("blood_glucose", 150)
        hr = patient_data.get("heart_rate", 72)
        med_taken = patient_data.get("medication_taken", True)

        thresholds = VITAL_THRESHOLDS

        # BP check
        if bp_sys >= thresholds["bp_systolic"]["danger_high"] or bp_sys <= thresholds["bp_systolic"]["danger_low"]:
            self._publish_vitals_alert(day, "bp_systolic", bp_sys, "DANGER")
        elif bp_sys >= thresholds["bp_systolic"]["warning_high"]:
            self._publish_vitals_alert(day, "bp_systolic", bp_sys, "WARNING")

        # Glucose check
        if glucose >= thresholds["blood_glucose"]["danger_high"]:
            self._publish_vitals_alert(day, "blood_glucose", glucose, "DANGER")
        elif glucose >= thresholds["blood_glucose"]["warning_high"]:
            self._publish_vitals_alert(day, "blood_glucose", glucose, "WARNING")

        # Heart rate
        if hr >= thresholds["heart_rate"]["danger_high"] or hr <= thresholds["heart_rate"]["danger_low"]:
            self._publish_vitals_alert(day, "heart_rate", hr, "DANGER")

        # Medication missed
        if not med_taken:
            self.event_bus.publish(
                event_type=EventType.MEDICATION_MISSED,
                data={
                    "patient_name": self.patient_name,
                    "day": day,
                    "message": f"{self.patient_name} did not take medications on day {day}.",
                },
                source=self.name,
                day=day,
            )

    def _publish_vitals_alert(
        self, day: int, metric: str, value: float, severity: str
    ) -> None:
        self.event_bus.publish(
            event_type=EventType.VITALS_ALERT,
            data={
                "patient_name": self.patient_name,
                "metric": metric,
                "value": value,
                "severity": severity,
                "day": day,
                "message": f"{severity}: {metric}={value} on day {day}",
            },
            source=self.name,
            day=day,
        )

    def _should_use_voice(self, patient_data: Dict[str, Any]) -> bool:
        """Voice call if escalation high or mood low; WhatsApp otherwise."""
        return (
            self.care_plan.escalation_level >= 2
            or patient_data.get("mood", 3) <= 2
            or not patient_data.get("medication_taken", True)
        )
