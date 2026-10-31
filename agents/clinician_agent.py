"""
agents/clinician_agent.py
Clinician Agent — prepares doctors before visits, monitors trends,
and escalates dangerous patterns to the clinical team.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional, Tuple

from agents.base_agent import BaseAgent
from core.care_plan import CarePlan
from core.event_bus import EventBus, EventType, Event
from core.memory import PatientMemory
from config.settings import (
    VITAL_THRESHOLDS,
    PATIENT_PROFILE,
    CLINICIAN_PROFILE,
    AGENT_CONFIG,
    ESCALATION_LEVELS,
    ALL_MEDICATIONS,
)
from api.mock_integrations import MockWhatsApp

logger = logging.getLogger(__name__)


class ClinicianAgent(BaseAgent):
    """
    The Clinician Agent analyses patient trends, prepares doctor visit
    summaries, and escalates dangerous situations to the clinical team.
    """

    def __init__(
        self,
        care_plan: CarePlan,
        memory: PatientMemory,
        event_bus: EventBus,
    ):
        super().__init__(
            name=AGENT_CONFIG["clinician_agent"]["name"],
            care_plan=care_plan,
            memory=memory,
            event_bus=event_bus,
        )
        self.patient_id = PATIENT_PROFILE["id"]
        self.patient_name = PATIENT_PROFILE["name"]
        self.doctor_name = CLINICIAN_PROFILE["name"]
        self.doctor_phone = CLINICIAN_PROFILE["phone"]
        self.whatsapp = MockWhatsApp()
        self.trend_window = AGENT_CONFIG["clinician_agent"]["trend_window_days"]
        self._escalation_alerts_sent: List[Dict] = []

        # Subscribe to events
        self.event_bus.subscribe(EventType.VITALS_ALERT, self._on_vitals_alert)
        self.event_bus.subscribe(EventType.ESCALATION_NEEDED, self._on_escalation_needed)

    # ─── Event Handlers ────────────────────────────────────────────────────

    def _on_vitals_alert(self, event: Event) -> None:
        """React to a vitals alert by checking whether escalation is warranted."""
        vitals_data = event.data
        day = event.day
        if self.check_escalation(vitals_data):
            trend = self.analyze_trends(
                vitals_data.get("metric", "bp_systolic"),
                self.memory.get_trend(
                    self.patient_id,
                    vitals_data.get("metric", "bp_systolic"),
                    days=self.trend_window,
                ).get("values", []),
            )
            alert = self.generate_escalation_alert(vitals_data, trend)
            self._send_doctor_alert(alert, day=day)

    def _on_escalation_needed(self, event: Event) -> None:
        """React to an explicit escalation request."""
        day = event.day
        vitals = event.data.get("vitals", {})
        message = event.data.get("message", "Escalation required for patient.")
        alert = (
            f"🆘 ESCALATION TRIGGERED — Day {day}\n\n"
            f"{message}\n\n"
            f"Current Vitals: {vitals}\n"
            f"Please review immediately."
        )
        self._send_doctor_alert(alert, day=day)

    # ─── Main Methods ──────────────────────────────────────────────────────

    def run_check_in(self, patient_data: Dict[str, Any]) -> str:
        """
        Called daily by DemoRunner.
        Analyses current vitals + trends; escalates if needed.
        """
        day = patient_data.get("day", 0)

        # Check if we're approaching a doctor visit
        visit_day = 30
        days_to_visit = visit_day - day
        if 0 < days_to_visit <= 3:
            self.event_bus.publish(
                event_type=EventType.DOCTOR_VISIT_APPROACHING,
                data={
                    "days_remaining": days_to_visit,
                    "patient_name": self.patient_name,
                    "message": f"Doctor visit in {days_to_visit} days. Preparing summary.",
                },
                source=self.name,
                day=day,
            )

        # Analyse trends every 3 days
        if day >= 7 and day % 3 == 0:
            trend_report = self._run_trend_analysis(day)
            return (
                f"[Day {day}] Trend analysis: "
                f"BP {trend_report['bp']['trend_direction']}, "
                f"Glucose {trend_report['glucose']['trend_direction']} | "
                f"Escalation: {self.care_plan.escalation_level}"
            )

        return f"[Day {day}] Clinician monitoring — vitals within watchlist"

    def _run_trend_analysis(self, day: int) -> Dict[str, Any]:
        """Analyse BP and glucose trends and update escalation if needed."""
        bp_trend = self.analyze_trends(
            "bp_systolic",
            self.memory.get_trend(self.patient_id, "bp_systolic", self.trend_window).get("values", []),
        )
        glucose_trend = self.analyze_trends(
            "blood_glucose",
            self.memory.get_trend(self.patient_id, "blood_glucose", self.trend_window).get("values", []),
        )

        # Determine escalation level from trends
        danger_count = 0
        if bp_trend.get("status") == "deteriorating":
            danger_count += 1
        if glucose_trend.get("status") == "deteriorating":
            danger_count += 1

        latest_bp = self.care_plan.last_vitals.get("bp_systolic", 130)
        latest_glucose = self.care_plan.last_vitals.get("blood_glucose", 150)

        if latest_bp >= VITAL_THRESHOLDS["bp_systolic"]["danger_high"] or \
           latest_glucose >= VITAL_THRESHOLDS["blood_glucose"]["danger_high"]:
            danger_count += 2

        # Update escalation level
        new_level = min(3, danger_count)
        if new_level > self.care_plan.escalation_level:
            reason = (
                f"BP trend {bp_trend.get('trend_direction','?')}, "
                f"Glucose trend {glucose_trend.get('trend_direction','?')}, "
                f"Latest BP={latest_bp}, Glucose={latest_glucose}"
            )
            self.care_plan.escalate(new_level, reason)
            if new_level >= 2:
                self.event_bus.publish(
                    event_type=EventType.ESCALATION_NEEDED,
                    data={
                        "level": new_level,
                        "reason": reason,
                        "vitals": self.care_plan.last_vitals,
                        "message": f"Clinical escalation level {new_level}: {reason}",
                    },
                    source=self.name,
                    day=day,
                )

        return {"bp": bp_trend, "glucose": glucose_trend}

    def analyze_trends(
        self, metric: str, data: List[float]
    ) -> Dict[str, Any]:
        """
        Analyse a list of metric values for trend direction.
        Returns: {metric, trend_direction, status, latest, average, pct_change}
        """
        if not data:
            return {
                "metric": metric,
                "trend_direction": "unknown",
                "status": "unknown",
                "latest": None,
                "average": None,
                "pct_change": 0,
            }

        latest = data[-1]
        avg = sum(data) / len(data)

        if len(data) >= 4:
            mid = len(data) // 2
            first_avg = sum(data[:mid]) / mid
            second_avg = sum(data[mid:]) / (len(data) - mid)
            pct = ((second_avg - first_avg) / first_avg) * 100 if first_avg else 0

            if pct > 5:
                direction = "increasing"
            elif pct < -5:
                direction = "decreasing"
            else:
                direction = "stable"
        else:
            direction = "stable"
            pct = 0.0

        # Interpret status based on metric
        high_is_bad = metric in ("bp_systolic", "bp_diastolic", "blood_glucose", "heart_rate")
        if high_is_bad:
            status = "deteriorating" if direction == "increasing" else (
                "improving" if direction == "decreasing" else "stable"
            )
        else:
            status = "improving" if direction == "increasing" else (
                "deteriorating" if direction == "decreasing" else "stable"
            )

        return {
            "metric": metric,
            "trend_direction": direction,
            "status": status,
            "latest": round(latest, 1),
            "average": round(avg, 1),
            "pct_change": round(pct, 1),
            "data_points": len(data),
        }

    def check_escalation(self, vitals: Dict[str, Any]) -> bool:
        """
        Returns True if any vital crosses the danger threshold.
        Vitals dict may use either camelCase from event or snake_case from memory.
        """
        bp_sys = vitals.get("bp_systolic") or vitals.get("value") or 0
        glucose = vitals.get("blood_glucose", 0)
        hr = vitals.get("heart_rate", 72)

        thresholds = VITAL_THRESHOLDS

        if (
            bp_sys >= thresholds["bp_systolic"]["danger_high"]
            or bp_sys <= thresholds["bp_systolic"]["danger_low"]
            or glucose >= thresholds["blood_glucose"]["danger_high"]
            or hr >= thresholds["heart_rate"]["danger_high"]
            or hr <= thresholds["heart_rate"]["danger_low"]
        ):
            return True
        return False

    def generate_escalation_alert(
        self, vitals: Dict[str, Any], trend: Dict[str, Any]
    ) -> str:
        """
        Generate an urgent doctor alert message.
        Uses Gemini if available, otherwise uses a detailed template.
        """
        day = self.care_plan.current_day
        adherence = self.care_plan.medication_adherence_pct
        social_score = self.care_plan.social_wellbeing_score

        context = {
            "task": "Generate urgent clinical escalation alert for doctor",
            "patient_name": self.patient_name,
            "patient_age": PATIENT_PROFILE["age"],
            "conditions": ", ".join(PATIENT_PROFILE["conditions"]),
            "day": day,
            "current_vitals": vitals,
            "trend": trend,
            "medication_adherence": f"{adherence}%",
            "social_score": f"{social_score}/5",
            "escalation_level": self.care_plan.escalation_level,
            "escalation_reason": self.care_plan.escalation_reason,
        }

        if self._llm_available:
            prompt = self._build_escalation_prompt(context)
            return self._call_llm(prompt)
        else:
            return self._template_escalation_alert(context)

    def _build_escalation_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
You are MedInsightAgent, an AI clinical decision support agent.
Generate an urgent clinical escalation alert for Dr. {self.doctor_name}.

PATIENT: {context['patient_name']}, {context['patient_age']}M
CONDITIONS: {context['conditions']}
SIMULATION DAY: {context['day']}
ESCALATION LEVEL: {context['escalation_level']}/3
REASON: {context['escalation_reason']}

CURRENT VITALS: {context['current_vitals']}
TREND ANALYSIS: {context['trend']}
MEDICATION ADHERENCE: {context['medication_adherence']}
SOCIAL WELLBEING: {context['social_score']}

Write a concise, structured clinical alert (under 200 words) that:
1. Opens with severity level and immediate action required
2. Lists the concerning vitals and trend
3. Notes medication non-adherence if relevant
4. Recommends specific clinical actions
5. Notes social isolation if relevant

Use clinical language appropriate for a doctor. Be precise and urgent.
""".strip()

    def _template_escalation_alert(self, context: Dict[str, Any]) -> str:
        """Template escalation alert for when LLM is unavailable."""
        level = context["escalation_level"]
        bp = context["current_vitals"].get("bp_systolic", "?")
        glucose = context["current_vitals"].get("blood_glucose", "?")
        adherence = context["medication_adherence"]

        return (
            f"🆘 CLINICAL ESCALATION — LEVEL {level}/3\n"
            f"{'=' * 50}\n"
            f"PATIENT: {context['patient_name']}, {context['patient_age']}M\n"
            f"CONDITIONS: {context['conditions']}\n"
            f"DATE: Monitoring Day {context['day']}\n\n"
            f"⚠️ CRITICAL FINDINGS:\n"
            f"  • BP Systolic: {bp} mmHg (Danger threshold: ≥160)\n"
            f"  • Blood Glucose: {glucose} mg/dL (Danger threshold: ≥300)\n"
            f"  • Trend: {context['trend'].get('trend_direction', 'increasing')} over 7 days\n"
            f"  • Medication Adherence: {adherence} ⚠️\n\n"
            f"📋 RECOMMENDED ACTIONS:\n"
            f"  1. Immediate telephonic consultation with patient\n"
            f"  2. Review and adjust antihypertensive dosage\n"
            f"  3. Consider same-day/next-day clinic visit\n"
            f"  4. Assess for secondary causes of hypertension\n"
            f"  5. Family member to accompany patient\n\n"
            f"— {self.name} AI Clinical Decision Support"
        )

    def prepare_visit_summary(self, days: int = 30) -> str:
        """
        Generate a comprehensive pre-visit doctor briefing.
        Uses Gemini if available.
        """
        history = self.memory.get_history(self.patient_id, days=days)
        adherence = self.memory.get_medication_adherence(self.patient_id, days=days)
        social = self.memory.get_social_summary(self.patient_id, days=days)

        vitals_rows = history.get("vitals", [])
        if vitals_rows:
            bp_values = [r["bp_systolic"] for r in vitals_rows if r.get("bp_systolic")]
            glucose_values = [r["blood_glucose"] for r in vitals_rows if r.get("blood_glucose")]
            bp_avg = sum(bp_values) / len(bp_values) if bp_values else 0
            bp_max = max(bp_values) if bp_values else 0
            bp_min = min(bp_values) if bp_values else 0
            glucose_avg = sum(glucose_values) / len(glucose_values) if glucose_values else 0
            glucose_max = max(glucose_values) if glucose_values else 0
        else:
            bp_avg = bp_max = bp_min = glucose_avg = glucose_max = 0

        critical_events = self.care_plan.get_critical_events()
        escalation_events = [
            e for e in history.get("events", []) if e.get("severity") in ("warning", "critical")
        ]

        context = {
            "task": "Generate comprehensive pre-visit doctor briefing",
            "patient_name": self.patient_name,
            "patient_age": PATIENT_PROFILE["age"],
            "conditions": PATIENT_PROFILE["conditions"],
            "period_days": days,
            "bp_avg": round(bp_avg, 1),
            "bp_max": bp_max,
            "bp_min": bp_min,
            "glucose_avg": round(glucose_avg, 1),
            "glucose_max": glucose_max,
            "medication_adherence_pct": adherence["adherence_pct"],
            "missed_doses": adherence["missed"],
            "social_interaction_days": social["interaction_days"],
            "isolation_days": social["isolation_days"],
            "escalation_alerts": len(escalation_events),
            "peak_escalation": self.care_plan.escalation_level,
            "caregiver_alerts": len(self.care_plan.caregiver_alerts),
            "current_medications": [m["name"] for m in ALL_MEDICATIONS],
            "allergies": PATIENT_PROFILE["allergies"],
        }

        if self._llm_available:
            prompt = self._build_visit_summary_prompt(context)
            return self._call_llm(prompt)
        else:
            return self._template_visit_summary(context, vitals_rows)

    def _build_visit_summary_prompt(self, context: Dict[str, Any]) -> str:
        return f"""
You are MedInsightAgent, an AI preparing a pre-visit clinical summary for Dr. {self.doctor_name}.

PATIENT: {context['patient_name']}, {context['patient_age']}M
CONDITIONS: {', '.join(context['conditions'])}
ALLERGIES: {', '.join(context['allergies'])}
MONITORING PERIOD: Last {context['period_days']} days

30-DAY VITALS SUMMARY:
- BP: Average {context['bp_avg']} | Max {context['bp_max']} | Min {context['bp_min']} mmHg
- Blood Glucose: Average {context['glucose_avg']} | Max {context['glucose_max']} mg/dL

MEDICATION ADHERENCE:
- Adherence Rate: {context['medication_adherence_pct']}%
- Missed Doses: {context['missed_doses']} times

SOCIAL WELLBEING:
- Social Interaction: {context['social_interaction_days']}/{context['period_days']} days
- Isolation Days: {context['isolation_days']}

CLINICAL EVENTS:
- Escalation Alerts: {context['escalation_alerts']}
- Peak Escalation Level: {context['peak_escalation']}/3
- Family Notifications Sent: {context['caregiver_alerts']}

CURRENT MEDICATIONS: {', '.join(context['current_medications'])}

Generate a structured, comprehensive clinical visit summary (under 300 words) for the doctor that includes:
1. Executive summary / chief concern
2. 30-day health trend narrative
3. Medication review
4. Social determinants of health
5. Recommended discussion points and actions for today's visit
Use professional clinical language. Format with clear sections.
""".strip()

    def _template_visit_summary(
        self, context: Dict[str, Any], vitals_rows: List[Dict]
    ) -> str:
        """Rich template-based visit summary."""
        adherence = context["medication_adherence_pct"]
        adherence_flag = "⚠️ Poor" if adherence < 80 else ("🟡 Fair" if adherence < 90 else "✅ Good")

        return (
            f"{'=' * 60}\n"
            f"PRE-VISIT CLINICAL SUMMARY\n"
            f"{'=' * 60}\n"
            f"Patient: {context['patient_name']} | Age: {context['patient_age']}M\n"
            f"Conditions: {', '.join(context['conditions'])}\n"
            f"Allergies: {', '.join(context['allergies'])}\n"
            f"Monitoring Period: Last {context['period_days']} days\n"
            f"{'─' * 60}\n\n"
            f"📊 VITALS SUMMARY (30-DAY)\n"
            f"  Blood Pressure:\n"
            f"    Average: {context['bp_avg']} mmHg\n"
            f"    Peak:    {context['bp_max']} mmHg {'🆘 DANGER' if context['bp_max'] >= 160 else ''}\n"
            f"    Min:     {context['bp_min']} mmHg\n"
            f"  Blood Glucose:\n"
            f"    Average: {context['glucose_avg']} mg/dL\n"
            f"    Peak:    {context['glucose_max']} mg/dL {'🆘 DANGER' if context['glucose_max'] >= 300 else ''}\n\n"
            f"💊 MEDICATION ADHERENCE\n"
            f"  Overall: {adherence}% — {adherence_flag}\n"
            f"  Missed Doses: {context['missed_doses']} times in {context['period_days']} days\n"
            f"  Current Medications: {', '.join(context['current_medications'])}\n\n"
            f"👥 SOCIAL WELLBEING\n"
            f"  Social Days: {context['social_interaction_days']}/{context['period_days']}\n"
            f"  Isolation Days: {context['isolation_days']}\n\n"
            f"🚨 CLINICAL EVENTS\n"
            f"  Escalation Alerts: {context['escalation_alerts']}\n"
            f"  Peak Escalation: Level {context['peak_escalation']}/3\n"
            f"  Family Alerts Sent: {context['caregiver_alerts']}\n\n"
            f"📋 RECOMMENDED ACTIONS\n"
            f"  1. {'Urgent medication review — adherence critically low' if adherence < 80 else 'Review medication effectiveness'}\n"
            f"  2. Adjust antihypertensive regimen if BP remains elevated\n"
            f"  3. Reassess glycaemic control — consider HbA1c\n"
            f"  4. Screen for depression / social isolation\n"
            f"  5. Refer to dietitian and physiotherapist\n"
            f"  6. Schedule next monitoring review in 2 weeks\n"
            f"{'=' * 60}\n"
            f"Generated by {self.name} AI Clinical Support System\n"
        )

    def _send_doctor_alert(self, alert: str, day: int = 0) -> None:
        """Send escalation alert to the doctor via WhatsApp."""
        self.whatsapp.send_message(
            to=self.doctor_phone,
            message=alert,
            sender=self.name,
            message_type="clinical_escalation",
        )
        from datetime import datetime as _dt
        self._escalation_alerts_sent.append(
            {"day": day, "alert": alert, "timestamp": _dt.now().isoformat()}
        )
        logger.warning(f"[{self.name}] Escalation alert sent to doctor on day {day}")
