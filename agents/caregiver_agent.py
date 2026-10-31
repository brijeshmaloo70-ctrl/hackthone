"""
agents/caregiver_agent.py
Caregiver Agent — keeps the patient's family informed and engaged.
Subscribes to isolation, escalation, and family notification events.
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from core.care_plan import CarePlan
from core.event_bus import EventBus, EventType, Event
from core.memory import PatientMemory
from config.settings import CAREGIVER_PROFILE, PATIENT_PROFILE, AGENT_CONFIG
from nlp.language_handler import LanguageHandler
from api.mock_integrations import MockWhatsApp, MockSMSGateway

logger = logging.getLogger(__name__)


class CaregiverAgent(BaseAgent):
    """
    The Caregiver Agent notifies the family about the patient's status,
    sends weekly summaries, and responds urgently to escalations.
    """

    def __init__(
        self,
        care_plan: CarePlan,
        memory: PatientMemory,
        event_bus: EventBus,
    ):
        super().__init__(
            name=AGENT_CONFIG["caregiver_agent"]["name"],
            care_plan=care_plan,
            memory=memory,
            event_bus=event_bus,
        )
        self.lang_handler = LanguageHandler()
        self.whatsapp = MockWhatsApp()
        self.sms = MockSMSGateway()
        self.patient_id = PATIENT_PROFILE["id"]
        self.patient_name = PATIENT_PROFILE["name"]
        self.caregiver_name = CAREGIVER_PROFILE["name"]
        self.caregiver_phone = CAREGIVER_PROFILE["phone"]
        self.notifications_sent: List[Dict[str, Any]] = []

        # Subscribe to events
        self._subscribe_to_events()

    # ─── Subscriptions ─────────────────────────────────────────────────────

    def _subscribe_to_events(self) -> None:
        """Register handlers for all events this agent cares about."""
        self.event_bus.subscribe(EventType.FAMILY_NOTIFICATION, self._on_family_notification)
        self.event_bus.subscribe(EventType.ESCALATION_NEEDED, self._on_escalation)
        self.event_bus.subscribe(EventType.SOCIAL_ISOLATION_DETECTED, self._on_isolation)
        self.event_bus.subscribe(EventType.MEDICATION_MISSED, self._on_medication_missed)

    # ─── Event Handlers ────────────────────────────────────────────────────

    def _on_family_notification(self, event: Event) -> None:
        message = event.data.get("message", "Health update for your family member.")
        urgency = event.data.get("urgency", "normal")
        self.notify_family(message, urgency, day=event.day)

    def _on_escalation(self, event: Event) -> None:
        message = event.data.get("message", f"⚠️ URGENT: {self.patient_name} needs attention!")
        self.notify_family(message, urgency="critical", day=event.day)

    def _on_isolation(self, event: Event) -> None:
        isolation_days = event.data.get("isolation_days", 0)
        lang = CAREGIVER_PROFILE.get("preferred_language", "English")
        message = self.lang_handler.get_family_alert(lang, "isolation", self.patient_name)
        message += (
            f"\n📊 Detail: {self.patient_name} has had no meaningful social contact "
            f"for {isolation_days} consecutive days. "
            f"Please visit or video call him today."
        )
        self.notify_family(message, urgency="moderate", day=event.day)

    def _on_medication_missed(self, event: Event) -> None:
        day = event.data.get("day", self.care_plan.current_day)
        message = (
            f"💊 Medication Alert: {self.patient_name} missed his medications on Day {day}. "
            f"Please remind him to take his medicines. "
            f"Missing BP and diabetes medication can be dangerous."
        )
        self.notify_family(message, urgency="moderate", day=day)

    # ─── Main Methods ──────────────────────────────────────────────────────

    def run_check_in(self, patient_data: Dict[str, Any]) -> str:
        """
        Called daily by DemoRunner.
        Generates a brief status update for the caregiver.
        """
        day = patient_data.get("day", 0)

        # On day 7, 14, 21, 28 send weekly summary
        if day % 7 == 0 and day > 0:
            history = self.memory.get_history(self.patient_id, days=7)
            summary = self.weekly_summary(
                vitals_list=[
                    dict(row) for row in history.get("vitals", [])
                ],
                day=day,
            )
            self.whatsapp.send_message(
                to=self.caregiver_phone,
                message=f"📋 WEEKLY HEALTH SUMMARY — Week {day // 7}\n\n{summary}",
                sender=self.name,
                message_type="weekly_summary",
            )
            return f"[Day {day}] Weekly summary sent to {self.caregiver_name}"

        return f"[Day {day}] Caregiver monitoring — no alerts today"

    def notify_family(
        self,
        message: str,
        urgency: str = "normal",
        day: Optional[int] = None,
    ) -> None:
        """
        Send a notification to the caregiver via WhatsApp (and SMS for critical).
        urgency: 'normal' | 'moderate' | 'critical'
        """
        day = day or self.care_plan.current_day
        urgency_emoji = {"normal": "ℹ️", "moderate": "⚠️", "critical": "🆘"}.get(urgency, "ℹ️")
        full_message = (
            f"{urgency_emoji} Health Update — {self.patient_name} (Day {day})\n\n"
            f"{message}\n\n"
            f"— {self.name} AI Care System"
        )

        self.whatsapp.send_message(
            to=self.caregiver_phone,
            message=full_message,
            sender=self.name,
            message_type=f"alert_{urgency}",
        )

        if urgency == "critical":
            self.sms.send_sms(
                to=self.caregiver_phone,
                message=f"URGENT: {self.patient_name} health alert. Check WhatsApp for details.",
                sender=self.name,
            )

        # Track in care plan
        self.care_plan.add_caregiver_alert(message=message, urgency=urgency)
        self.notifications_sent.append(
            {
                "day": day,
                "urgency": urgency,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )
        logger.info(f"[{self.name}] Notified caregiver (urgency={urgency}) on day {day}")

    def weekly_summary(
        self, vitals_list: List[Dict[str, Any]], day: int = 0
    ) -> str:
        """
        Generate a weekly summary message for the caregiver.
        Uses Gemini if available, otherwise uses a rich template.
        """
        if not vitals_list:
            return "No vitals data recorded this week."

        # Calculate averages
        bp_avg = sum(v.get("bp_systolic", 0) for v in vitals_list) / len(vitals_list)
        glucose_avg = sum(v.get("blood_glucose", 0) for v in vitals_list) / len(vitals_list)
        adherence = self.memory.get_medication_adherence(self.patient_id, days=7)
        social = self.memory.get_social_summary(self.patient_id, days=7)

        week_num = day // 7

        context = {
            "task": "Generate weekly family health summary",
            "week_number": week_num,
            "days_covered": f"Days {day - 6}–{day}",
            "average_bp_systolic": round(bp_avg, 1),
            "average_blood_glucose": round(glucose_avg, 1),
            "medication_adherence_pct": adherence["adherence_pct"],
            "social_interaction_days": social["interaction_days"],
            "isolation_days": social["isolation_days"],
            "escalation_level": self.care_plan.escalation_level,
            "recent_events": len(self.care_plan.get_critical_events()),
        }

        if self._llm_available:
            prompt = self._build_weekly_summary_prompt(context)
            return self._call_llm(prompt)
        else:
            return self._template_weekly_summary(context)

    def _build_weekly_summary_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
You are ConnectAgent, an AI that communicates health updates to family caregivers.
You need to write a clear, caring weekly health summary for the son (Suresh Kumar)
of an elderly patient (Ramesh Kumar, 78, Hypertension + Diabetes).

WEEK {context['week_number']} SUMMARY DATA:
- Period: {context['days_covered']}
- Average BP: {context['average_bp_systolic']} mmHg (target: 120-140)
- Average Blood Glucose: {context['average_blood_glucose']} mg/dL (target: 100-180)
- Medication Adherence: {context['medication_adherence_pct']}%
- Social Interaction: {context['social_interaction_days']} of 7 days
- Days of Isolation: {context['isolation_days']}
- Current Alert Level: {context['escalation_level']}/3
- Critical Events: {context['recent_events']}

Write a friendly, clear summary in English (mixed with a little Hindi if appropriate).
Include:
1. Overall week assessment (Good/Okay/Concerning)
2. Key health metrics in simple language
3. What needs attention
4. Specific action items for the family
Keep it under 200 words. Use bullet points. Be caring but clear.
""".strip()

    def _template_weekly_summary(self, context: Dict[str, Any]) -> str:
        """Template-based weekly summary."""
        escalation = context["escalation_level"]
        status = "✅ Stable" if escalation == 0 else ("⚠️ Needs Attention" if escalation <= 2 else "🆘 Critical")

        adherence = context["medication_adherence_pct"]
        social_days = context["social_interaction_days"]

        return (
            f"📅 Week {context['week_number']} Health Summary — {context['days_covered']}\n"
            f"Overall Status: {status}\n\n"
            f"🩺 Vitals:\n"
            f"  • Average BP: {context['average_bp_systolic']} mmHg\n"
            f"  • Average Blood Sugar: {context['average_blood_glucose']} mg/dL\n\n"
            f"💊 Medications:\n"
            f"  • Adherence: {adherence}% {'✅' if adherence >= 90 else '⚠️'}\n\n"
            f"👥 Social Wellbeing:\n"
            f"  • Had interaction {social_days}/7 days "
            f"{'✅' if social_days >= 5 else '⚠️ Please visit or call'}\n\n"
            f"{'⚠️ ACTION NEEDED: Please call Papa today — vitals are concerning.' if escalation >= 2 else '✅ Keep supporting his routine. Well done!'}\n"
        )
