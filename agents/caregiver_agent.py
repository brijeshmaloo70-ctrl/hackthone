"""
agents/caregiver_agent.py
Caregiver Agent (ConnectAgent) — keeps the patient's family informed and engaged.
Subscribes to isolation, escalation, and family notification events.
Provides role-based privacy scoping and supports alert acknowledgments and action logs.
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
    ConnectAgent notifies the family about patient status,
    sends weekly summaries, facilitates alert acknowledgments,
    and logs caregiver follow-up actions.
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
        """Register handlers for all relevant event types."""
        self.event_bus.subscribe(EventType.FAMILY_NOTIFICATION, self._on_family_notification)
        self.event_bus.subscribe(EventType.ESCALATION_NEEDED, self._on_escalation)
        self.event_bus.subscribe(EventType.SOCIAL_ISOLATION_DETECTED, self._on_isolation)
        self.event_bus.subscribe(EventType.MEDICATION_MISSED, self._on_medication_missed)
        self.event_bus.subscribe(EventType.RISK_ALERT_ISSUED, self._on_risk_alert)
        self.event_bus.subscribe(EventType.SOCIAL_INTERVENTION_TRIGGERED, self._on_social_intervention)

    def _on_social_intervention(self, event: Event) -> None:
        """SocialWellbeingAgent already WhatsApp'd the family — record it so Suresh can acknowledge it."""
        msg = event.data.get("caregiver_message")
        if msg:
            self.notify_family(msg, urgency="moderate", day=event.day, source="SocialWellbeingAgent", deliver=False)

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
        message = self.lang_handler.get_family_alert(lang, "isolation", self.patient_name, self.caregiver_name)
        message += (
            f"\n📊 Detail: {self.patient_name} has had no social contact "
            f"for {isolation_days} consecutive days. Please check in with him today."
        )
        self.notify_family(message, urgency="moderate", day=event.day)

    def _on_medication_missed(self, event: Event) -> None:
        day = event.data.get("day", self.care_plan.current_day)
        med_name = event.data.get("med_name", "prescribed medicine")
        message = (
            f"💊 Medication Alert: {self.patient_name} missed {med_name} on Day {day}. "
            f"Please ensure he takes it at the right time. Missing medication can lead to vital spikes."
        )
        self.notify_family(message, urgency="moderate", day=day)

    def _on_risk_alert(self, event: Event) -> None:
        data = event.data
        if "caregiver" in data.get("intended_recipient", ""):
            urgency = "critical" if data.get("risk_level") in ["High Concern", "Emergency"] else "moderate"
            reasons = "; ".join(data.get("reasons", []))
            rec = data.get("recommended_action", "")
            msg = (
                f"🚨 Health Alert [{data.get('risk_level')}]: {self.patient_name}\n"
                f"Findings: {reasons}\n"
                f"Action Recommended: {rec}"
            )
            self.notify_family(msg, urgency=urgency, day=event.day)

    # ─── Main Methods ──────────────────────────────────────────────────────

    def run_check_in(self, patient_data: Dict[str, Any]) -> str:
        """Called daily by DemoRunner to generate status for the caregiver."""
        day = patient_data.get("day", 0)

        # Weekly summary every 7 days
        if day > 0 and day % 7 == 0:
            history = self.memory.get_all_vitals(self.patient_id)
            week_vitals = history[-7:] if len(history) >= 7 else history
            summary_msg = self.weekly_summary(week_vitals, day=day)
            self.notify_family(summary_msg, urgency="normal", day=day)
            return f"[Day {day}] Weekly summary sent to {self.caregiver_name}"

        return f"[Day {day}] Caregiver monitoring active — no alerts required"

    def notify_family(
        self,
        message: str,
        urgency: str = "normal",
        day: int = 0,
        source: str = "ConnectAgent",
        deliver: bool = True,
    ) -> Dict[str, Any]:
        """Send notification via WhatsApp (and SMS if critical) and store it as an acknowledgeable alert."""
        # Persist first: alerts used to live only in this process's memory, so the
        # caregiver hub was empty after every server restart and after `python main.py`.
        alert = self.memory.add_caregiver_alert(
            patient_id=self.patient_id, day=day, urgency=urgency, message=message, source=source,
        )

        if not deliver:  # already delivered by another agent; just make it acknowledgeable
            self.notifications_sent.append(alert)
            return alert

        # 1. WhatsApp message
        self.whatsapp.send_message(
            recipient=self.caregiver_phone,
            message=message,
            sender_name=self.name,
            message_type="urgent_alert" if urgency == "critical" else "text",
        )

        # 2. SMS if critical
        if urgency == "critical":
            self.sms.send_sms(
                recipient=self.caregiver_phone,
                message=f"[URGENT CARESYNC ALERT] {message[:140]}",
                sender=self.name,
            )

        self.care_plan.add_caregiver_alert(message=message, urgency=urgency)
        self.notifications_sent.append(alert)
        logger.info(f"[{self.name}] Notified caregiver (urgency={urgency}) on day {day}")
        return alert

    def acknowledge_alert(self, alert_id: str, action_taken: str, notes: str = "") -> Optional[Dict[str, Any]]:
        """Record caregiver acknowledgment + follow-up action.
        Returns None if the alert does not exist (previously any id was 'acknowledged')."""
        alert = self.memory.get_caregiver_alert(alert_id)
        if alert is None:
            return None
        day = alert["day"]
        self.memory.acknowledge_caregiver_alert(alert_id, action_taken, notes)

        self.memory.log_caregiver_action(
            patient_id=self.patient_id,
            caregiver_name=self.caregiver_name,
            action_taken=action_taken,
            notes=notes,
            day=day,
            alert_id=alert_id,
        )

        action_data = {
            "alert_id": alert_id,
            "caregiver": self.caregiver_name,
            "action_taken": action_taken,
            "notes": notes,
            "day": day,
            "timestamp": datetime.now().isoformat(),
        }

        self.event_bus.publish(
            event_type=EventType.CAREGIVER_ACTION_RECORDED,
            data=action_data,
            source="CaregiverAgent",
            day=day,
        )

        return action_data

    def get_caregiver_dashboard_data(self) -> Dict[str, Any]:
        """
        Role-based scoped view of patient health for family.
        Excludes raw clinician private notes; highlights safety, adherence, and wellbeing.
        """
        adherence = self.memory.get_medication_adherence(self.patient_id, days=7)
        social = self.memory.get_social_summary(self.patient_id, days=7)
        actions = self.memory.get_caregiver_actions(self.patient_id, limit=10)
        alerts = self.memory.get_caregiver_alerts(self.patient_id, limit=100)
        vitals = self.memory.get_all_vitals(self.patient_id)
        latest = vitals[-1] if vitals else None

        return {
            "patient": {
                "name": PATIENT_PROFILE["name"],
                "age": PATIENT_PROFILE["age"],
                "conditions": PATIENT_PROFILE["conditions"],
                "doctor": PATIENT_PROFILE["doctor_name"],
                "hospital": PATIENT_PROFILE["hospital"],
                "next_appointment": PATIENT_PROFILE["next_appointment"],
            },
            "caregiver": {
                "name": self.caregiver_name,
                "phone": self.caregiver_phone,
            },
            "escalation_level": self.care_plan.escalation_level,
            "adherence_7d_pct": adherence["adherence_pct"],
            "social_interaction_days_7d": social["interaction_days"],
            "isolation_days_7d": social["isolation_days"],
            "notifications": alerts,
            "unacknowledged_count": sum(1 for a in alerts if not a["acknowledged"]),
            "latest_vitals": {
                "day": latest["day"],
                "bp_systolic": latest["bp_systolic"],
                "bp_diastolic": latest["bp_diastolic"],
                "blood_glucose": latest["blood_glucose"],
                "heart_rate": latest["heart_rate"],
            } if latest else None,
            "recent_actions": actions,
        }

    def weekly_summary(self, vitals_list: List[Dict[str, Any]], day: int = 0) -> str:
        """Generate weekly summary message for the caregiver."""
        if not vitals_list:
            return "No vitals data recorded this week."

        bp_avg = sum(v.get("bp_systolic", 0) for v in vitals_list) / len(vitals_list)
        glucose_avg = sum(v.get("blood_glucose", 0) for v in vitals_list) / len(vitals_list)
        adherence = self.memory.get_medication_adherence(self.patient_id, days=7)
        social = self.memory.get_social_summary(self.patient_id, days=7)

        week_num = max(1, day // 7)
        escalation = self.care_plan.escalation_level
        status = "✅ Stable" if escalation == 0 else ("⚠️ Needs Attention" if escalation <= 2 else "🆘 Critical")

        return (
            f"📅 Week {week_num} Health Summary (Days {max(1, day - 6)}–{day})\n"
            f"Overall Status: {status}\n\n"
            f"🩺 Vitals:\n"
            f"  • Avg BP: {round(bp_avg, 1)} mmHg\n"
            f"  • Avg Blood Sugar: {round(glucose_avg, 1)} mg/dL\n\n"
            f"💊 Medications:\n"
            f"  • Adherence: {adherence['adherence_pct']}% {'✅' if adherence['adherence_pct'] >= 90 else '⚠️'}\n\n"
            f"👥 Social Wellbeing:\n"
            f"  • Interacted on {social['interaction_days']}/7 days "
            f"{'✅' if social['interaction_days'] >= 5 else '⚠️ Please plan a phone call or visit'}\n\n"
            f"{'⚠️ ACTION NEEDED: Please check in with Papa today — vitals have deviated from target.' if escalation >= 2 else '✅ Routines are stable. Thank you for your continued support!'}"
        )
