"""
agents/clinician_agent.py
Clinician Agent (MedInsightAgent) — prepares doctors before consultations,
monitors vital trends, manages clinical escalation, and reviews care plan proposals.
Designed to augment clinicians, not replace clinical judgment.
"""

from __future__ import annotations
import logging
from datetime import datetime
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
    MedInsightAgent synthesizes longitudinal trends, generates structured
    pre-consultation briefings, handles clinical escalations, and approves care plan updates.
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
        self._escalation_alerts_sent: List[Dict[str, Any]] = []

        # Subscribe to events
        self.event_bus.subscribe(EventType.VITALS_ALERT, self._on_vitals_alert)
        self.event_bus.subscribe(EventType.ESCALATION_NEEDED, self._on_escalation_needed)
        self.event_bus.subscribe(EventType.RISK_ALERT_ISSUED, self._on_risk_alert)

    # ─── Event Handlers ────────────────────────────────────────────────────

    def _on_vitals_alert(self, event: Event) -> None:
        """Evaluate if vitals alert warrants clinical notification."""
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
        day = event.day
        vitals = event.data.get("vitals", {})
        message = event.data.get("message", "Escalation required for patient.")
        alert = (
            f"🆘 CLINICAL ESCALATION — Day {day}\n\n"
            f"{message}\n\n"
            f"Recorded Vitals: {vitals}\n"
            f"Please review immediately."
        )
        self._send_doctor_alert(alert, day=day)

    def _on_risk_alert(self, event: Event) -> None:
        data = event.data
        if data.get("risk_level") in ["High Concern", "Emergency"]:
            alert = (
                f"🚨 [{data.get('risk_level')}] Clinician Alert — Day {event.day}\n"
                f"Patient: {self.patient_name} (78M)\n"
                f"Reasons: {'; '.join(data.get('reasons', []))}\n"
                f"Action Recommended: {data.get('recommended_action')}"
            )
            self._send_doctor_alert(alert, day=event.day)

    # ─── Trend Analysis ────────────────────────────────────────────────────

    def analyze_trends(self, metric: str, values: List[float]) -> Dict[str, Any]:
        """Compute clinical trend indicators."""
        if not values or len(values) < 2:
            return {"metric": metric, "trend_direction": "stable", "pct_change": 0.0}

        first_half = values[:len(values) // 2]
        second_half = values[len(values) // 2:]
        avg1 = sum(first_half) / len(first_half) if first_half else 0
        avg2 = sum(second_half) / len(second_half) if second_half else 0

        pct_change = ((avg2 - avg1) / avg1) * 100 if avg1 > 0 else 0
        direction = "increasing" if pct_change > 3 else ("decreasing" if pct_change < -3 else "stable")

        return {
            "metric": metric,
            "trend_direction": direction,
            "pct_change": round(pct_change, 1),
            "values": values,
            "current": values[-1] if values else None,
            "baseline": values[0] if values else None,
        }

    def check_escalation(self, vitals: Dict[str, Any]) -> bool:
        """Check if single reading breaches warning/danger thresholds."""
        bp_sys = vitals.get("bp_systolic", 0)
        gluc = vitals.get("blood_glucose", 0)
        return bp_sys >= VITAL_THRESHOLDS["bp_systolic"]["warning_high"] or gluc >= VITAL_THRESHOLDS["blood_glucose"]["warning_high"]

    # ─── 10-Point Doctor-Facing Structured Dashboard ───────────────────────

    def get_structured_clinician_dashboard(self, days: int = 30) -> Dict[str, Any]:
        """
        Synthesizes the comprehensive 10-point clinician dashboard view (HEALTH-01 requirement):
        1. Patient overview
        2. Current conditions
        3. Medication adherence
        4. Vital trends
        5. Symptom history
        6. Significant events
        7. Risk indicators
        8. AI-generated observations
        9. Suggested topics for clinical review
        10. Previous escalation history
        """
        history = self.memory.get_history(self.patient_id, days=days)
        adherence = self.memory.get_medication_adherence(self.patient_id, days=days)
        social = self.memory.get_social_summary(self.patient_id, days=days)
        vitals_rows = history.get("vitals", [])

        # Vitals aggregation
        bp_sys = [v["bp_systolic"] for v in vitals_rows if v.get("bp_systolic")]
        gluc = [v["blood_glucose"] for v in vitals_rows if v.get("blood_glucose")]
        hr = [v["heart_rate"] for v in vitals_rows if v.get("heart_rate")]

        # AI observations (evidence-based)
        observations = []
        if bp_sys and (sum(bp_sys) / len(bp_sys)) > 145:
            observations.append(f"Systolic BP averaged {round(sum(bp_sys)/len(bp_sys), 1)} mmHg, exceeding JNC-8 geriatric target (<140 mmHg).")
        if gluc and (sum(gluc) / len(gluc)) > 200:
            observations.append(f"Mean glucose ({round(sum(gluc)/len(gluc), 1)} mg/dL) suggests deteriorating glycaemic control; HbA1c testing recommended.")
        if adherence["adherence_pct"] < 80:
            observations.append(f"Medication adherence is {adherence['adherence_pct']}%, with {adherence['missed']} missed doses contributing directly to vital instability.")
        if social["isolation_days"] >= 3:
            observations.append(f"Patient experienced {social['isolation_days']} days of social isolation, correlating with mood reduction and decreased physical activity.")

        # Suggested clinical review topics
        suggested_topics = [
            "Consider intensifying antihypertensive therapy (e.g. increase Amlodipine or add thiazide-like diuretic)",
            "Review Metformin gastrointestinal tolerance vs adherence barriers; order HbA1c",
            "Discuss pill organizer or caregiver-assisted daily medication verification",
            "Assess social support network and screen for caregiver strain",
        ]

        # Symptoms collected
        symptom_history = []
        for c in history.get("checkins", []):
            import json
            try:
                s_list = json.loads(c.get("symptoms") or "[]")
                if s_list:
                    symptom_history.append({"day": c["day"], "symptoms": s_list, "mood": c.get("mood")})
            except Exception:
                pass

        # Pending care plan proposals
        pending_proposals = [p for p in self.care_plan.proposals if p.get("status") == "pending_review"]

        return {
            "1_patient_overview": {
                "name": PATIENT_PROFILE["name"],
                "age": PATIENT_PROFILE["age"],
                "gender": PATIENT_PROFILE["gender"],
                "doctor": CLINICIAN_PROFILE["name"],
                "hospital": PATIENT_PROFILE["hospital"],
                "monitoring_period": f"Days 1 to {self.care_plan.current_day or days}",
            },
            "2_current_conditions": {
                "diagnoses": PATIENT_PROFILE["conditions"],
                "allergies": PATIENT_PROFILE["allergies"],
                "current_medications": self.care_plan.medications,
            },
            "3_medication_adherence": {
                "rate_pct": adherence["adherence_pct"],
                "taken_doses": adherence["taken"],
                "missed_doses": adherence["missed"],
                "status": "Critical" if adherence["adherence_pct"] < 75 else ("Warning" if adherence["adherence_pct"] < 90 else "Good"),
            },
            "4_vital_trends": {
                "bp_systolic_avg": round(sum(bp_sys)/len(bp_sys), 1) if bp_sys else 0,
                "bp_systolic_peak": max(bp_sys) if bp_sys else 0,
                "blood_glucose_avg": round(sum(gluc)/len(gluc), 1) if gluc else 0,
                "blood_glucose_peak": max(gluc) if gluc else 0,
                "heart_rate_avg": round(sum(hr)/len(hr), 1) if hr else 0,
            },
            "5_symptom_history": symptom_history,
            "6_significant_events": self.care_plan.recent_events[-15:],
            "7_risk_indicators": {
                "current_escalation_level": self.care_plan.escalation_level,
                "current_escalation_reason": self.care_plan.escalation_reason,
                "caregiver_alerts_sent": len(self.care_plan.caregiver_alerts),
            },
            "8_ai_observations": observations or ["Patient health parameters remained within expected targets."],
            "9_suggested_clinical_topics": suggested_topics,
            "10_previous_escalation_history": [
                e for e in self.care_plan.recent_events if "ESCALATION" in e.get("event_type", "")
            ],
            "pending_care_plan_proposals": pending_proposals,
        }

    def review_care_plan_proposal(self, proposal_id: str, approve: bool = True, notes: str = "") -> bool:
        """Authorize or reject care plan proposal with clinical audit tracking."""
        if approve:
            success = self.care_plan.approve_proposal(proposal_id=proposal_id, reviewer_role="clinician")
            if notes and success:
                self.care_plan.add_doctor_note(f"Approved proposal '{proposal_id}': {notes}", author=self.doctor_name)
            return success
        else:
            return self.care_plan.reject_proposal(proposal_id=proposal_id, reviewer_role="clinician", reason=notes)

    def run_check_in(self, patient_data: Dict[str, Any]) -> str:
        """Called daily by DemoRunner."""
        day = patient_data.get("day", 0)
        return f"[Day {day}] Clinician surveillance active (Escalation Level {self.care_plan.escalation_level})"

    def _send_doctor_alert(self, alert: str, day: int = 0) -> None:
        """Send clinical escalation alert to doctor via WhatsApp."""
        self.whatsapp.send_message(
            recipient=self.doctor_phone,
            message=alert,
            sender_name=self.name,
        )
        self._escalation_alerts_sent.append({
            "day": day,
            "alert": alert,
            "timestamp": datetime.now().isoformat(),
        })
        logger.warning(f"[{self.name}] Escalation alert sent to doctor on day {day}")
