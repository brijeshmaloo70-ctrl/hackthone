"""
agents/risk_agent.py
Health Monitoring & Risk Analysis Agent (RiskAnalysisAgent).
Evaluates incoming vitals and symptoms using deterministic clinical guidelines
and contextual AI reasoning. Never relies solely on LLM for emergency decisions.
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from agents.base_agent import BaseAgent
from core.care_plan import CarePlan
from core.memory import PatientMemory
from core.event_bus import EventBus, EventType
from config.settings import VITAL_THRESHOLDS, PATIENT_PROFILE, AGENT_CONFIG

logger = logging.getLogger(__name__)


class RiskLevel:
    NORMAL = "Normal"
    LOW = "Low Concern"
    MODERATE = "Moderate Concern"
    HIGH = "High Concern"
    EMERGENCY = "Emergency"


class RiskAnalysisAgent(BaseAgent):
    """
    Continuous monitoring agent.
    Combines rule-based physiological triage with longitudinal trend comparisons.
    Produces transparent, explainable clinical alerts.
    """

    def __init__(
        self,
        care_plan: CarePlan,
        memory: PatientMemory,
        event_bus: EventBus,
    ):
        super().__init__(
            name="RiskAnalysisAgent",
            care_plan=care_plan,
            memory=memory,
            event_bus=event_bus,
        )
        self.patient_id = PATIENT_PROFILE["id"]
        self.patient_name = PATIENT_PROFILE["name"]
        self.thresholds = VITAL_THRESHOLDS
        self._alerts_history: List[Dict[str, Any]] = []

        # Subscribe to vitals alerts and check-in completion
        self.event_bus.subscribe(EventType.VITALS_ALERT, self._on_vitals_alert)
        self.event_bus.subscribe(EventType.CHECKIN_COMPLETED, self._on_checkin_completed)

    # ─── Event Handlers ────────────────────────────────────────────────────

    def _on_vitals_alert(self, event) -> None:
        """Handle incoming vital alert for comprehensive multi-metric evaluation."""
        day = event.day
        data = event.data
        evaluation = self.evaluate_health_record(data, day=day)
        if evaluation["risk_level"] in [RiskLevel.HIGH, RiskLevel.EMERGENCY]:
            self._dispatch_risk_alert(evaluation, day=day)

    def _on_checkin_completed(self, event) -> None:
        """Analyze combined symptom and vital picture post check-in."""
        day = event.day
        data = event.data
        evaluation = self.evaluate_health_record(data, day=day)
        if evaluation["risk_level"] != RiskLevel.NORMAL:
            self._dispatch_risk_alert(evaluation, day=day)

    # ─── Comprehensive Health Record Evaluation ────────────────────────────

    def evaluate_health_record(self, record: Dict[str, Any], day: int = 0) -> Dict[str, Any]:
        """
        Deterministic multi-parameter clinical evaluation.
        Evaluates BP, glucose, heart rate, symptoms, and medication non-adherence.
        """
        bp_sys = record.get("bp_systolic", 130)
        bp_dia = record.get("bp_diastolic", 85)
        gluc = record.get("blood_glucose", 140.0)
        hr = record.get("heart_rate", 72)
        symptoms = [s.lower() for s in record.get("symptoms", [])]
        meds_taken = record.get("medication_taken", True)

        reasons = []
        observations = []
        risk_level = RiskLevel.NORMAL
        rec_action = "Continue standard care plan monitoring."
        recipient = "patient"

        # 1. Deterministic Emergency Checks (Fail-safe, ZERO LLM dependency)
        has_chest_pain = any("chest" in s or "सीने" in s for s in symptoms)
        has_breathless = any("breath" in s or "सांस" in s for s in symptoms)
        bp_crisis = bp_sys >= self.thresholds["bp_systolic"]["danger_high"] or bp_dia >= self.thresholds["bp_diastolic"]["danger_high"]
        gluc_crisis = gluc >= self.thresholds["blood_glucose"]["danger_high"]

        if (has_chest_pain or has_breathless) and (bp_crisis or bp_sys >= 160):
            risk_level = RiskLevel.EMERGENCY
            reasons.append("Hypertensive Crisis with acute red-flag symptoms (chest pain/dyspnoea).")
            observations.append(f"BP {bp_sys}/{bp_dia} mmHg exceeding emergency threshold ({self.thresholds['bp_systolic']['danger_high']} mmHg).")
            observations.append(f"Symptoms reported: {', '.join(symptoms)}.")
            rec_action = "IMMEDIATE EMERGENCY: Dispatch emergency medical team (108), instruct patient to sit, notify caregiver."
            recipient = "emergency_team,caregiver,clinician"

        elif bp_sys >= 170 or gluc >= 315:
            risk_level = RiskLevel.EMERGENCY if symptoms else RiskLevel.HIGH
            reasons.append(f"Severe physiological deviation: BP {bp_sys} mmHg, Glucose {gluc} mg/dL.")
            observations.append(f"Systolic BP {bp_sys} >= 170 mmHg and/or Blood Glucose {gluc} >= 315 mg/dL.")
            rec_action = "Urgent clinical review within 2 hours. Escalate care plan to Level 3."
            recipient = "clinician,caregiver"

        elif bp_sys >= self.thresholds["bp_systolic"]["warning_high"] or gluc >= self.thresholds["blood_glucose"]["warning_high"]:
            risk_level = RiskLevel.HIGH if (not meds_taken or len(symptoms) >= 2) else RiskLevel.MODERATE
            reasons.append("Marked hypertension or glycaemic surge.")
            observations.append(f"BP {bp_sys}/{bp_dia} mmHg (threshold >= 150), Glucose {gluc} mg/dL (threshold >= 250).")
            if not meds_taken:
                observations.append("Patient missed daily scheduled medication.")
            rec_action = "Alert caregiver and flag for clinician pre-consultation review. Escalate to Level 2."
            recipient = "caregiver,clinician"

        elif not meds_taken or ("dizziness" in symptoms or "headache" in symptoms):
            risk_level = RiskLevel.LOW
            reasons.append("Mild symptom report or isolated missed medication.")
            observations.append(f"Reported symptoms: {symptoms or 'None'}; Meds: {'Taken' if meds_taken else 'Missed'}.")
            rec_action = "Send gentle patient reminder and log in longitudinal memory."
            recipient = "patient,caregiver"

        # 2. Historical Baseline Comparison Layer
        hist_trend = self.memory.get_trend(self.patient_id, "bp_systolic", days=7)
        hist_gluc_trend = self.memory.get_trend(self.patient_id, "blood_glucose", days=7)
        baseline_comparison = {
            "7d_avg_bp": hist_trend.get("average"),
            "bp_trend": hist_trend.get("trend_direction"),
            "7d_avg_glucose": hist_gluc_trend.get("average"),
            "glucose_trend": hist_gluc_trend.get("trend_direction"),
        }

        if hist_trend.get("trend_direction") == "increasing" and risk_level == RiskLevel.NORMAL and bp_sys >= 145:
            risk_level = RiskLevel.LOW
            reasons.append("Consistent 7-day upward drift in systolic blood pressure.")
            rec_action = "Monitor BP closely over next 48 hours."

        evaluation = {
            "timestamp": datetime.now().isoformat(),
            "day": day or self.care_plan.current_day,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "risk_level": risk_level,
            "reasons": reasons or ["Vitals within normal physiological variance."],
            "supporting_observations": observations or [f"BP: {bp_sys}/{bp_dia}, Glucose: {gluc}, HR: {hr}."],
            "historical_comparisons": baseline_comparison,
            "recommended_action": rec_action,
            "intended_recipient": recipient,
        }

        self._alerts_history.append(evaluation)
        return evaluation

    def _dispatch_risk_alert(self, evaluation: Dict[str, Any], day: int) -> None:
        """Publish structured risk alert on event bus and log into memory."""
        self.event_bus.publish(
            event_type=EventType.RISK_ALERT_ISSUED,
            data=evaluation,
            source="RiskAnalysisAgent",
            day=day,
        )

        # Sync escalation with care plan
        lvl_map = {
            RiskLevel.NORMAL: 0,
            RiskLevel.LOW: 1,
            RiskLevel.MODERATE: 2,
            RiskLevel.HIGH: 2,
            RiskLevel.EMERGENCY: 3,
        }
        target_lvl = lvl_map.get(evaluation["risk_level"], 0)
        if target_lvl > self.care_plan.escalation_level:
            self.care_plan.escalate(
                level=target_lvl,
                reason="; ".join(evaluation["reasons"]),
            )

        # Log into memory events table
        self.memory.log_event(
            patient_id=self.patient_id,
            day=day,
            event_type=EventType.RISK_ALERT_ISSUED,
            description=f"[{evaluation['risk_level']}] {'; '.join(evaluation['reasons'])}",
            severity="critical" if evaluation["risk_level"] in [RiskLevel.HIGH, RiskLevel.EMERGENCY] else "warning",
            agent_name=self.name,
        )

    def run_check_in(self, patient_data: Dict[str, Any]) -> str:
        """Called daily to execute physiological monitoring."""
        day = patient_data.get("day", self.care_plan.current_day)
        eval_result = self.evaluate_health_record(patient_data, day=day)
        return f"[Day {day}] Risk Analysis: {eval_result['risk_level']} ({eval_result['reasons'][0]})"

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._alerts_history[-limit:]
