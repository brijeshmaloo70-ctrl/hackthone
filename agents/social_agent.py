"""
agents/social_agent.py
Social Wellbeing Agent (SocialWellbeingAgent).
Tracks healthy ageing beyond physical vitals: emotional wellbeing,
routine engagement, gentle activity nudges, and family reconnection.
Explicitly avoids clinical psychiatric diagnosis.
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from core.care_plan import CarePlan
from core.memory import PatientMemory
from core.event_bus import EventBus, EventType
from config.settings import PATIENT_PROFILE, CAREGIVER_PROFILE, AGENT_CONFIG
from nlp.language_handler import LanguageHandler
from api.mock_integrations import MockWhatsApp

logger = logging.getLogger(__name__)


class SocialWellbeingAgent(BaseAgent):
    """
    Monitors emotional patterns, social connectedness, and daily routine.
    Provides gentle non-clinical encouragement and coordinates with family.
    """

    def __init__(
        self,
        care_plan: CarePlan,
        memory: PatientMemory,
        event_bus: EventBus,
    ):
        super().__init__(
            name="SocialWellbeingAgent",
            care_plan=care_plan,
            memory=memory,
            event_bus=event_bus,
        )
        self.patient_id = PATIENT_PROFILE["id"]
        self.patient_name = PATIENT_PROFILE["name"]
        self.caregiver_name = CAREGIVER_PROFILE["name"]
        self.lang_handler = LanguageHandler()
        self.whatsapp = MockWhatsApp()
        self.isolation_threshold = 3  # days
        self._interventions_log: List[Dict[str, Any]] = []

        # Subscribe to social isolation events
        self.event_bus.subscribe(EventType.SOCIAL_ISOLATION_DETECTED, self._on_isolation_detected)

    def _on_isolation_detected(self, event) -> None:
        """Handle social isolation detected by patient agent or memory check."""
        day = event.day
        isolation_days = event.data.get("isolation_days", 3)
        self.handle_isolation(isolation_days=isolation_days, day=day)

    def evaluate_social_health(self, day: int, day_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate daily social signals, mood, activity minutes, and consecutive isolated days.
        """
        mood_raw = day_data.get("mood", 3)
        if isinstance(mood_raw, str):
            mood = {"happy": 5, "calm": 4, "tired": 2, "dizzy": 1}.get(mood_raw.lower(), 3)
        else:
            try:
                mood = int(mood_raw)
            except (ValueError, TypeError):
                mood = 3
        activity_mins = day_data.get("activity_minutes", 20)
        had_social = day_data.get("social_interaction", True)

        # Log into social_logs in memory
        self.memory.log_social(
            patient_id=self.patient_id,
            day=day,
            had_interaction=had_social,
            interaction_type="family" if had_social else "none",
            duration_minutes=30 if had_social else 0,
            mood_after=mood,
            notes="Evaluated by SocialWellbeingAgent",
        )

        # Retrieve rolling 7-day social summary
        social_summary = self.memory.get_social_summary(self.patient_id, days=7)
        isolation_days = social_summary.get("isolation_days", 0)

        # Update care plan social score (1.0 to 5.0)
        # Score calculation: base 5, minus 0.6 per isolation day, adjusted for mood
        social_score = max(1.0, min(5.0, 5.0 - (isolation_days * 0.6) + (mood - 3) * 0.3))
        self.care_plan.update_social_score(social_score)

        intervention_needed = False
        intervention_details = ""

        # Trigger intervention if 3+ days without contact or low mood + low activity
        if isolation_days >= self.isolation_threshold:
            intervention_needed = True
            intervention_details = f"Patient has spent {isolation_days} consecutive days without social engagement."
            self.handle_isolation(isolation_days, day)
        elif mood <= 2 and activity_mins < 15:
            intervention_needed = True
            intervention_details = "Low energy and mood detected; gentle walking and hydration encouragement sent."
            self._send_routine_nudge(day)

        return {
            "day": day,
            "isolation_days_7d": isolation_days,
            "social_score": social_score,
            "intervention_triggered": intervention_needed,
            "details": intervention_details,
        }

    def handle_isolation(self, isolation_days: int, day: int) -> None:
        """
        Non-clinical family engagement intervention with patient consent.
        """
        lang = PATIENT_PROFILE.get("primary_language", "Hindi")
        patient_nudge = self.lang_handler.get_isolation_nudge(lang, isolation_days)

        # 1. Gently nudge patient
        logger.info(f"[SocialWellbeingAgent] Nudging patient {self.patient_name} (isolation={isolation_days}d)")

        # 2. Inform caregiver with suggested positive activities (not alarming them)
        family_msg = (
            f"💙 Family Wellbeing Update: {self.patient_name} has had limited social connection over the last "
            f"{isolation_days} days. Research indicates regular conversation significantly improves chronic care outcomes. "
            f"Could you plan a phone call, video chat, or visit today? Suresh, your involvement makes a world of difference!"
        )
        self.whatsapp.send_message(
            recipient=CAREGIVER_PROFILE["phone"],
            message=family_msg,
            sender_name="SocialWellbeingAgent",
        )

        record = {
            "day": day,
            "timestamp": datetime.now().isoformat(),
            "isolation_days": isolation_days,
            "action": "Family check-in suggested & patient companion nudge sent",
            "patient_message": patient_nudge,
            "caregiver_message": family_msg,
        }
        self._interventions_log.append(record)

        # Publish event
        self.event_bus.publish(
            event_type=EventType.SOCIAL_INTERVENTION_TRIGGERED,
            data=record,
            source="SocialWellbeingAgent",
            day=day,
        )

        # Propose care plan goal adjustment if persistent
        if isolation_days >= 4:
            self.care_plan.propose_update(
                agent_name="SocialWellbeingAgent",
                category="current_concerns",
                proposed_value=list(set(self.care_plan.current_concerns + [f"Social isolation: {isolation_days} days unaccompanied"])),
                reason=f"Persistent isolation ({isolation_days} days). Recommend caregiver engagement and community activity.",
                requires_clinical_approval=False,
            )

    def _send_routine_nudge(self, day: int) -> None:
        """Send gentle healthy ageing routine reminder (walk, hobby, music, water)."""
        lang = PATIENT_PROFILE.get("primary_language", "Hindi")
        if lang == "Hindi":
            msg = "रमेश जी, हल्की धूप में 15 मिनट की सैर और ताज़ा पानी आपके स्वास्थ्य को तरोताज़ा कर देगा। ☀️ क्या आज थोड़ा टहलने का मन है?"
        elif lang == "Marathi":
            msg = "रमेश जी, थोडा वेळ हलकी फेरफटका मारणे आणि पाणी पिणे आपल्या आरोग्यासाठी खूप छान राहील। ☀️"
        else:
            msg = "Ramesh ji, a gentle 15-minute stroll and a glass of water can refresh your energy! ☀️"

        self.whatsapp.send_message(
            recipient=PATIENT_PROFILE["phone"],
            message=msg,
            sender_name="SocialWellbeingAgent",
        )

    def run_check_in(self, patient_data: Dict[str, Any]) -> str:
        """Called daily to track social connectedness."""
        day = patient_data.get("day", self.care_plan.current_day)
        res = self.evaluate_social_health(day, patient_data)
        return f"[Day {day}] Social Wellbeing: Score {res['social_score']}/5 (Isolation: {res['isolation_days_7d']}d)"

    def get_interventions(self) -> List[Dict[str, Any]]:
        return self._interventions_log
